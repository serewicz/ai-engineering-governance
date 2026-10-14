"""Synthetic adversarial budget cases; never provider integration evidence."""
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from scripts.orchestration import budget as b

class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.now = int(datetime(2026, 10, 13, tzinfo=timezone.utc).timestamp())
        self.task = b.identity('fixture-owner/fixture-project', '123', 'standard')
        self.state = b.ledger(self.task, 'standard', '2026-10')
        self.meter = {'task_id':self.task,'period':'2026-10','as_of':self.now,
            'complete':True,'pending':False,'hard_limits_verified':True,
            'monthly_cents':{'anthropic':0,'openai':0,'actions_other':0}}
    def admit(self, state=None, **kwargs):
        args = dict(role='claude',cycle=0,invocation_id='run1',reserve_cents=1000,
                    meter=self.meter,now=self.now,upper_bound_verified=True)
        args.update(kwargs)
        return b.admit(self.state if state is None else state, **args)
    def test_pending_failures_and_timeout_keep_reservation(self):
        state=self.admit()
        self.assertEqual(b.used(state),1000)
        with self.assertRaisesRegex(b.BudgetBlocked,'UNRECONCILED'): self.admit(state,invocation_id='retry')
        with self.assertRaisesRegex(b.BudgetBlocked,'USAGE_NOT_FINAL'): b.reconcile(state,'run1',0)
    def test_all_three_cycles_share_role_and_task_totals(self):
        state=self.state
        for i, amount in enumerate((1000,200,400,100,300,100,300,100)):
            role=('claude','codex')[i%2]
            state=self.admit(state,role=role,cycle=i//2,invocation_id=f'call{i}',reserve_cents=amount)
            state=b.reconcile(state,f'call{i}',amount,provider_final=True)
        self.assertEqual(b.used(state),2500)
        self.assertEqual(b.used(state,'claude'),2000)
        self.assertEqual(b.used(state,'codex'),500)
        with self.assertRaises(b.BudgetBlocked):self.admit(state,cycle=4,invocation_id='fifth')
    def test_stable_task_identity_across_runs(self):
        self.assertEqual(self.task,b.identity('fixture-owner/fixture-project','123','standard'))
        state=self.admit()
        with self.assertRaisesRegex(b.BudgetBlocked,'REPLAY'): self.admit(state)
        # Changing run attempt cannot erase persisted unresolved accounting.
        with self.assertRaisesRegex(b.BudgetBlocked,'UNRECONCILED'): self.admit(state,invocation_id='run2')
    def test_missing_stale_future_wrong_period_unknown_reports(self):
        for key,value in [('complete',False),('pending',True),('hard_limits_verified',False),('task_id','b'*64),('period','2026-09'),('as_of',self.now-301),('as_of',self.now+1)]:
            meter=dict(self.meter);meter[key]=value
            with self.subTest(key=key), self.assertRaises(b.BudgetBlocked):self.admit(meter=meter)
        meter=dict(self.meter);meter.pop('complete')
        with self.assertRaises(b.BudgetBlocked):self.admit(meter=meter)
        with self.assertRaises(b.BudgetBlocked):self.admit(meter=None)
    def test_unknown_invocation_bound_denied(self):
        with self.assertRaisesRegex(b.BudgetBlocked,'UNVERIFIED'):self.admit(upper_bound_verified=False)
    def test_monthly_exhaustion_and_other_charges(self):
        for provider,amount in [('anthropic',69500),('openai',20001),('actions_other',9901)]:
            meter=copy.deepcopy(self.meter);meter['monthly_cents'][provider]=amount
            with self.subTest(provider=provider),self.assertRaisesRegex(b.BudgetBlocked,'MONTHLY_EXHAUSTED'):self.admit(meter=meter)
    def test_money_types_negative_and_nonfinite_rejected(self):
        for amount in (True,-1,1.0,'10',float('nan'),float('inf'),100000001):
            with self.subTest(amount=str(amount)),self.assertRaises(b.BudgetBlocked):self.admit(reserve_cents=amount)
    def test_reconciliation_no_refund_or_overrun_or_replay(self):
        state=self.admit()
        for amount in (-1,1001,False):
            with self.assertRaises(b.BudgetBlocked):b.reconcile(state,'run1',amount,provider_final=True)
        final=b.reconcile(state,'run1',800,provider_final=True)
        self.assertEqual(b.used(final),800)
        with self.assertRaises(b.BudgetBlocked):b.reconcile(final,'run1',0,provider_final=True)
    def test_role_exhaustion_does_not_borrow_review_budget(self):
        with self.assertRaisesRegex(b.BudgetBlocked,'ROLE_EXHAUSTED'):self.admit(reserve_cents=2001)
    def test_smoke_budget_separate_and_bounded(self):
        smoke=b.ledger(b.identity('fixture-owner/fixture-project','124','smoke'),'smoke','2026-10')
        meter=dict(self.meter,task_id=smoke['task_id'])
        with self.assertRaisesRegex(b.BudgetBlocked,'TASK_EXHAUSTED'):self.admit(smoke,meter=meter,reserve_cents=501)
        self.assertNotEqual(smoke['task_id'],self.task)
    def test_cannot_skip_build_or_prior_review(self):
        with self.assertRaisesRegex(b.BudgetBlocked,'OUT_OF_ORDER'):self.admit(role='codex')
        with self.assertRaisesRegex(b.BudgetBlocked,'OUT_OF_ORDER'):self.admit(cycle=1)
    def test_month_rollover_denied(self):
        november=int(datetime(2026,11,1,tzinfo=timezone.utc).timestamp())
        with self.assertRaisesRegex(b.BudgetBlocked,'PERIOD_ROLLOVER'):self.admit(now=november,meter=dict(self.meter,as_of=november))
    def test_live_gate_cannot_be_enabled_by_environment_or_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            env=dict(os.environ,RUN_DATA=tmp,BUDGET_ROLE='authorize',CYCLE='0',ENGINEERING_BUDGET_ENABLED='true',ENGINEERING_ORCHESTRATION_ENABLED='true')
            result=subprocess.run([sys.executable,str(b.ROOT/'scripts/orchestration/budget.py'),'gate'],env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,1)
            report=json.loads((Path(tmp)/'budget-report.json').read_text())
            self.assertEqual(report['usage_status'],'UNKNOWN')
            self.assertFalse(report['provider_called'])
            self.assertFalse(report['publication_permitted'])
            self.assertIsNone(report['usage_cents'])
    def test_workflow_admission_precedes_authority_and_all_credentialed_calls(self):
        for file,job in [('agent-orchestrator.yml','authorize'),('agent-build.yml','build'),('agent-review.yml','review'),('agent-publish.yml','publish')]:
            steps=json.loads((b.ROOT/'.github/workflows'/file).read_text())['jobs'][job]['steps']
            gate=next(i for i,s in enumerate(steps) if 'budget.py gate' in s.get('run',''))
            authority=next(i for i,s in enumerate(steps) if s.get('run','').endswith('control.py gate'))
            self.assertLess(gate,authority)
            for i,step in enumerate(steps):
                if step.get('uses','').startswith(('anthropics/','openai/')) or 'ENGINEERING_AUTOMATION_TOKEN' in json.dumps(step):self.assertLess(gate,i)
    def test_dry_run_has_no_a1_or_credentials_or_publication(self):
        workflow=json.loads((b.ROOT/'.github/workflows/budget-dry-run.yml').read_text())
        self.assertEqual(workflow['permissions'],{'contents':'read'})
        self.assertEqual(workflow['on'],{'workflow_dispatch':{}})
        serialized=json.dumps(workflow)
        for forbidden in ('secrets.', 'id-token', 'agent-build', 'agent-publish', 'agent-review', 'control.py', 'issue_number', 'ENGINEERING_AUTOMATION_TOKEN', 'OPENAI_API_KEY'):
            self.assertNotIn(forbidden,serialized)
        with tempfile.TemporaryDirectory() as tmp:
            result=subprocess.run([sys.executable,str(b.ROOT/'scripts/orchestration/budget.py'),'dry-run'],env=dict(os.environ,RUN_DATA=tmp),capture_output=True,text=True)
            self.assertEqual(result.returncode,0)
            self.assertTrue(json.loads((Path(tmp)/'budget-report.json').read_text())['dry_run'])

if __name__=='__main__':unittest.main()
