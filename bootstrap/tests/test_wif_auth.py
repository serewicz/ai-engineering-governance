"""Offline authentication boundaries; synthetic signatures, never real identity tokens."""
import base64
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch
from scripts.orchestration import wif_auth_test as w

ROOT=Path(__file__).resolve().parents[1]
def enc(value):return base64.urlsafe_b64encode(value).decode().rstrip('=')

class SignedClaimsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup)
        cls.key=Path(cls.tmp.name)/'synthetic.pem'
        subprocess.run(['/usr/bin/openssl','genrsa','-out',str(cls.key),'2048'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        raw=subprocess.run(['/usr/bin/openssl','rsa','-in',str(cls.key),'-noout','-modulus'],check=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL).stdout.decode().strip().split('=',1)[1]
        n=bytes.fromhex(raw)
        cls.jwks={'keys':[{'kty':'RSA','use':'sig','kid':'synthetic','alg':'RS256','n':enc(n),'e':enc((65537).to_bytes(3,'big'))}]}
    def setUp(self):
        now=int(time.time())
        self.env=dict(w.CONFIG,GITHUB_SHA='a'*40,GITHUB_RUN_ID='123',GITHUB_RUN_ATTEMPT='1',GITHUB_REPOSITORY='fixture-owner/fixture-project',GITHUB_REF='refs/heads/main',GITHUB_EVENT_NAME='workflow_dispatch',GITHUB_WORKFLOW_REF=w.WORKFLOW)
        self.claims={'iss':w.ISSUER,'aud':w.AUDIENCE,'sub':w.SUBJECT,'repository':'fixture-owner/fixture-project','repository_id':'9001','repository_owner':'fixture-owner','repository_owner_id':'9000','ref':'refs/heads/main','event_name':'workflow_dispatch','workflow_ref':w.WORKFLOW,'sha':'a'*40,'workflow_sha':'a'*40,'run_id':'123','run_attempt':'1','exp':now+300,'iat':now-1,'nbf':now-1,'jti':'synthetic-only'}
    def jwt(self,claims=None,header=None):
        parts=[enc(json.dumps(header or {'alg':'RS256','kid':'synthetic'}).encode()),enc(json.dumps(self.claims if claims is None else claims).encode())]
        signed='.'.join(parts)
        signature=subprocess.run(['/usr/bin/openssl','dgst','-sha256','-sign',str(self.key)],input=signed.encode(),check=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL).stdout
        return signed+'.'+enc(signature)
    def test_correct_signature_exact_claims(self):
        checks,jti=w.validate_signed(self.jwt(),self.jwks,self.env)
        self.assertTrue(checks['signature']);self.assertEqual(checks['job_workflow_ref'],'ABSENT_TOP_LEVEL_WORKFLOW');self.assertEqual(len(jti[0]),32)
    def test_signed_wrong_claims_and_context_rejected(self):
        for key,value in [('iss','https://wrong.example'),('aud','https://wrong.example'),('sub','repo:fixture-owner/fixture-project:ref:refs/heads/main'),('repository','serewicz/HarvestGuard'),('repository_id','1306768141'),('repository_owner_id','123'),('ref','refs/heads/other'),('event_name','pull_request'),('workflow_ref','fixture-owner/fixture-project/.github/workflows/agent-build.yml@refs/heads/main'),('workflow_sha','b'*40),('run_attempt','2'),('job_workflow_ref','untrusted')]:
            c=dict(self.claims);c[key]=value
            with self.subTest(key=key),self.assertRaises(w.Stop):w.validate_signed(self.jwt(c),self.jwks,self.env)
    def test_expiry_future_missing_jti_or_algorithm_rejected(self):
        for key,value in [('exp',1),('iat',int(time.time())+60),('nbf',int(time.time())+60),('exp',True),('jti','')]:
            c=dict(self.claims);c[key]=value
            with self.subTest(key=key),self.assertRaises(w.Stop):w.validate_signed(self.jwt(c),self.jwks,self.env)
        with self.assertRaises(w.Stop):w.validate_signed(self.jwt(header={'alg':'none','kid':'synthetic'}),self.jwks,self.env)
    def test_tampering_or_unknown_public_key_rejected(self):
        token=self.jwt();parts=token.split('.');parts[1]=enc(json.dumps(dict(self.claims,ref='refs/heads/other')).encode())
        with self.assertRaises(w.Stop):w.validate_signed('.'.join(parts),self.jwks,self.env)
        with self.assertRaises(w.Stop):w.validate_signed(token,{'keys':[]},self.env)
    def test_valid_signed_wrong_audience_is_not_forged(self):
        audience='https://invalid.example/engineering-wif-auth-test';c=dict(self.claims,aud=audience)
        checks,_=w.validate_signed(self.jwt(c),self.jwks,self.env,audience)
        self.assertTrue(checks['aud']);self.assertTrue(checks['signature'])
    def test_full_auth_flow_accepts_shortened_ttl_and_runs_real_planned_negatives(self):
        report={}
        other=dict(self.claims,aud='https://invalid.example/engineering-wif-auth-test',jti='second-synthetic')
        responses=[(200,{'issuer':w.ISSUER,'jwks_uri':w.ISSUER+'/.well-known/jwks'}),(200,self.jwks)]
        exchanges=[(200,{'access_token':'sk-ant-oat01-synthetic','token_type':'Bearer','scope':'workspace:developer','expires_in':300}), (401,{'error':{'type':'authentication_error'}}), (401,{'error':{'type':'authentication_error'}})]
        with patch.object(w,'request_json',side_effect=responses),patch.object(w,'mint',side_effect=[self.jwt(),self.jwt(other)]),patch.object(w,'exchange',side_effect=exchanges) as exchange:
            w.run_auth(self.env,report)
            self.assertEqual(exchange.call_count,3)
        self.assertEqual(report['status'],'PASS_AUTH_TEST_ONLY');self.assertEqual(report['positive_granted_ttl_seconds'],300)
        self.assertEqual(report['negative_replay'],'PASS');self.assertEqual(report['negative_wrong_audience'],'PASS')
        self.assertNotIn('access_token',json.dumps(report))
    def test_overlong_grant_or_scope_mismatch_stops_before_negative_calls(self):
        for field,value in [('expires_in',3600),('expires_in',True),('expires_in',0),('scope','org:admin')]:
            grant={'access_token':'sk-ant-oat01-synthetic','token_type':'Bearer','scope':'workspace:developer','expires_in':300};grant[field]=value
            with self.subTest(field=field),patch.object(w,'request_json',side_effect=[(200,{'issuer':w.ISSUER,'jwks_uri':w.ISSUER+'/.well-known/jwks'}),(200,self.jwks)]),patch.object(w,'mint',return_value=self.jwt()),patch.object(w,'exchange',return_value=(200,grant)) as exchange:
                with self.assertRaises(w.Stop):w.run_auth(self.env,{})
                self.assertEqual(exchange.call_count,1)
    def test_unexpected_claims_stop_before_any_exchange(self):
        report={}
        with patch.object(w,'request_json',side_effect=[(200,{'issuer':w.ISSUER,'jwks_uri':w.ISSUER+'/.well-known/jwks'}),(200,self.jwks)]),patch.object(w,'mint',return_value=self.jwt(dict(self.claims,workflow_ref='wrong'))),patch.object(w,'exchange') as exchange:
            with self.assertRaises(w.Stop):w.run_auth(self.env,report)
            exchange.assert_not_called()

class WorkflowBoundaryTests(unittest.TestCase):
    def test_config_without_credential_access_or_network(self):
        with patch.object(w,'request_json') as network:
            self.assertTrue(all(w.config_check(dict(w.CONFIG)).values()));network.assert_not_called()
        for name in w.CONFIG:
            env=dict(w.CONFIG);env[name]='wrong'
            with self.assertRaises(w.Stop):w.config_check(env)
    def test_no_agent_or_repository_writes_and_oidc_only_auth_job(self):
        d=json.loads((ROOT/'.github/workflows/authentication-test.yml').read_text());self.assertEqual(d['on'],{'workflow_dispatch':{}});self.assertEqual(d['permissions'],{'contents':'read'})
        self.assertEqual(d['jobs']['configuration']['permissions'],{'contents':'read'})
        self.assertEqual(d['jobs']['authentication']['permissions'],{'contents':'read','id-token':'write'})
        self.assertIn("refs/heads/main",d['jobs']['authentication']['if']);self.assertIn("== 'false'",d['jobs']['authentication']['if'])
        for forbidden in ('secrets.','agent-orchestrator','agent-build','agent-review','agent-publish','control.py','budget.py','issue_number','ENGINEERING_AUTOMATION_TOKEN','OPENAI_API_KEY'):
            self.assertNotIn(forbidden,json.dumps(d))
    def test_auth_foreign_branch_stops_before_request(self):
        env=dict(w.CONFIG,GITHUB_REPOSITORY='fixture-owner/fixture-project',GITHUB_REF='refs/heads/other',GITHUB_EVENT_NAME='workflow_dispatch',GITHUB_WORKFLOW_REF=w.WORKFLOW)
        with patch.object(w,'request_json') as network,self.assertRaises(w.Stop):w.run_auth(env,{})
        network.assert_not_called()
    def test_request_url_cannot_send_runner_credential_to_other_host(self):
        env={'ACTIONS_ID_TOKEN_REQUEST_URL':'https://evil.example/token','ACTIONS_ID_TOKEN_REQUEST_TOKEN':'synthetic-marker'}
        with patch.object(w,'request_json') as network,self.assertRaises(w.Stop):w.mint(env,w.AUDIENCE)
        network.assert_not_called()
    def test_redirects_denied(self):
        with self.assertRaises(w.Stop):w.NoRedirect().redirect_request(None,None,302,'',{},'https://evil.example')
    def test_failure_report_never_contains_response_or_token(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,dict(w.CONFIG,RUN_DATA=tmp),clear=True),patch.object(w.sys,'argv',['check','auth']),patch.object(w,'run_auth',side_effect=ValueError('secret-JWT-sentinel')):
            self.assertEqual(w.main(),1);report=(Path(tmp)/'wif-auth-result.json').read_text();self.assertNotIn('secret-JWT-sentinel',report);self.assertNotIn('access_token',report);self.assertIn('STOP_CONFIGURATION_CLAIM_OR_PROVIDER_MISMATCH',report)

if __name__=='__main__':unittest.main()
