"""Offline/adversarial bootstrap tests. No provider or privileged GitHub operation."""
import copy,hashlib,json,os
from pathlib import Path
import subprocess,sys,tempfile,unittest
from unittest.mock import patch
B=Path(__file__).resolve().parents[1]/'bootstrap'
sys.path.insert(0,str(B/'scripts'));sys.path.insert(0,str(B/'tests'))
import bootstrap as b
from fixture import manifest
class BootstrapTests(unittest.TestCase):
 def test_schema_pins_and_disabled(self):
  m=manifest();self.assertIs(b.validate(m),m)
  for keys,value in [(('activation','state'),'enabled'),(('execution','correction_cycles'),4),(('execution','automatic_merge'),True),(('checkpoint','max_files'),101),(('budget','live_meter_adapter'),'trust-me'),(('bootstrap','bundle_sha256'),'f'*64),(('roles','principal'),'claude')]:
   bad=copy.deepcopy(m);bad[keys[0]][keys[1]]=value
   with self.subTest(keys=keys),self.assertRaises(b.Invalid):b.validate(bad)
 def test_duplicate_unknown_and_secret_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'input.json'
   for raw in ['{"x":1,"x":2}','{"key":"'+'github_pat_'+'x'*40+'"}','{"x":NaN}']:
    p.write_text(raw)
    with self.assertRaises((b.Invalid,ValueError)):b.load(p)
  m=manifest();m['extra']='unknown'
  with self.assertRaises(b.Invalid):b.validate(m)
 def test_cross_project_authority_and_smoke_protected_overlap(self):
  for group,key,value in [('identity','owner_id','123'),('anthropic','subject','repo:wrong:ref:refs/heads/main')]:
   m=manifest();m[group][key]=value
   with self.assertRaises(b.Invalid):b.validate(m)
  for mutation in [lambda m:m['authorization']['standard']['approval'].update(repository='other/project'),lambda m:m['authorization']['smoke'].update(issue_number=11),lambda m:m['authorization']['smoke'].update(allowed_roots=['src/']),lambda m:m['authorization']['standard'].update(allowed_roots=['scripts/']),lambda m:m['authorization']['standard'].update(allowed_roots=['src/../scripts/']),lambda m:m['scope']['protected_paths'].append('src/private/'),lambda m:m['budget']['standard'].update(claude_cents=True)]:
   m=manifest();mutation(m)
   with self.assertRaises(b.Invalid):b.validate(m)
 def test_deterministic_two_projects_no_inherited_values(self):
  outputs=[]
  for name,num in [('first-project','9001'),('second-project','9002')]:
   m=manifest(name,num);f=b.render(b.validate(m));self.assertEqual(f,b.render(m));outputs.append(f)
   for text in f.values():
    for old in ['serewicz/sar-tracker','HarvestGuard','A1-SPEC-5','6149289268','SAR_AUTOMATION_TOKEN','57ddc762','sar_tracker','tests/a1/']:
     self.assertNotIn(old,text)
   for path,text in f.items():
    if path.endswith('.py'):compile(text,path,'exec')
    if path.endswith('.yml'):json.loads(text)
  self.assertNotEqual(outputs[0]['.agent-policy.yml'],outputs[1]['.agent-policy.yml'])
 def test_dry_run_never_network_or_write(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'manifest.json';p.write_text(json.dumps(manifest()))
   with patch.object(b,'inspect',side_effect=AssertionError('network prohibited')),patch.object(b.subprocess,'run',side_effect=AssertionError('subprocess prohibited')),patch.object(sys,'argv',['bootstrap','render','--manifest',str(p),'--dry-run','--offline']),patch('builtins.print'):
    b.main()
   self.assertEqual(list(Path(t).iterdir()),[p])
 def test_staging_refuses_existing_and_upgrade_weakening(self):
  m=manifest();b.compare(m,copy.deepcopy(m));changed=copy.deepcopy(m);changed['scope']['protected_paths']=[]
  with self.assertRaises(b.Invalid):b.compare(m,changed)
  changed=copy.deepcopy(m);changed['authorization']['standard']['allowed_roots'].append('extra/')
  with self.assertRaises(b.Invalid):b.compare(m,changed)
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'manifest.json';p.write_text(json.dumps(m))
   r=subprocess.run([sys.executable,str(B/'scripts/bootstrap.py'),'render','--manifest',str(p),'--output',t],capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0);self.assertEqual(list(Path(t).iterdir()),[p])
 def test_report_complete_and_no_fake_integration_pass(self):
  r=b.report(manifest(),b.render(manifest()));self.assertEqual({x['id'] for x in r['checks']},set(b.STEPS));self.assertEqual(len(r['checks']),18);self.assertFalse(r['ready_to_execute'])
  for c in r['checks']:
   self.assertIn(c['status'],('PASS','FAIL','BLOCKED','NOT RUN'))
   if c['id'] in ('B15','B16','B18'):self.assertEqual(c['status'],'NOT RUN')
  self.assertEqual(next(x for x in r['checks'] if x['id']=='B14')['status'],'BLOCKED')
 def test_generated_workflow_scope_and_secret_separation(self):
  f=b.render(manifest());smoke=json.loads(f['.github/workflows/integration-smoke.yml']);self.assertEqual(smoke['on'],{'workflow_dispatch':{}});self.assertEqual(smoke['jobs']['authorize']['env']['ISSUE_NUMBER'],'12')
  for name in ('agent-build.yml','agent-review.yml','agent-publish.yml'):
   w=json.loads(f['.github/workflows/'+name]);txt=json.dumps(w)
   if name=='agent-build.yml':
    self.assertNotIn('secrets.',txt);self.assertEqual(w['jobs']['build']['permissions']['contents'],'read');self.assertEqual(w['jobs']['build']['permissions']['id-token'],'write')
   elif name=='agent-review.yml':self.assertNotIn('ENGINEERING_AUTOMATION_TOKEN',txt);self.assertNotIn('id-token',txt)
   else:self.assertNotIn('ENGINEERING_OPENAI_API_KEY',txt);self.assertNotIn('id-token',txt);self.assertNotIn('anthropics/',txt)
  auth=json.loads(f['.github/workflows/authentication-test.yml']);self.assertNotIn('secrets.',json.dumps(auth));self.assertNotIn('agent-build',json.dumps(auth));self.assertEqual(auth['jobs']['configuration']['permissions'],{'contents':'read'})
 def test_real_comment_ids_strong_upgrade_and_contract_discovery(self):
  m=manifest();m['governance']['adoption_approval']['comment_id']=6175413684;b.validate(m)
  for group,key,value in [('roles','principal','different-reviewer'),('execution','build_timeout_minutes',89)]:
   changed=copy.deepcopy(m);changed[group][key]=value
   with self.assertRaises(b.Invalid):b.compare(m,changed)
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   for name,text in b.render(m).items():p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
   (root/'src').mkdir()
   command=[sys.executable,'-c',"from scripts.orchestration.control import test_suite;print(test_suite('.').countTestCases())"]
   r=subprocess.run(command,cwd=root,capture_output=True,text=True);self.assertNotEqual(r.returncode,0);self.assertIn('contract package missing',r.stderr)
   package=root/'tests/contracts';package.mkdir();(package/'__init__.py').write_text('')
   r=subprocess.run(command,cwd=root,capture_output=True,text=True);self.assertNotEqual(r.returncode,0);self.assertIn('zero contract tests',r.stderr)
   (package/'test_contract.py').write_text('import unittest\nclass Contract(unittest.TestCase):\n def test_real(self):self.assertTrue(True)\n')
   r=subprocess.run(command,cwd=root,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);self.assertGreaterEqual(int(r.stdout.strip()),3)
 def test_every_render_input_is_inside_verified_bundle(self):
  m=manifest()
  inventory=b.load(B/'release-manifest.json')['files'];self.assertIn('templates/BOOTSTRAP_CHECKLIST.md',inventory)
  # Top-level checklist is not consumed; modifying it cannot influence pinned output.
  text=b.render(m)['docs/orchestration/BOOTSTRAP_CHECKLIST.md'];self.assertEqual(text,(B/'templates/BOOTSTRAP_CHECKLIST.md').read_text())
  source=(B/'scripts/renderer.py').read_text();self.assertNotIn("BUNDLE.parent",source)
 def test_generated_execution_recovery_budget_and_signed_claim_regressions(self):
  # Run original adversarial reference cases against newly rendered fixture identities,
  # not original hard-coded controllers. No model or real exchange is involved.
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);files=b.render(manifest())
   for path,text in files.items():p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
   for name in ('test_execution_parity.py','test_budget.py','test_wif_auth.py'):
    text=(B/'tests'/name).read_text();(root/'tests'/name).write_text(text)
   r=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=root,capture_output=True,text=True,env=dict(os.environ,PYTHONPYCACHEPREFIX=str(root/'bytecode')))
   self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   self.assertIn('Ran 43 tests',r.stderr)
   self.assertIn('OK',r.stderr)
   print('PASS: 43 generated-runtime recovery, continuation, budget and synthetic signed-claim regressions.')
