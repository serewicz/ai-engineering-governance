"""Bounded complete file-image recovery; no opaque patches or candidate code execution."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import zipfile
try:
    from .control import Blocked, require, policy, git, SHA, PATH
except ImportError:
    from control import Blocked, require, policy, git, SHA, PATH

MAX_FILES=100
MAX_DATA=25*1024*1024
MAX_METADATA=64*1024
SECRET=re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-(?:ant-|proj-)?[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----\s*(?:[A-Za-z0-9+/=]\s*){40,})')

def digest(data):return hashlib.sha256(data).hexdigest()
def safe(data):
    require(not SECRET.search(data),'credential-shaped checkpoint content')
    for key in ('GH_TOKEN','AUTOMATION_TOKEN','OPENAI_API_KEY','ACTIONS_ID_TOKEN_REQUEST_TOKEN'):
        value=os.environ.get(key,'');require(not value or value.encode() not in data,'credential in checkpoint')

def paths(candidate):
    names=set()
    for args in [('diff','--cached','--name-only','--no-renames','-z','HEAD'),('diff','--name-only','--no-renames','-z'),('ls-files','--others','--exclude-standard','-z')]:
        names.update(filter(None,git(candidate,*args).decode().split('\0')))
    return sorted(names)

def approved(name):
    require(type(name) is str and PATH.fullmatch(name) and '..' not in PurePosixPath(name).parts
        and not name.startswith('/') and '//' not in name and str(PurePosixPath(name))==name,'unsafe checkpoint path')
    require(not any(part.lower() in ('.git','.env','.ssh','.aws','.claude','.codex','credentials.json','auth.json','.git-credentials')
        or part.lower().startswith('.env.') for part in PurePosixPath(name).parts),'credential/cache path')
    p=policy();require(any(name.startswith(r) for r in p['allowed_roots'])
        and not any(name==r or name.startswith(r) for r in p['protected_paths']),'checkpoint scope')

def regular(candidate,name):
    path=candidate/name
    for part in [path,*path.parents]:
        if part==candidate:break
        require(not part.is_symlink(),'checkpoint symlink')
    if path.exists():require(stat.S_ISREG(path.stat().st_mode),'checkpoint nonregular file')
    return path

def blob(candidate,oid):
    require(SHA.fullmatch(oid),'blob identity')
    require(git(candidate,'cat-file','-t',oid).strip()==b'blob','checkpoint object type')
    size=int(git(candidate,'cat-file','-s',oid))
    require(0<=size<=MAX_DATA,'decoded blob overflow')
    value=git(candidate,'cat-file','blob',oid);require(len(value)==size,'blob size mismatch');safe(value)
    return value

def index(candidate,names):
    result={}
    if not names:return result
    for row in filter(None,git(candidate,'ls-files','--stage','-z','--',*names).decode().split('\0')):
        prefix,name=row.split('\t',1);mode,oid,stage=prefix.split()
        require(name in names and stage=='0' and mode in ('100644','100755'),'unsafe or unmerged index')
        result[name]=(int(mode,8),oid)
    return result

def collect(candidate,destination,base,label):
    candidate=Path(candidate);destination=Path(destination)
    require(SHA.fullmatch(base) and git(candidate,'rev-parse','HEAD').decode().strip()==base,'checkpoint HEAD moved')
    require(label in ('segment-1','segment-2','failure'),'checkpoint label')
    names=paths(candidate);require(len(names)<=MAX_FILES,'checkpoint file limit')
    for name in names:approved(name)
    idx=index(candidate,names)
    # No baseline or inverse-patch bytes are uploaded. Scan changed baseline blobs
    # conservatively as well; recovery remains bound to an independently fetched base.
    if names:
        for row in filter(None,git(candidate,'ls-tree','-z',base,'--',*names).decode().split('\0')):
            prefix,name=row.split('\t',1);mode,kind,oid=prefix.split()
            require(name in names and kind=='blob' and mode in ('100644','100755'),'unsafe base mode')
            blob(candidate,oid)
    images={};states={};total=0
    for i,name in enumerate(names):
        state={}
        for which in ('index','worktree'):
            value=None;mode=None
            if which=='index' and name in idx:
                mode,oid=idx[name];value=blob(candidate,oid)
            elif which=='worktree':
                path=regular(candidate,name)
                if path.exists():
                    require(path.stat().st_size<=MAX_DATA,'worktree image overflow')
                    mode=path.stat().st_mode;require(not (mode&0o7000),'privileged file mode')
                    mode=0o100755 if mode&0o111 else 0o100644
                    value=path.read_bytes();require(len(value)<=MAX_DATA,'worktree grew beyond limit');safe(value)
            if value is None:state[which]={'present':False}
            else:
                member=f'{which}/{i}'
                total+=len(value);require(total<=MAX_DATA,'decoded recovery data overflow')
                images[member]=value
                state[which]={'present':True,'member':member,'mode':mode,'size':len(value),'sha256':digest(value)}
                if which=='worktree':state[which]['permissions']=stat.S_IMODE(path.stat().st_mode)
        states[name]=state
    metadata={'version':2,'base_sha':base,'label':label,'states':states}
    raw=json.dumps(metadata,sort_keys=True).encode();require(len(raw)<=MAX_METADATA,'metadata overflow')
    require(not destination.exists() and not destination.is_symlink(),'preseeded checkpoint')
    destination.mkdir(parents=True)
    with zipfile.ZipFile(destination/'recovery.zip','w',compression=zipfile.ZIP_STORED) as bundle:
        for name,value in images.items():bundle.writestr(name,value)
    (destination/'manifest.json').write_bytes(raw)
    (destination/'RECOVERY.md').write_text('Use trusted checkpoint.py verify, then checkpoint.py restore into a NEW clean checkout at the exact manifest base SHA. Explicit index/worktree images preserve staged, unstaged, untracked, deleted and binary changes. Never restore over the dirty local checkout. Binary recovery never authorizes publication.\n')
    verify(destination)
    return metadata

def verify(destination):
    destination=Path(destination);require(not destination.is_symlink(),'checkpoint symlink')
    manifest=destination/'manifest.json';archive=destination/'recovery.zip'
    require(manifest.is_file() and not manifest.is_symlink() and manifest.stat().st_size<=MAX_METADATA,'manifest bounds')
    require(archive.is_file() and not archive.is_symlink() and archive.stat().st_size<=MAX_DATA+65536,'archive bounds')
    m=json.loads(manifest.read_text())
    require(type(m) is dict and set(m)=={'version','base_sha','label','states'} and type(m['version']) is int
        and m['version']==2 and type(m['base_sha']) is str and SHA.fullmatch(m['base_sha'])
        and m['label'] in ('segment-1','segment-2','failure'),'manifest schema')
    require(type(m['states']) is dict and len(m['states'])<=MAX_FILES,'state count')
    expected={};total=0
    for name,states in m['states'].items():
        approved(name);require(type(states) is dict and set(states)=={'index','worktree'},'state schema')
        for which,state in states.items():
            require(type(state) is dict and type(state.get('present')) is bool,'presence schema')
            if not state['present']:require(set(state)=={'present'},'absence schema');continue
            require(set(state)==({'present','member','mode','size','sha256','permissions'} if which=='worktree' else {'present','member','mode','size','sha256'}) and type(state['mode']) is int
                and state['mode'] in (0o100644,0o100755) and type(state['size']) is int
                and 0<=state['size']<=MAX_DATA and type(state['sha256']) is str
                and re.fullmatch(r'[0-9a-f]{64}',state['sha256']),'image schema/mode')
            if which=='worktree':require(type(state['permissions']) is int and 0<=state['permissions']<=0o777 and state['mode']==(0o100755 if state['permissions']&0o111 else 0o100644),'worktree permissions')
            member=state['member'];require(type(member) is str and re.fullmatch(which+r'/[0-9]{1,3}',member)
                and member not in expected,'image member identity')
            total+=state['size'];require(total<=MAX_DATA,'decoded data limit');expected[member]=state
    with zipfile.ZipFile(archive) as bundle:
        members=bundle.infolist();require(len(members)==len(expected) and {i.filename for i in members}==set(expected),'archive membership')
        for member in members:
            entry=expected[member.filename]
            require(not member.is_dir() and member.file_size==entry['size'] and member.compress_type==zipfile.ZIP_STORED and member.compress_size==member.file_size
                and (member.external_attr>>16)&0o170000 not in (0o120000,),'image storage mode')
            value=bundle.read(member);safe(value);require(len(value)==entry['size'] and digest(value)==entry['sha256'],'image integrity')
    return m

def restore(destination,candidate):
    m=verify(destination);candidate=Path(candidate)
    require(not candidate.is_symlink() and git(candidate,'rev-parse','HEAD').decode().strip()==m['base_sha']
        and not git(candidate,'status','--porcelain'),'restore requires clean exact base')
    # Preflight every path/mode/body before the first filesystem or index mutation.
    for name in m['states']:regular(candidate,name)
    with zipfile.ZipFile(Path(destination)/'recovery.zip') as bundle:
        for name,states in m['states'].items():
            entry=states['index']
            if entry['present']:
                value=bundle.read(entry['member'])
                oid=subprocess.check_output(['git','-C',str(candidate),'hash-object','-w','--stdin'],input=value).decode().strip()
                git(candidate,'update-index','--add','--cacheinfo',f"{entry['mode']:o},{oid},{name}")
            else:git(candidate,'update-index','--force-remove','--',name)
            path=regular(candidate,name);entry=states['worktree']
            if entry['present']:
                path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(bundle.read(entry['member']));path.chmod(entry['permissions'])
            elif path.exists():path.unlink()
    require(paths(candidate)==sorted(m['states']),'restore changed-path mismatch')
    restored=index(candidate,list(m['states']))
    for name,states in m['states'].items():
        entry=states['index']
        if entry['present']:
            require(name in restored and restored[name][0]==entry['mode'] and digest(blob(candidate,restored[name][1]))==entry['sha256'],'restored index mismatch')
        else:require(name not in restored,'restored index unexpected')
        path=regular(candidate,name);entry=states['worktree']
        require(path.exists()==entry['present'],'restored presence mismatch')
        if entry['present']:require(digest(path.read_bytes())==entry['sha256'] and stat.S_IMODE(path.stat().st_mode)==entry['permissions'],'restored worktree mismatch')
    return m

if __name__=='__main__':
    try:
        if len(sys.argv)==3 and sys.argv[1]=='verify':verify(sys.argv[2])
        elif len(sys.argv)==4 and sys.argv[1]=='restore':restore(sys.argv[2],sys.argv[3])
        elif len(sys.argv)==2 and sys.argv[1]=='collect':collect(os.environ['CANDIDATE'],os.environ['CHECKPOINT'],os.environ['BASE_SHA'],os.environ['CHECKPOINT_LABEL'])
        else:raise Blocked('invalid checkpoint command')
        print('PASS: bounded complete file-image checkpoint.')
    except (Blocked,OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError,zipfile.BadZipFile):
        print('BLOCKED: checkpoint unsafe, incomplete, oversized or verification failed; no publication authorized.');sys.exit(1)
