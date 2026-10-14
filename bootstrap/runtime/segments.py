"""Trusted segment classification and validated Claude session fallback; no transcripts uploaded."""
import json
import os
from pathlib import Path
import re
import sys
try:
    from .control import Blocked, require
except ImportError:
    from control import Blocked, require

SESSION = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,254}\Z')

def terminal(path):
    if not path:
        return None
    p = Path(path)
    require(p.is_file() and not p.is_symlink() and p.stat().st_size <= 25*1024*1024, 'execution evidence unavailable or oversized')
    text = p.read_text()
    try:
        documents = [json.loads(text)]
    except ValueError:
        documents = [json.loads(line) for line in text.splitlines() if line.strip()]
    events = []
    def walk(value):
        if isinstance(value, dict):
            if value.get('type') == 'result': events.append(value)
            for child in value.values(): walk(child)
        elif isinstance(value, list):
            for child in value: walk(child)
    for document in documents: walk(document)
    return events[-1] if events else None

def session(direct, event):
    for value in (direct, (event or {}).get('session_id')):
        if isinstance(value, str) and SESSION.fullmatch(value.strip()):
            return value.strip()
    return None

def continuation(outcome, result, event):
    if result is not None:
        require(isinstance(result, dict) and result.get('status') in ('COMPLETE','NEEDS_HUMAN','FAILED'), 'invalid builder result')
        return False
    return outcome == 'failure' and isinstance(event, dict) and event.get('subtype') == 'error_max_turns'

def main():
    event = terminal(os.environ.get('EXECUTION_FILE'))
    path = Path(os.environ['RUN_DATA'])/'result.json'
    result = None
    if path.exists():
        require(not path.is_symlink() and path.stat().st_size <= 65536, 'unsafe result')
        result = json.loads(path.read_text())
    sid = session(os.environ.get('SESSION_ID',''), event)
    resume = continuation(os.environ['SEGMENT_OUTCOME'], result, event)
    if resume: require(sid is not None, 'missing session ID; cannot resume')
    # Validated opaque session ID is output only to the runner control file, not log.
    with open(os.environ['GITHUB_OUTPUT'],'a') as stream:
        stream.write('continue='+str(resume).lower()+'\n')
        stream.write('session_id='+(sid or '')+'\n')
    require(os.environ['SEGMENT_OUTCOME'] == 'success' or resume, 'terminal Claude failure')

if __name__ == '__main__':
    try: main()
    except (Blocked, OSError, ValueError, KeyError, TypeError, RecursionError):
        print('BLOCKED: invalid segment evidence, missing session or terminal failure.');sys.exit(1)
