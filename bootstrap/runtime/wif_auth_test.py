"""Authentication-only diagnostic. No model, repository write or static credential.

All assertions/tokens remain in process memory; only fixed comparison results leave it.
Live execution requires this reviewed workflow merged on main and explicit dispatch.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

ISSUER = 'https://token.actions.githubusercontent.com'
AUDIENCE = 'https://api.anthropic.com'
EXCHANGE = AUDIENCE + '/v1/oauth/token'
WORKFLOW = 'serewicz/sar-tracker/.github/workflows/wif-auth-test.yml@refs/heads/main'
SUBJECT = 'repo:serewicz@7537557/sar-tracker@1411265082:ref:refs/heads/main'
CONFIG = {
    'TEMPLATE_CONFIGURATION': 'RENDER_FROM_NEW_MANIFEST'
}

class Stop(Exception):
    """Never attach a credential, provider response, URL or raw exception."""


def require(ok):
    if not ok:
        raise Stop()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise Stop()


def request_json(url, body=None, authorization=None):
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    if authorization:
        headers['Authorization'] = 'Bearer ' + authorization
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=20) as response:
            payload = response.read(65537)
            require(len(payload) <= 65536)
            return response.status, json.loads(payload)
    except urllib.error.HTTPError as error:
        # Negative tests inspect only status and a constant error type. Never retain
        # provider text, headers, request IDs, request objects or echoed assertions.
        payload = error.read(65537)
        require(len(payload) <= 65536)
        value = json.loads(payload)
        return error.code, {'error': {'type': value.get('error', {}).get('type')}}


def config_check(env):
    comparisons = {name: env.get(name) == value for name, value in CONFIG.items()}
    require(all(comparisons.values()))
    return comparisons


def decode64(text):
    require(type(text) is str and re.fullmatch(r'[A-Za-z0-9_-]+', text) is not None)
    return base64.b64decode(text + '=' * (-len(text) % 4), altchars=b'-_', validate=True)


def der(tag, value):
    size = len(value)
    length = bytes([size]) if size < 128 else (lambda n: bytes([128 + len(n)]) + n)(size.to_bytes((size.bit_length()+7)//8, 'big'))
    return bytes([tag]) + length + value


def rsa_public_pem(key):
    require(key.get('kty') == 'RSA' and key.get('use') == 'sig' and key.get('alg', 'RS256') == 'RS256')
    n, e = decode64(key['n']), decode64(key['e'])
    require(2048 <= int.from_bytes(n, 'big').bit_length() <= 8192 and int.from_bytes(e, 'big') == 65537)
    integers = [der(2, (b'\0' if value[0] & 128 else b'') + value) for value in (n, e)]
    rsa_key = der(48, b''.join(integers))
    # X.509 SubjectPublicKeyInfo, rsaEncryption OID and NULL parameters.
    encoded = base64.b64encode(der(48, bytes.fromhex('300d06092a864886f70d0101010500') + der(3, b'\0' + rsa_key)))
    lines = b'\n'.join(encoded[i:i+64] for i in range(0, len(encoded), 64))
    return b'-----BEGIN PUBLIC KEY-----\n' + lines + b'\n-----END PUBLIC KEY-----\n'


def validate_signed(jwt, jwks, env, audience=AUDIENCE):
    require(type(jwt) is str and len(jwt) <= 32768)
    parts = jwt.split('.')
    require(len(parts) == 3)
    header = json.loads(decode64(parts[0]))
    claims = json.loads(decode64(parts[1]))
    require(type(header) is dict and type(claims) is dict and header.get('alg') == 'RS256'
            and type(header.get('kid')) is str and header['kid'] and 'crit' not in header)
    keys = [key for key in jwks['keys'] if key.get('kid') == header['kid']]
    require(len(keys) == 1)
    # OpenSSL handles cryptographic verification; only public key and JWS signature
    # bytes use temporary files. The JWT/header/payload/access token is never written.
    with tempfile.TemporaryDirectory() as tmp:
        key = Path(tmp) / 'public.pem'
        signature = Path(tmp) / 'signature.bin'
        key.write_bytes(rsa_public_pem(keys[0]))
        signature.write_bytes(decode64(parts[2]))
        result = subprocess.run(['/usr/bin/openssl', 'dgst', '-sha256', '-verify', str(key), '-signature', str(signature)],
            input=(parts[0] + '.' + parts[1]).encode(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        require(result.returncode == 0)
    expected = {'iss': ISSUER, 'aud': audience, 'sub': SUBJECT, 'repository': CONFIG['SAR_WIF_REPOSITORY'],
        'repository_id': '1411265082', 'repository_owner': 'serewicz', 'repository_owner_id': '7537557',
        'ref': 'refs/heads/main', 'event_name': 'workflow_dispatch', 'workflow_ref': WORKFLOW,
        'sha': env['GITHUB_SHA'], 'workflow_sha': env['GITHUB_SHA'],
        'run_id': env['GITHUB_RUN_ID'], 'run_attempt': env['GITHUB_RUN_ATTEMPT']}
    comparisons = {name: claims.get(name) == value for name, value in expected.items()}
    require(all(comparisons.values()))
    if 'job_workflow_ref' in claims:
        require(claims['job_workflow_ref'] == WORKFLOW)
        comparisons['job_workflow_ref'] = 'PRESENT_MATCH'
    else:
        comparisons['job_workflow_ref'] = 'ABSENT_TOP_LEVEL_WORKFLOW'
    now = int(time.time())
    require(all(type(claims.get(key)) is int for key in ('exp', 'iat', 'nbf')))
    require(claims['nbf'] <= now < claims['exp'] and claims['iat'] <= now
        and 0 < claims['exp'] - claims['iat'] <= 600)
    require(type(claims.get('jti')) is str and 0 < len(claims['jti']) <= 256)
    comparisons['signature'] = True
    comparisons['time_validity'] = True
    return comparisons, (hashlib.sha256(claims['jti'].encode()).digest(), claims['exp'])


def mint(env, audience):
    url = urllib.parse.urlsplit(env['ACTIONS_ID_TOKEN_REQUEST_URL'])
    require(url.scheme == 'https' and url.hostname is not None and url.hostname.endswith('.actions.githubusercontent.com')
            and not url.username and not url.password and url.port in (None, 443))
    query = [(key, value) for key, value in urllib.parse.parse_qsl(url.query) if key != 'audience']
    query.append(('audience', audience))
    request_url = urllib.parse.urlunsplit(url._replace(query=urllib.parse.urlencode(query)))
    status, value = request_json(request_url, authorization=env['ACTIONS_ID_TOKEN_REQUEST_TOKEN'])
    require(status == 200 and type(value.get('value')) is str)
    return value['value']


def exchange(jwt):
    body = {'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer', 'assertion': jwt,
        'organization_id': CONFIG['SAR_ANTHROPIC_ORGANIZATION_ID'],
        'workspace_id': CONFIG['SAR_ANTHROPIC_WORKSPACE_ID'],
        'service_account_id': CONFIG['SAR_ANTHROPIC_SERVICE_ACCOUNT_ID'],
        'federation_rule_id': CONFIG['SAR_ANTHROPIC_FEDERATION_RULE_ID']}
    return request_json(EXCHANGE, body=body)


def run_auth(env, report):
    require(env.get('GITHUB_REPOSITORY') == CONFIG['SAR_WIF_REPOSITORY']
        and env.get('GITHUB_REF') == 'refs/heads/main' and env.get('GITHUB_EVENT_NAME') == 'workflow_dispatch'
        and env.get('GITHUB_WORKFLOW_REF') == WORKFLOW and env.get('SAR_ORCHESTRATION_ENABLED') == 'false')
    require(re.fullmatch(r'[0-9a-f]{40}', env.get('GITHUB_SHA', '')) is not None)
    status, discovery = request_json(ISSUER + '/.well-known/openid-configuration')
    require(status == 200 and discovery['issuer'] == ISSUER)
    uri = urllib.parse.urlsplit(discovery['jwks_uri'])
    require(uri.scheme == 'https' and uri.hostname == 'token.actions.githubusercontent.com' and not uri.username
        and not uri.password and uri.port in (None, 443))
    status, jwks = request_json(discovery['jwks_uri'])
    require(status == 200 and type(jwks.get('keys')) is list and 0 < len(jwks['keys']) <= 20)
    jwt = mint(env, AUDIENCE)
    comparisons, assertion = validate_signed(jwt, jwks, env)
    first_jti, assertion_exp = assertion
    report['signed_claim_comparisons'] = comparisons
    # Capture remaining assertion validity before exchange; provider processing can
    # shorten the grant further. Documented minimum is 60 seconds.
    remaining = assertion_exp - int(time.time())
    require(remaining > 0)
    ttl_ceiling = max(60, min(3600, 2 * remaining))
    status, value = exchange(jwt)
    require(status == 200 and type(value.get('access_token')) is str and value['access_token'].startswith('sk-ant-oat01-')
        and value.get('token_type') == 'Bearer' and value.get('scope') == 'workspace:developer'
        and type(value.get('expires_in')) is int and 60 <= value['expires_in'] <= ttl_ceiling)
    report['positive_granted_ttl_seconds'] = value['expires_in']
    # Drop the access token without using it. No Models/Messages/Files/API call.
    del value
    report['positive_exchange'] = 'PASS'
    # Replay tests issuer JTI protection, not a forged or altered JWT signature.
    status, denial = exchange(jwt)
    require(status == 401 and denial.get('error', {}).get('type') == 'authentication_error')
    report['negative_replay'] = 'PASS'
    del jwt
    # Real GitHub-signed wrong-audience assertion; not a tampered JWT.
    wrong_audience = 'https://invalid.example/sar-wif-auth-test'
    other = mint(env, wrong_audience)
    negative_comparisons, next_assertion = validate_signed(other, jwks, env, wrong_audience)
    require(next_assertion[0] != first_jti)
    status, denial = exchange(other)
    require(status == 401 and denial.get('error', {}).get('type') == 'authentication_error')
    report['negative_wrong_audience'] = 'PASS'
    report['negative_signed_claim_comparisons'] = negative_comparisons
    report['status'] = 'PASS_AUTH_TEST_ONLY'


def main():
    report = {'status': 'BLOCKED', 'configuration': 'NOT_RUN', 'signed_claim_comparisons': 'NOT_RUN',
        'positive_exchange': 'NOT_RUN', 'negative_replay': 'NOT_RUN', 'negative_wrong_audience': 'NOT_RUN',
        'negative_wrong_repository': 'NOT_RUN', 'negative_wrong_branch': 'NOT_RUN',
        'negative_wrong_workflow': 'NOT_RUN', 'inference_called': False, 'tokens_omitted': True}
    code = 1
    try:
        require(len(sys.argv) == 2 and sys.argv[1] in ('config', 'auth'))
        report['configuration_comparisons'] = config_check(os.environ)
        report['configuration'] = 'PASS'
        if sys.argv[1] == 'auth':
            run_auth(os.environ, report)
        else:
            report['status'] = 'PASS_CONFIGURATION_ONLY'
        code = 0
    except Exception:
        # Do not print exceptions: HTTP exceptions can contain credential-bearing URLs.
        report['reason'] = 'STOP_CONFIGURATION_CLAIM_OR_PROVIDER_MISMATCH'
    destination = Path(os.environ['RUN_DATA'])
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'wif-auth-result.json').write_text(json.dumps(report, indent=2) + '\n')
    print('WIF check: ' + report['status'] + '; tokens and provider response omitted.')
    return code

if __name__ == '__main__':
    sys.exit(main())
