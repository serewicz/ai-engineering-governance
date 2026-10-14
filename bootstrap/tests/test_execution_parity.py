"""Offline execution/recovery regressions. No models, credentials or live jobs."""
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from scripts.orchestration import control as c, checkpoint as cp, segments as seg, budget as b

ROOT=Path(__file__).resolve().parents[1]
class SegmentTests(unittest.TestCase):
    def test_fallback_and_terminal_classification(self):
        event={'type':'result','subtype':'error_max_turns','session_id':'fallback-123'}
        self.assertEqual(seg.session('direct-123',event),'direct-123')
        self.assertEqual(seg.session('',event),'fallback-123')
        self.assertIsNone(seg.session('bad\nvalue',{'session_id':''}))
        self.assertTrue(seg.continuation('failure',None,event))
        for status in ('COMPLETE','NEEDS_HUMAN','FAILED'):
            self.assertFalse(seg.continuation('failure',{'status':status},event))
        self.assertFalse(seg.continuation('failure',None,dict(event,subtype='error_authentication')))
        with self.assertRaises(c.Blocked):seg.continuation('failure',{'status':'garbage'},event)
    def test_missing_session_fails_before_resume_and_no_terminal_failure_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);e=p/'execution.json';e.write_text(json.dumps({'type':'result','subtype':'error_max_turns'}));out=p/'outputs'
            env={'RUN_DATA':tmp,'EXECUTION_FILE':str(e),'SESSION_ID':'','SEGMENT_OUTCOME':'failure','GITHUB_OUTPUT':str(out)}
            with patch.dict(os.environ,env,clear=True),self.assertRaises(c.Blocked):seg.main()
            self.assertFalse(out.exists())
            e.write_text(json.dumps({'type':'result','subtype':'error_network','session_id':'valid-123'}))
            with patch.dict(os.environ,env,clear=True),self.assertRaises(c.Blocked):seg.main()
    def test_direct_and_fallback_resume_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);e=p/'execution.json';e.write_text(json.dumps([{'type':'result','subtype':'error_max_turns','session_id':'fallback-123'}]));out=p/'outputs'
            with patch.dict(os.environ,{'RUN_DATA':tmp,'EXECUTION_FILE':str(e),'SEGMENT_OUTCOME':'failure','GITHUB_OUTPUT':str(out)},clear=True):seg.main()
            self.assertIn('continue=true',out.read_text());self.assertIn('session_id=fallback-123',out.read_text())

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.repo=self.root/'source';self.repo.mkdir()
        self.git('init');self.git('config','user.email','test@example.invalid');self.git('config','user.name','test')
        (self.repo/'src').mkdir();(self.repo/'src/text.py').write_text('base\n');(self.repo/'src/binary.dat').write_bytes(b'\x00base\xff');(self.repo/'src/deleted.py').write_text('delete me\n');self.git('add','--all');self.git('commit','-m','synthetic base');self.base=self.git('rev-parse','HEAD').decode().strip()
    def git(self,*args):return subprocess.check_output(['git','-C',str(self.repo),*args],stderr=subprocess.DEVNULL)
    def restore_repo(self):
        dest=self.root/'restore';subprocess.run(['git','clone','--no-hardlinks',str(self.repo),str(dest)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);return dest
    def test_full_index_worktree_untracked_binary_round_trip(self):
        (self.repo/'src/text.py').write_text('staged\n');self.git('add','src/text.py');(self.repo/'src/text.py').write_text('unstaged\n')
        (self.repo/'src/binary.dat').write_bytes(b'\x00staged\xff');self.git('add','src/binary.dat');(self.repo/'src/binary.dat').write_bytes(b'\x00unstaged\xff')
        (self.repo/'src/new.bin').write_bytes(b'\x00new\xff');(self.repo/'src/new.bin').chmod(0o755)
        (self.repo/'src/deleted.py').unlink();self.git('add','src/deleted.py')
        status=self.git('status','--porcelain','-z');staged=self.git('diff','--cached','--binary');unstaged=self.git('diff','--binary')
        directory=self.root/'checkpoint';cp.collect(self.repo,directory,self.base,'segment-1');dest=self.restore_repo();cp.restore(directory,dest)
        def read(*args):return subprocess.check_output(['git','-C',str(dest),*args])
        self.assertEqual(status,read('status','--porcelain','-z'));self.assertEqual(staged,read('diff','--cached','--binary'));self.assertEqual(unstaged,read('diff','--binary'));self.assertEqual((dest/'src/new.bin').read_bytes(),b'\x00new\xff');self.assertEqual((dest/'src/new.bin').stat().st_mode & 0o777,0o755);self.assertFalse((dest/'src/deleted.py').exists())
        with self.assertRaises(c.Blocked):c.patch_paths(staged)
    def test_overflow_secrets_symlink_protected_and_tamper_fail(self):
        (self.repo/'src/text.py').write_text('changed\n')
        with patch.object(cp,'MAX_DATA',4),self.assertRaises(c.Blocked):cp.collect(self.repo,self.root/'over',self.base,'failure')
        (self.repo/'src/text.py').write_text('github_pat_'+'x'*60)
        with self.assertRaises(c.Blocked):cp.collect(self.repo,self.root/'secret',self.base,'failure')
        (self.repo/'src/text.py').write_text('safe\n');(self.repo/'src/link').symlink_to('text.py')
        with self.assertRaises(c.Blocked):cp.collect(self.repo,self.root/'linkcp',self.base,'failure')
        (self.repo/'src/link').unlink();(self.repo/'outside.md').write_text('out')
        with self.assertRaises(c.Blocked):cp.collect(self.repo,self.root/'outside',self.base,'failure')
        (self.repo/'outside.md').unlink();directory=self.root/'cp';cp.collect(self.repo,directory,self.base,'failure');m=json.loads((directory/'manifest.json').read_text());m['states']['src/text.py']['worktree']['sha256']='0'*64;(directory/'manifest.json').write_text(json.dumps(m))
        with self.assertRaises(c.Blocked):cp.verify(directory)
    def test_staged_only_pack_and_binary_publication_still_denied(self):
        (self.repo/'src/text.py').write_text('staged only\n');self.git('add','src/text.py')
        data=self.root/'data';data.mkdir();(data/'result.json').write_text(json.dumps({'status':'COMPLETE','issue_number':11,'base_sha':self.base,'cycle':3,'scope_expansion_requested':False,'summary':'synthetic','validation':{'unittest':'pass'}}))
        artifact=self.root/'artifact'
        with patch.dict(os.environ,{'CANDIDATE':str(self.repo),'BASE_SHA':self.base,'CYCLE':'3','RUN_DATA':str(data),'ARTIFACT':str(artifact)},clear=True):c.pack()
        self.assertIn(b'staged only',(artifact/'implementation.patch').read_bytes())
        (self.repo/'src/binary.dat').write_bytes(b'\0new\xff');self.git('add','src/binary.dat')
        with self.assertRaises(c.Blocked):c.patch_paths(self.git('diff','--cached','--binary'))
    def test_raw_staged_secret_and_size_cannot_hide_behind_worktree(self):
        target=self.repo/'src/binary.dat'
        target.write_bytes(b'\0'+b'github_pat_'+b'x'*60);self.git('add','src/binary.dat');target.write_bytes(b'innocent')
        with self.assertRaises(c.Blocked):cp.collect(self.repo,self.root/'secretcp',self.base,'failure')
        target.write_bytes(b'\0'*1048576);self.git('add','src/binary.dat');target.write_bytes(b'innocent')
        with patch.object(cp,'MAX_DATA',8192),self.assertRaises(c.Blocked):cp.collect(self.repo,self.root/'sizecp',self.base,'failure')
        self.git('reset','--','src/binary.dat');target.unlink();target.symlink_to('../../outside');self.git('add','src/binary.dat');target.unlink();target.write_bytes(b'innocent')
        with self.assertRaises(c.Blocked):cp.collect(self.repo,self.root/'modecp',self.base,'failure')
    def test_hash_consistent_unsafe_modes_and_compression_rejected_before_mutation(self):
        (self.repo/'src/text.py').write_text('staged\n');self.git('add','src/text.py')
        directory=self.root/'cp';cp.collect(self.repo,directory,self.base,'failure');original=json.loads((directory/'manifest.json').read_text());dest=self.restore_repo()
        for mode in (0o120000,0o160000,0o104755):
            modified=copy.deepcopy(original);modified['states']['src/text.py']['index']['mode']=mode;(directory/'manifest.json').write_text(json.dumps(modified))
            with self.assertRaises(c.Blocked):cp.restore(directory,dest)
            self.assertEqual(subprocess.check_output(['git','-C',str(dest),'status','--porcelain']),b'')
        (directory/'manifest.json').write_text(json.dumps(original))
        import zipfile
        with zipfile.ZipFile(directory/'recovery.zip') as source:images={i.filename:source.read(i) for i in source.infolist()}
        with zipfile.ZipFile(directory/'recovery.zip','w',compression=zipfile.ZIP_DEFLATED) as archive:
            for name,value in images.items():archive.writestr(name,value)
        with self.assertRaises(c.Blocked):cp.verify(directory)
    def test_metadata_file_count_preseed_and_dirty_restore_guards(self):
        (self.repo/'src/text.py').write_text('change\n')
        with patch.object(cp,'MAX_FILES',0),self.assertRaises(c.Blocked):cp.collect(self.repo,self.root/'count',self.base,'failure')
        with patch.object(cp,'MAX_METADATA',1),self.assertRaises(c.Blocked):cp.collect(self.repo,self.root/'meta',self.base,'failure')
        destination=self.root/'cp';destination.mkdir()
        with self.assertRaises(c.Blocked):cp.collect(self.repo,destination,self.base,'failure')
        destination.rmdir();cp.collect(self.repo,destination,self.base,'failure')
        with self.assertRaises(c.Blocked):cp.restore(destination,self.repo)

class ParityGraphTests(unittest.TestCase):
    def test_three_chains_and_terminal_review(self):
        workflow=json.loads((ROOT/'.github/workflows/agent-orchestrator.yml').read_text())
        for n in (1,2,3):
            self.assertIn('build_'+str(n),workflow['jobs']);self.assertIn('publish_'+str(n),workflow['jobs']);self.assertIn('review_'+str(n),workflow['jobs'])
            self.assertIn('BLOCKERS',workflow['jobs']['build_'+str(n)]['if'])
            self.assertEqual(workflow['jobs']['build_'+str(n)]['with']['prior_cycle'],n-1)
        self.assertNotIn('build_4',workflow['jobs']);self.assertEqual(c.policy()['max_correction_cycles'],3)
        verdict={'status':'BLOCKERS','reviewed_sha':'a'*40,'blockers':['unresolved'],'important':[],'follow_up':[],'summary':'test'}
        with self.assertRaises(c.Blocked):c.review_ok(verdict,'a'*40,final=True)
        verdict.update(status='APPROVED',blockers=[]);self.assertEqual(c.review_ok(verdict,'a'*40,final=True),'APPROVED')
    def test_segments_checkpoints_and_admission_edges(self):
        steps=json.loads((ROOT/'.github/workflows/agent-build.yml').read_text())['jobs']['build']['steps'];indexed={s['id']:s for s in steps if 'id' in s}
        self.assertIn('40 || 80',indexed['claude_1']['with']['claude_args']);self.assertTrue(indexed['claude_2']['with']['claude_args'].startswith('--max-turns 40 --resume ${{ steps.segment.outputs.session_id }}'))
        self.assertIn('success()',indexed['claude_2']['if']);self.assertIn('checkpoint_1',indexed['segment']['if']);self.assertNotIn('claude_3',indexed)
        self.assertTrue(indexed['claude_1']['continue-on-error']);self.assertTrue(indexed['claude_2']['continue-on-error'])
        self.assertTrue(any('budget.py gate' in s.get('run','') for s in steps));self.assertTrue(any('Reject terminal' in s.get('name','') for s in steps))
    def test_two_initial_invocations_three_corrections_never_reset_budget(self):
        now=1791849600;period=__import__('datetime').datetime.fromtimestamp(now,__import__('datetime').timezone.utc).strftime('%Y-%m')
        task=b.identity('fixture-owner/fixture-project','777','standard');state=b.ledger(task,'standard',period);meter={'task_id':task,'period':period,'as_of':now,'complete':True,'pending':False,'hard_limits_verified':True,'monthly_cents':{'anthropic':0,'openai':0,'actions_other':0}}
        calls=[(0,'claude',1,500),(0,'claude',2,500),(0,'codex',1,200)]+[(n,r,1,amount) for n in (1,2,3) for r,amount in [('claude',300),('codex',100)]]
        for i,(cycle,role,segment,amount) in enumerate(calls):
            state=b.admit(state,role,cycle,str(i),amount,meter,now,upper_bound_verified=True,segment=segment);state=b.reconcile(state,str(i),amount,provider_final=True)
        self.assertEqual(b.used(state),2400)
        with self.assertRaises(b.BudgetBlocked):b.admit(state,'claude',4,'extra',1,meter,now,upper_bound_verified=True)
        self.assertEqual(b.TARGETS['standard'],{'combined_cents':2500,'claude_cents':2000,'codex_cents':500})

if __name__=='__main__':unittest.main()
