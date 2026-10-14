"""Stdlib budget controls. Live admission is deliberately unavailable without a trusted meter.

Pure functions operate on synthetic or future trusted-backend records. Never authorize
live spending from a workflow input, repository file, agent transcript or environment.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
TARGETS = {
    'schema_version': 1, 'currency': 'USD', 'project_revision': 'orchestration-budget-1-proposed',
    'standard': {'combined_cents': 2500, 'claude_cents': 2000, 'codex_cents': 500},
    'smoke': {'combined_cents': 500},
    'monthly': {'anthropic_cents': 70000, 'openai_cents': 20000, 'actions_other_cents': 9900},
    'existing_subscriptions_and_taxes': 'ACCOUNTED_SEPARATELY',
    'max_correction_cycles': 3, 'max_meter_age_seconds': 300,
    'live_meter_adapter': 'UNAVAILABLE', 'live_reservation_backend': 'UNAVAILABLE',
    'invocation_upper_bounds_verified': False,
}

class BudgetBlocked(Exception):
    pass


def need(ok, reason):
    if not ok:
        raise BudgetBlocked(reason)


def cents(value):
    need(type(value) is int and 0 <= value <= 100000000, 'INVALID_CENTS')
    return value


def config():
    path = ROOT / 'scripts/orchestration/budget-targets.json'
    need(path.is_file() and not path.is_symlink() and path.stat().st_size <= 10000, 'INVALID_CONFIG')
    value = json.loads(path.read_text())
    need(json.dumps(value, sort_keys=True) == json.dumps(TARGETS, sort_keys=True), 'CONFIG_MISMATCH')
    return value


def identity(repository, authorization_id, scope):
    """Stable across dispatches/run attempts; Owner approval identifies one task.

    A future backend must bind this to authenticated Owner approval and reject a new
    approval purporting to reset the same task. This hash alone authenticates nothing.
    """
    need(repository == 'serewicz/sar-tracker', 'WRONG_REPOSITORY')
    need(type(authorization_id) is str and re.fullmatch(r'[1-9][0-9]{0,19}', authorization_id), 'INVALID_AUTHORIZATION')
    need(scope in ('standard', 'smoke'), 'INVALID_SCOPE')
    return hashlib.sha256(f'{repository}:{authorization_id}:{scope}'.encode()).hexdigest()


def ledger(task_id, scope, period):
    need(type(task_id) is str and re.fullmatch(r'[0-9a-f]{64}', task_id), 'INVALID_TASK')
    need(scope in ('standard', 'smoke'), 'INVALID_SCOPE')
    need(type(period) is str and re.fullmatch(r'20[0-9]{2}-(0[1-9]|1[0-2])', period), 'INVALID_PERIOD')
    return {'task_id': task_id, 'scope': scope, 'period': period, 'entries': []}


def used(state, role=None):
    """Pending reservations remain fully charged, including failure/timeouts."""
    return sum(cents(e['actual_cents'] if e['state'] == 'FINAL' else e['reserved_cents'])
               for e in state['entries'] if role is None or e['role'] == role)


def admit(state, role, cycle, invocation_id, reserve_cents, meter, now, *, upper_bound_verified=False, segment=1):
    """Backend transaction must atomically load+admit+persist; pure function is not a lock.

    meter is accepted only from a future credential-isolated authenticated provider
    adapter. No live workflow accepts these records as input in this version.
    """
    need(type(cycle) is int and cycle in (0, 1, 2, 3), 'INVALID_CYCLE')
    need(role in ('claude', 'codex'), 'INVALID_ROLE')
    need(type(invocation_id) is str and re.fullmatch(r'[A-Za-z0-9_-]{1,80}', invocation_id), 'INVALID_INVOCATION')
    reserve_cents = cents(reserve_cents)
    need(reserve_cents > 0 and upper_bound_verified is True, 'UNVERIFIED_INVOCATION_BOUND')
    need(not any(e['invocation_id'] == invocation_id for e in state['entries']), 'REPLAY')
    need(not any(e['state'] != 'FINAL' for e in state['entries']), 'UNRECONCILED_USAGE')
    need(type(segment) is int and segment in (1, 2), 'INVALID_SEGMENT')
    need(segment == 1 or (cycle == 0 and role == 'claude'), 'INVALID_SEGMENT')
    sequence = [(e['cycle'], e['role'], e.get('segment', 1)) for e in state['entries']]
    initial = [(0, 'claude', 1)]
    if len(sequence) > 1 and sequence[1] == (0, 'claude', 2): initial.append((0, 'claude', 2))
    expected = initial + [(0, 'codex', 1)] + [(n, r, 1) for n in (1,2,3) for r in ('claude','codex')]
    need(sequence == expected[:len(sequence)], 'INVALID_SEQUENCE')
    next_item = (cycle, role, segment)
    need((sequence == [(0,'claude',1)] and next_item == (0,'claude',2))
        or (len(sequence) < len(expected) and next_item == expected[len(sequence)]), 'OUT_OF_ORDER')
    need(type(meter) is dict and set(meter) == {'task_id', 'period', 'as_of', 'complete', 'pending', 'monthly_cents', 'hard_limits_verified'}, 'INVALID_METER')
    need(meter['task_id'] == state['task_id'] and meter['period'] == state['period'], 'METER_BINDING')
    need(meter['complete'] is True and meter['pending'] is False and meter['hard_limits_verified'] is True, 'UNKNOWN_USAGE_OR_LIMITS')
    need(type(now) is int and type(meter['as_of']) is int and 0 <= now - meter['as_of'] <= TARGETS['max_meter_age_seconds'], 'STALE_METER')
    need(datetime.fromtimestamp(now, timezone.utc).strftime('%Y-%m') == state['period'], 'PERIOD_ROLLOVER')
    monthly = meter['monthly_cents']
    need(type(monthly) is dict and set(monthly) == {'anthropic', 'openai', 'actions_other'}, 'INVALID_MONTHLY_METER')
    for provider in monthly:
        amount = cents(monthly[provider])
        allowance = TARGETS['monthly'][provider + '_cents']
        extra = reserve_cents if provider == {'claude': 'anthropic', 'codex': 'openai'}[role] else 0
        need(amount + extra <= allowance, 'MONTHLY_EXHAUSTED')
    scope = state['scope']
    limit = TARGETS[scope]['combined_cents']
    need(used(state) + reserve_cents <= limit, 'TASK_EXHAUSTED')
    if scope == 'standard':
        need(used(state, role) + reserve_cents <= TARGETS['standard'][role + '_cents'], 'ROLE_EXHAUSTED')
    entry = {'invocation_id': invocation_id, 'role': role, 'cycle': cycle,
             'segment': segment, 'reserved_cents': reserve_cents, 'actual_cents': None, 'state': 'PENDING'}
    # Copy-on-write lets a future backend reject a conflicting compare-and-swap.
    return dict(state, entries=[*state['entries'], entry])


def reconcile(state, invocation_id, actual_cents, *, provider_final=False):
    actual_cents = cents(actual_cents)
    need(provider_final is True, 'USAGE_NOT_FINAL')
    matches = [e for e in state['entries'] if e['invocation_id'] == invocation_id]
    need(len(matches) == 1 and matches[0]['state'] == 'PENDING', 'RECONCILIATION_REPLAY')
    need(actual_cents <= matches[0]['reserved_cents'], 'RESERVATION_OVERRUN')
    return dict(state, entries=[dict(e, actual_cents=actual_cents, state='FINAL')
        if e['invocation_id'] == invocation_id else dict(e) for e in state['entries']])


def report(role, cycle, reason, dry_run=False):
    # Fixed allowlisted metadata only, no provider responses, account IDs, billing
    # data, token counts, raw exceptions, transcripts or environment dumps.
    return {'schema_version': 1, 'status': 'BLOCKED', 'reason': reason,
            'role': role, 'cycle': cycle, 'dry_run': dry_run,
            'targets': TARGETS['standard'], 'usage_cents': None,
            'usage_status': 'UNKNOWN', 'exact_monetary_cap_claimed': False,
            'provider_called': False, 'publication_permitted': False}


def live_gate():
    config()
    role = os.environ.get('BUDGET_ROLE')
    need(role in ('claude', 'codex', 'publish', 'authorize'), 'INVALID_ROLE')
    cycle = os.environ.get('CYCLE', '0')
    need(cycle in ('0', '1', '2', '3'), 'INVALID_CYCLE')
    path = Path(os.environ['RUN_DATA']) / 'budget-report.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report(role, int(cycle), 'TRUSTED_METER_AND_RESERVATION_BACKEND_UNAVAILABLE')) + '\n')
    # Deliberately no environment switch, local ledger, agent cost or workflow input
    # can make this pass. Add a real trusted adapter in a separately governed change.
    raise BudgetBlocked('TRUSTED_METER_AND_RESERVATION_BACKEND_UNAVAILABLE')


def dry_run():
    config()
    destination = Path(os.environ['RUN_DATA'])
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'budget-report.json').write_text(json.dumps(report('authorize', 0, 'OFFLINE_ONLY', True)) + '\n')
    # This dry run does not call control.gate, read issues, obtain OIDC or use secrets.
    print('PASS: offline budget report; live automation remains BLOCKED.')


if __name__ == '__main__':
    try:
        need(len(sys.argv) == 2 and sys.argv[1] in ('gate', 'dry-run'), 'INVALID_COMMAND')
        {'gate': live_gate, 'dry-run': dry_run}[sys.argv[1]]()
    except (BudgetBlocked, OSError, ValueError, KeyError, TypeError):
        print('BLOCKED: budget validation or trusted metering unavailable; no provider call authorized.')
        sys.exit(1)
