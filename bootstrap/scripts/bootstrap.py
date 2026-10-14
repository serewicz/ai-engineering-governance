"""Offline-first bootstrap CLI. No provider administration, model call, merge or activation."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

BUNDLE = Path(__file__).resolve().parents[1]
LIMIT = 1048576
STEPS = tuple(f'B{n:02}' for n in range(1,19))
SECRET = re.compile(r'(?:gh[pousr]_|github_pat_|sk-ant-|sk-proj-)[A-Za-z0-9_-]{16,}|eyJ[A-Za-z0-9_-]{20,}[.]|-----BEGIN [A-Z ]*PRIVATE KEY')
MIN_PROTECTED = ['.github/', '.agent-policy.yml', 'AGENTS.md', 'PROJECT_AGENT_CONFIG.md', 'CLAUDE.md', 'docs/governance/', 'docs/orchestration/', 'scripts/', 'bootstrap.project.json', 'bootstrap-runtime.json', 'tests/test_bootstrap_runtime.py']
class Invalid(ValueError): pass

def need(ok, code):
    if not ok: raise Invalid(code)

def pairs(items):
    result={}
    for key,value in items:
        need(key not in result, 'DUPLICATE_FIELD')
        result[key]=value
    return result

def load(path):
    p=Path(path)
    need(p.is_file() and not p.is_symlink() and p.stat().st_size<=LIMIT, 'INVALID_JSON_FILE')
    raw=p.read_text()
    need(not SECRET.search(raw), 'CREDENTIAL_CONTENT_PROHIBITED')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(Invalid('NONFINITE_NUMBER')))

def validate_shape(v,s):
    if 'anyOf' in s:
        for alternative in s['anyOf']:
            try: validate_shape(v,alternative); return
            except Invalid: pass
        raise Invalid('NO_SCHEMA_ALTERNATIVE')
    if 'const' in s:
        need(type(v) is type(s['const']) and json.dumps(v,sort_keys=True)==json.dumps(s['const'],sort_keys=True), 'CONSTANT_MISMATCH')
    if 'enum' in s: need(v in s['enum'] and any(type(v) is type(x) for x in s['enum']), 'ENUM_MISMATCH')
    t=s.get('type')
    if t=='object':
        need(type(v) is dict and set(v)==set(s['required']), 'OBJECT_FIELDS')
        for k,x in v.items(): validate_shape(x,s['properties'][k])
    elif t=='array':
        need(type(v) is list and s['minItems']<=len(v)<=s['maxItems'], 'ARRAY_SIZE')
        need(len({json.dumps(x,sort_keys=True) for x in v})==len(v), 'DUPLICATE_ARRAY_VALUE')
        for x in v: validate_shape(x,s['items'])
    elif t=='integer': need(type(v) is int and s['minimum']<=v<=s['maximum'], 'INTEGER_BOUNDS')
    elif t=='string':
        need(type(v) is str and s['minLength']<=len(v)<=s['maxLength'], 'STRING_BOUNDS')
        if 'pattern' in s: need(re.fullmatch(s['pattern'],v) is not None, 'STRING_PATTERN')
        need(not any(x in v.lower() for x in ('replace_with','<','>','placeholder')), 'PLACEHOLDER')

def canonical(p):
    need(type(p) is str and re.fullmatch(r'[A-Za-z0-9_./-]+',p) is not None, 'PATH_SYNTAX')
    need(not p.startswith('/') and '..' not in PurePosixPath(p).parts and '//' not in p and '.git' not in PurePosixPath(p).parts, 'PATH_BOUNDARY')
    need(str(PurePosixPath(p))==p.rstrip('/'), 'PATH_CANONICAL')

def validate(m):
    validate_shape(m,load(BUNDLE/'schemas/project.schema.json'))
    i=m['identity'];repo=i['repository'];owner,name=repo.split('/')
    need(owner==i['owner'] and m['roles']['owner_id']==i['owner_id'] and m['credentials']['owner_id']==i['owner_id'], 'OWNER_BINDING')
    need(m['anthropic']['subject']==f"repo:{owner}@{i['owner_id']}/{name}@{i['repository_id']}:ref:refs/heads/main", 'IMMUTABLE_SUBJECT')
    need(m['anthropic']['production_rule_id']!=m['anthropic']['auth_test_rule_id'], 'SEPARATE_TEST_RULE_REQUIRED')
    need(m['roles']['principal']!=m['roles']['builder'], 'SELF_REVIEW')
    for e in [m['governance']['adoption_approval'],m['governance']['three_cycle_deviation'],m['data']['retention_approval']]:
        need(e['repository']==repo and e['actor_id']==i['owner_id'], 'APPROVAL_REPOSITORY_OR_OWNER')
    tasks=m['authorization'];need(tasks['standard']['issue_number']!=tasks['smoke']['issue_number'], 'SMOKE_PRODUCT_SEPARATION')
    roots=[]
    for t in tasks.values():
        e=t['approval'];need(e['repository']==repo and e['actor_id']==i['owner_id'] and e['issue']==t['issue_number'], 'TASK_APPROVAL_BINDING')
        roots.append(t['allowed_roots'])
    for p in m['scope']['protected_paths']: canonical(p)
    protected=set(m['scope']['protected_paths'])|set(MIN_PROTECTED)
    for group in roots:
        for p in group:
            canonical(p)
            need(not any(p.startswith(q) or q.startswith(p) for q in protected), 'ALLOW_PROTECTED_OVERLAP')
    need(not any(a.startswith(b) or b.startswith(a) for a in roots[0] for b in roots[1]), 'SMOKE_ROOT_OVERLAP')
    b=m['budget'];need(b['standard']['claude_cents']+b['standard']['codex_cents']<=b['standard']['combined_cents'], 'BUDGET_PARTS')
    need(b['smoke']['combined_cents']<=b['standard']['combined_cents'], 'SMOKE_BUDGET')
    need(b['standard']['claude_cents']<=b['monthly']['anthropic_cents'] and b['standard']['codex_cents']<=b['monthly']['openai_cents'], 'MONTHLY_BUDGET')
    bundle_digest=verify_bundle()
    need(m['bootstrap']['bundle_sha256']==bundle_digest, 'MANIFEST_BUNDLE_PIN')
    need(m['bootstrap']['dependency_lock_sha256']==hashlib.sha256((BUNDLE/'dependency-lock.json').read_bytes()).hexdigest(), 'DEPENDENCY_PIN')
    return m

def verify_bundle():
    release=load(BUNDLE/'release-manifest.json')
    need(release['version']=='0.1.0' and release['status']=='unreleased-candidate', 'BUNDLE_VERSION')
    actual={}
    for p in sorted(BUNDLE.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and p.name!='release-manifest.json':
            need(not p.is_symlink(), 'BUNDLE_SYMLINK')
            actual[str(p.relative_to(BUNDLE))]=hashlib.sha256(p.read_bytes()).hexdigest()
    need(actual==release['files'], 'BUNDLE_INTEGRITY')
    # Digest manifest is integrity metadata only. Acquisition must verify reviewed commit independently.
    return hashlib.sha256(json.dumps(actual,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def compare(previous,current):
    validate(previous);validate(current)
    need(previous['identity']==current['identity'], 'UPGRADE_IDENTITY_CHANGE')
    need(previous['governance']==current['governance'], 'UPGRADE_GOVERNANCE_CHANGE_REQUIRES_OWNER_REVIEW')
    need(set(previous['scope']['protected_paths'])<=set(current['scope']['protected_paths']), 'UPGRADE_REMOVED_PROTECTION')
    need(current['scope']['max_patch_bytes']<=previous['scope']['max_patch_bytes'], 'UPGRADE_INCREASED_PATCH_LIMIT')
    need(previous['authorization']==current['authorization'], 'UPGRADE_SCOPE_OR_APPROVAL_CHANGE')
    need(previous['budget']==current['budget'], 'UPGRADE_BUDGET_CHANGE')
    need(previous['anthropic']==current['anthropic'] and previous['credentials']==current['credentials'], 'UPGRADE_TRUST_CHANGE')
    need(previous['data']==current['data'] and previous['protection']==current['protection'], 'UPGRADE_RETAINED_CONTROLS_CHANGE')

def source(name): return (BUNDLE/name).read_text()
def replace_function(s,name,new):
    start=s.index('def '+name+'(');end=s.find('\ndef ',start+1)
    if end==-1: end=s.find("\nif __name__",start+1)
    need(end!=-1,'TEMPLATE_FUNCTION')
    return s[:start]+new.rstrip()+'\n'+s[end:]

def render(m):
    from renderer import render_project
    return render_project(m)

def report(m,files=None):
    checks=[{'id':n,'responsibility':('Owner' if n in ('B02','B03','B07','B09','B10','B11','B12','B15','B16','B18') else 'Codex'), 'status':'NOT RUN','reason':'NO_AUTHENTICATED_EXECUTION_EVIDENCE','evidence':[]} for n in STEPS]
    for c in checks:
        if c['id']=='B04': c.update(status='PASS',reason='OFFLINE_SCHEMA_AND_CONTROL_VALIDATION',evidence=['bootstrap.project.json','bootstrap/schemas/project.schema.json'])
        if c['id']=='B05' and files is not None: c.update(status='PASS',reason='DETERMINISTIC_OFFLINE_RENDER',evidence=['render_sha256'])
        if c['id']=='B14': c.update(status='BLOCKED',reason='LIVE_METER_RESERVATIONS_INVOCATION_BOUNDS_AND_ISOLATION_UNAVAILABLE')
    return {'schema_version':'1.0.0','repository':m['identity']['repository'],'activation':'disabled','ready_to_execute':False,'exact_monetary_cap_claimed':False,'manifest_sha256':hashlib.sha256(json.dumps(m,sort_keys=True).encode()).hexdigest(),'governance_pin':m['governance']['commit'],'bootstrap_pin':m['bootstrap']['commit'],'checks':checks,'render_sha256':hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest() if files is not None else None}

def inspect(m):
    """Explicit read-only GitHub metadata queries; never prints arbitrary remote bodies."""
    def gh(path):
        r=subprocess.run(['gh','api',path],capture_output=True,text=True,timeout=30)
        if r.returncode: return None
        try: return json.loads(r.stdout)
        except ValueError: return None
    repo=m['identity']['repository'];metadata=gh('repos/'+repo)
    identity=type(metadata) is dict and str(metadata.get('id'))==m['identity']['repository_id'] and str(metadata.get('owner',{}).get('id'))==m['identity']['owner_id'] and metadata.get('full_name')==repo
    branch=gh('repos/'+repo+'/branches/main');rules=gh('repos/'+repo+'/rules/branches/main')
    variables=gh('repos/'+repo+'/actions/variables?per_page=100');secrets=gh('repos/'+repo+'/actions/secrets?per_page=100')
    # Name/presence only. No variables' arbitrary values or provider/billing data exported.
    main_sha=branch.get('commit',{}).get('sha') if type(branch) is dict else None
    if type(main_sha) is not str or re.fullmatch(r'[0-9a-f]{40}',main_sha) is None: main_sha=None
    names={'pull_request','required_status_checks','non_fast_forward','deletion'}
    observed=sorted({r.get('type') for r in rules if type(r) is dict and r.get('type') in names}) if type(rules) is list else []
    return {'identity':'PASS' if identity else 'BLOCKED','main_sha':main_sha,'baseline_matches':main_sha==m['identity']['baseline_sha'] if main_sha else None,
      'protection_inspection':'PASS' if type(rules) is list else 'BLOCKED','observed_rule_types':observed,'effective_protection_verified':False,
      'activation_false_observed':any(v.get('name')=='ENGINEERING_ORCHESTRATION_ENABLED' and v.get('value')=='false' for v in variables.get('variables',[])) if type(variables) is dict else None,
      'credential_presence':{n:('PRESENT' if any(v.get('name')==n for v in secrets.get('secrets',[])) else 'MISSING') if type(secrets) is dict and secrets.get('total_count',0)<=100 else 'BLOCKED' for n in ('ENGINEERING_AUTOMATION_TOKEN','ENGINEERING_OPENAI_API_KEY')},
      'provider_configuration':'NOT RUN','credential_scope':'NOT RUN','note':'Metadata inspection does not prove required checks, bypass identities or protection enforcement.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['validate','render','report','inspect','upgrade']);p.add_argument('--manifest',required=True);p.add_argument('--output');p.add_argument('--previous');p.add_argument('--dry-run',action='store_true');p.add_argument('--offline',action='store_true');p.add_argument('--read-only-remote',action='store_true');args=p.parse_args()
    try:
        m=validate(load(args.manifest));files=None
        if args.command=='inspect':
            need(args.read_only_remote and not args.offline,'REMOTE_INSPECTION_REQUIRES_EXPLICIT_MODE');print(json.dumps(inspect(m),indent=2));return
        need(not args.read_only_remote,'OFFLINE_COMMAND_NO_REMOTE')
        if args.command=='upgrade': need(args.previous is not None and args.dry_run,'UPGRADE_DRY_RUN_ONLY');compare(load(args.previous),m)
        if args.command in ('render','upgrade'):
            files=render(m)
            if not args.dry_run:
                need(args.command=='render' and args.output is not None,'NEW_STAGING_DIRECTORY_REQUIRED')
                target=Path(args.output);need(not target.exists() and not target.is_symlink(),'OUTPUT_ALREADY_EXISTS')
                target.mkdir()
                for name,text in files.items():
                    canonical(name);dest=target/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
            else: need(args.output is None,'DRY_RUN_WRITES_PROHIBITED')
        print(json.dumps(report(m,files),indent=2))
    except (Invalid,OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError):
        print(json.dumps({'status':'FAIL','reason':'VALIDATION_OR_SAFE_OPERATION_FAILED','activation':'disabled'}));sys.exit(1)
if __name__=='__main__': main()
