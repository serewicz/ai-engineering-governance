"""Trusted stdlib-only authority gates. Never executed from an agent checkout."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import time
import urllib.request
import unittest

ROOT = Path(__file__).resolve().parents[2]
REPO = "serewicz/sar-tracker"
PIN = "8c9c954f57ac119877396bba1f973a7dc2700a10"
A1_APPROVAL_ID = 6149289268
A1_APPROVAL_DIGEST = "ece94c312059cc204a0959b672528fb7131b94e3b906cc246413b011f1fbc33f"
DIGEST = "096f4d652a5c21becf4cdc4b20e13bbbf448ac17037441739b02efc0355b8bef"
SHA = re.compile(r"[0-9a-f]{40}\Z")
PATH = re.compile(r"[A-Za-z0-9_./-]+\Z")

class Blocked(Exception):
    pass

def require(condition, reason):
    if not condition:
        raise Blocked(reason)

def load(path):
    p = Path(path)
    require(p.is_file() and not p.is_symlink() and p.stat().st_size <= 2000000, "invalid JSON file")
    return json.loads(p.read_text())

def policy():
    p = load(ROOT / ".agent-policy.yml")  # JSON is a YAML 1.2 subset; no PyYAML dependency.
    expected = {
        "version": 1, "project_revision": "orchestration-execution-parity-1-proposed",
        "repository": REPO, "issue_number": 7, "spec_revision": "A1-SPEC-5",
        "spec_sha256": DIGEST, "governance_repository": "serewicz/ai-engineering-governance",
        "governance_pin": PIN, "owner": "serewicz", "max_correction_cycles": 3,
        "max_patch_bytes": 1000000, "max_changed_files": 100,
        "builder_repository_write": False, "reviewer_repository_write": False,
        "security_qa_required": True, "automatic_merge": False, "automatic_issue_closure": False,
        "required_ci": "Contracts and security (CPython 3.14 macOS)",
        "allowed_roots": ["sar_tracker/", "tests/a1/", "docs/a1/"],
        "protected_paths": [".github/", ".agent-policy.yml", "AGENTS.md", "PROJECT_AGENT_CONFIG.md",
                            "CLAUDE.md", "docs/governance/", "docs/orchestration/", "scripts/",
                            "tests/test_orchestration.py", "tests/test_budget.py", "tests/test_execution_parity.py"]}
    require(json.dumps(p, sort_keys=True) == json.dumps(expected, sort_keys=True), "policy mismatch")
    require(PIN in (ROOT / "PROJECT_AGENT_CONFIG.md").read_text(), "project governance pin mismatch")
    return p

def api(path, payload=None, token=None):
    require(path.startswith(f"repos/{REPO}/"), "API repository mismatch")
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request("https://api.github.com/" + path, data=data,
        headers={"Authorization": "Bearer " + (token or os.environ["GH_TOKEN"]),
                 "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)

def pages(path):
    result = []
    for page in range(1, 101):
        batch = api(path + ("&" if "?" in path else "?") + f"per_page=100&page={page}")
        if isinstance(batch, dict):
            batch = batch["check_runs"]
        require(isinstance(batch, list), "invalid API page")
        result.extend(batch)
        if len(batch) < 100:
            return result
    raise Blocked("pagination limit")

def approval(issue, comments, authorization_id, control_sha):
    require(type(issue.get("number")) is int and issue["number"] == 7 and issue.get("state") == "open", "issue invalid or closed")
    require(issue.get("html_url") == f"https://github.com/{REPO}/issues/7", "issue repository mismatch")
    require(hashlib.sha256(issue["body"].encode()).hexdigest() == DIGEST, "spec digest mismatch")
    require(PIN in issue["body"] and "A1-SPEC-5" in issue["body"], "issue governance mismatch")
    matches = [c for c in comments if str(c.get("id")) == authorization_id]
    require(len(matches) == 1 and matches[0].get("user", {}).get("login") == "serewicz", "missing Owner authorization")
    body = matches[0].get("body", "")
    require(body.startswith("SAR_ORCHESTRATION_AUTHORIZATION\n"), "missing orchestration authorization")
    record = json.loads(body.split("\n", 1)[1])
    expected = {"issue_number": 7, "spec_sha256": DIGEST, "governance_pin": PIN,
        "control_sha": control_sha, "policy_sha256": hashlib.sha256((ROOT / ".agent-policy.yml").read_bytes()).hexdigest(),
        "scope": "A1-only", "implementation_authorized": True, "bootstrap_merged_and_reviewed": True,
        "security_qa_required": True, "allowed_roots": policy()["allowed_roots"],
        "a1_approval_comment_id": A1_APPROVAL_ID, "a1_approval_comment_sha256": A1_APPROVAL_DIGEST}
    require(json.dumps(record, sort_keys=True) == json.dumps(expected, sort_keys=True), "authorization mismatch")
    # Any later explicit revocation stops dispatch/corrections/publication.
    require(not any(c.get("user", {}).get("login") == "serewicz" and c.get("id", 0) > matches[0]["id"]
        and c.get("body", "").startswith("SAR_ORCHESTRATION_REVOKED") for c in comments), "authorization revoked")
    return record

def git(cwd, *args):
    return subprocess.check_output(["git", "-C", str(cwd), *args], stderr=subprocess.DEVNULL)

def output(**values):
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        for key, value in values.items():
            require(re.fullmatch(r"[A-Za-z0-9_./:-]+", str(value)) is not None, "unsafe output")
            f.write(f"{key}={value}\n")

def gate():
    policy()
    require(os.environ.get("GITHUB_REPOSITORY") == REPO and os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
        and os.environ.get("GITHUB_REF") == "refs/heads/main", "dispatch must use target main")
    require(os.environ.get("ISSUE_NUMBER") == "7", "unsupported issue number")
    require(os.environ.get("ENABLED") == "true", "orchestration not activated")
    control_sha = git(ROOT, "rev-parse", "HEAD").decode().strip()
    require(SHA.fullmatch(control_sha) is not None and api(f"repos/{REPO}/git/ref/heads/main")["object"]["sha"] == control_sha,
            "control main moved")
    issue = api(f"repos/{REPO}/issues/7")
    comments = pages(f"repos/{REPO}/issues/7/comments")
    a1 = [c for c in comments if c.get("id") == A1_APPROVAL_ID and c.get("user", {}).get("login") == "serewicz"]
    require(len(a1) == 1 and hashlib.sha256(a1[0]["body"].encode()).hexdigest() == A1_APPROVAL_DIGEST, "A1 approval record changed")
    record = approval(issue, comments, os.environ.get("AUTHORIZATION_ID", ""), control_sha)
    destination = Path(os.environ["RUN_DATA"])
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "context.json").write_text(json.dumps({"issue": issue, "authorization": record,
        "control_sha": control_sha, "spec_sha256": DIGEST, "governance_pin": PIN,
        "approved_a1_authorization": a1[0]["body"]}, indent=2))
    output(control_sha=control_sha)

def paths_ok(paths, p):
    require(0 < len(paths) <= p["max_changed_files"], "empty or excessive patch")
    for name in paths:
        path = PurePosixPath(name)
        require(PATH.fullmatch(name) is not None and not path.is_absolute() and ".." not in path.parts
                and ".git" not in path.parts and "//" not in name and str(path) == name, "unsafe path")
        require(any(name.startswith(r) for r in p["allowed_roots"]), "path outside approved roots")
        require(not any(name == r or name.startswith(r) for r in p["protected_paths"]), "protected path")

def test_suite(candidate):
    test_root = Path(candidate) / "tests"
    require(test_root.is_dir(), "missing test directory")
    a1 = test_root / "a1"
    if (Path(candidate) / "sar_tracker").exists() or a1.exists():
        require(a1.is_dir() and (a1 / "__init__.py").is_file(), "A1 test package missing")
        a1_suite = unittest.TestLoader().discover(str(a1), pattern="test*.py", top_level_dir=str(test_root))
        require(a1_suite.countTestCases() > 0, "no A1 tests discovered")
    suite = unittest.TestLoader().discover(str(test_root), pattern="test*.py")
    require(suite.countTestCases() > 0, "no tests discovered")
    return suite

def validate_tests():
    candidate = Path(os.environ.get("CANDIDATE", str(ROOT)))
    sys.path.insert(0, str(candidate))
    result = unittest.TextTestRunner(verbosity=2).run(test_suite(candidate))
    require(result.wasSuccessful(), "unittest failed")


def result_ok(result, base, cycle):
    require(isinstance(result, dict) and set(result) == {"status", "issue_number", "base_sha", "cycle", "scope_expansion_requested", "summary", "validation"}, "result schema mismatch")
    require(result["status"] == "COMPLETE" and type(result["issue_number"]) is int and result["issue_number"] == 7
        and result["base_sha"] == base and type(result["cycle"]) is int and result["cycle"] == cycle
        and result["scope_expansion_requested"] is False and isinstance(result["summary"], str)
        and 0 < len(result["summary"]) <= 4000 and result["validation"] == {"unittest": "pass"}, "builder result blocked")

def safe_text(data):
    text = data.decode("utf-8")
    require(not re.search(r"(?:gh[pousr]_|github_pat_|sk-ant-|sk-proj-)[A-Za-z0-9_-]{16,}|AKIA[A-Z0-9]{16}|-----BEGIN [A-Z ]*PRIVATE KEY|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}", text), "credential-shaped artifact prohibited")
    for key in ("GH_TOKEN", "AUTOMATION_TOKEN", "OPENAI_API_KEY"):
        secret = os.environ.get(key, "")
        require(not secret or len(secret) < 8 or secret not in text, "credential in artifact")
    return text

def patch_paths(data):
    require(0 < len(data) <= policy()["max_patch_bytes"], "patch size")
    text = safe_text(data)
    require("GIT binary patch" not in text and "Binary files " not in text, "binary patch prohibited")
    names = []
    for line in text.splitlines():
        if line.startswith("diff --git "):
            match = re.fullmatch(r"diff --git a/([A-Za-z0-9_./-]+) b/([A-Za-z0-9_./-]+)", line)
            require(match is not None and match[1] == match[2], "rename or malformed patch")
            names.append(match[1])
        if line.startswith(("new file mode ", "old mode ", "new mode ", "deleted file mode ")):
            require(line.endswith("100644"), "nonregular or executable mode")
    paths_ok(names, policy())
    return names

def pack():
    p = policy()
    candidate = Path(os.environ["CANDIDATE"])
    base = os.environ["BASE_SHA"]
    cycle = int(os.environ["CYCLE"])
    require(SHA.fullmatch(base) is not None and 0 <= cycle <= p["max_correction_cycles"], "base or cycle mismatch")
    require(git(candidate, "rev-parse", "HEAD").decode().strip() == base, "builder changed HEAD")
    names = []
    for args in (("diff", "--cached", "--name-only", "--no-renames", "-z", base),
                 ("diff", "--name-only", "--no-renames", "-z"),
                 ("ls-files", "--others", "--exclude-standard", "-z")):
        names.extend(git(candidate, *args).decode().split("\0"))
    names = sorted(set(n for n in names if n))
    paths_ok(names, p)
    for name in names:
        file = candidate / name
        require(not file.is_symlink() and (not file.exists() or file.is_file()), "nonregular file")
    git(candidate, "add", "--", *names)
    data = git(candidate, "diff", "--cached", "--no-ext-diff", "--no-renames", "--binary", base)
    patch_paths(data)
    result = load(Path(os.environ["RUN_DATA"]) / "result.json")
    result_ok(result, base, cycle)
    safe_text(json.dumps(result).encode())
    artifact = Path(os.environ["ARTIFACT"])
    artifact.mkdir(parents=True, exist_ok=False)
    (artifact / "implementation.patch").write_bytes(data)
    (artifact / "result.json").write_text(json.dumps(result))
    (artifact / "metadata.json").write_text(json.dumps({"base_sha": base, "cycle": cycle,
        "patch_sha256": hashlib.sha256(data).hexdigest()}))

def apply():
    artifact = Path(os.environ["ARTIFACT"])
    candidate = Path(os.environ["CANDIDATE"])
    base = os.environ["BASE_SHA"]
    cycle = int(os.environ["CYCLE"])
    require(0 <= cycle <= policy()["max_correction_cycles"] and SHA.fullmatch(base) is not None, "base or cycle")
    require(git(candidate, "rev-parse", "HEAD").decode().strip() == base, "publish base mismatch")
    result_ok(load(artifact / "result.json"), base, cycle)
    safe_text((artifact / "result.json").read_bytes())
    patch = artifact / "implementation.patch"
    require(patch.is_file() and not patch.is_symlink(), "missing patch")
    data = patch.read_bytes()
    names = patch_paths(data)
    meta = load(artifact / "metadata.json")
    require(meta == {"base_sha": base, "cycle": cycle, "patch_sha256": hashlib.sha256(data).hexdigest()}, "metadata mismatch")
    git(candidate, "apply", "--check", str(patch))
    git(candidate, "apply", str(patch))
    git(candidate, "add", "--all")
    actual = git(candidate, "diff", "--cached", "--name-only", "-z").decode().split("\0")
    require(set(filter(None, actual)) == set(names), "patch paths mismatch")
    for line in git(candidate, "ls-files", "--stage").decode().splitlines():
        mode, _, rest = line.split(" ", 2)
        name = rest.split("\t", 1)[1]
        if name in names:
            require(mode == "100644", "nonregular staged file")
    git(candidate, "-c", "user.name=SAR orchestrator", "-c", "user.email=actions@users.noreply.github.com",
        "-c", "core.hooksPath=/dev/null", "commit", "-m", f"A1 issue #7: bounded agent cycle {cycle}")
    output(candidate_sha=git(candidate, "rev-parse", "HEAD").decode().strip())

def ci_ready(runs, expected, name):
    matches = [r for r in runs if r.get("name") == name and r.get("head_sha") == expected
               and r.get("app", {}).get("slug") == "github-actions"]
    if not matches:
        return False
    latest = max(matches, key=lambda r: r.get("id", 0))
    return latest.get("status") == "completed" and latest.get("conclusion") == "success"

def head():
    pr = api(f"repos/{REPO}/pulls/{os.environ['PR_NUMBER']}")
    require(pr["state"] == "open" and pr["draft"] is True and pr["base"]["ref"] == "main"
        and pr["head"]["repo"]["full_name"] == REPO and pr["head"]["sha"] == os.environ["BASE_SHA"]
        and pr["head"]["ref"] == os.environ["BRANCH"], "PR moved or no longer an eligible draft")
    return pr

def wait_ci():
    expected = os.environ["BASE_SHA"]
    require(SHA.fullmatch(expected) is not None, "invalid head SHA")
    for _ in range(60):
        head()
        runs = pages(f"repos/{REPO}/commits/{expected}/check-runs?filter=latest")
        if ci_ready(runs, expected, policy()["required_ci"]):
            # Authenticate provenance: required check must be CI workflow pull_request run on this head.
            matching = max((r for r in runs if r.get("name") == policy()["required_ci"]
                and r.get("head_sha") == expected and r.get("app", {}).get("slug") == "github-actions"), key=lambda r:r["id"])
            url = matching.get("details_url", "")
            run_match = re.fullmatch(r"https://github.com/serewicz/sar-tracker/actions/runs/(\d+)/job/\d+", url)
            require(run_match is not None, "CI provenance missing")
            run = api(f"repos/{REPO}/actions/runs/{run_match[1]}")
            require(run["path"] == ".github/workflows/ci.yml" and run["event"] == "pull_request"
                and run["head_sha"] == expected, "CI workflow provenance mismatch")
            if run.get("status") != "completed":
                time.sleep(20)
                continue
            require(run.get("conclusion") == "success", "CI workflow failed")
            Path(os.environ["RUN_DATA"]).mkdir(parents=True, exist_ok=True)
            (Path(os.environ["RUN_DATA"]) / "ci-evidence.json").write_text(json.dumps({"head_sha": expected,
                "check_id": matching["id"], "run_id": run["id"], "conclusion": "success"}))
            return
        time.sleep(20)
    raise Blocked("CI missing, failed, or timed out")

def review_ok(review, expected, final=False):
    require(isinstance(review, dict) and set(review) == {"status", "reviewed_sha", "blockers", "important", "follow_up", "summary"}, "review schema")
    require(review["reviewed_sha"] == expected and review["status"] in ("APPROVED", "BLOCKERS", "NEEDS_HUMAN"), "review SHA or status")
    require(isinstance(review["summary"], str) and 0 < len(review["summary"]) <= 4000, "review summary")
    for key in ("blockers", "important", "follow_up"):
        require(isinstance(review[key], list) and len(review[key]) <= 100
            and all(isinstance(i, str) and 0 < len(i) <= 4000 for i in review[key]), "review findings")
    if review["status"] == "APPROVED":
        require(not review["blockers"] and not review["important"], "contradictory approval")
        return "APPROVED"
    require(not final and review["status"] == "BLOCKERS" and bool(review["blockers"]), "review requires human disposition")
    return "BLOCKERS"

def review():
    head()
    safe_text((Path(os.environ["RUN_DATA"]) / "review.json").read_bytes())
    status = review_ok(load(Path(os.environ["RUN_DATA"]) / "review.json"), os.environ["BASE_SHA"], os.environ["CYCLE"] == "3")
    output(status=status)

def safe_review_artifact():
    source = Path(os.environ["RUN_DATA"])
    destination = Path(os.environ["ARTIFACT"])
    destination.mkdir(parents=True, exist_ok=True)
    # Unvalidated/malformed/oversized/credential-shaped agent text is never uploaded.
    review_path = source / "review.json"
    if review_path.exists():
        value = load(review_path)
        require(isinstance(value, dict), "review artifact schema")
        # Validate shape/exact SHA separately from approval (final BLOCKERS remains useful evidence).
        if value.get("status") == "NEEDS_HUMAN":
            probe = dict(value, status="BLOCKERS", blockers=["human disposition required"])
        else:
            probe = value
        review_ok(probe, os.environ["BASE_SHA"], final=False)
        safe_text(review_path.read_bytes())
        (destination / "review.json").write_text(json.dumps(value))
    evidence = source / "ci-evidence.json"
    if evidence.is_file():
        value = load(evidence)
        require(set(value) == {"head_sha", "check_id", "run_id", "conclusion"}
            and value["head_sha"] == os.environ["BASE_SHA"] and value["conclusion"] == "success"
            and type(value["check_id"]) is int and type(value["run_id"]) is int, "CI evidence schema")
        (destination / "ci-evidence.json").write_text(json.dumps(value))

def diagnostics():
    # Fail-safe metadata only: no agent text, diff, environment, credentials, or model transcript.
    destination = Path(os.environ["RUN_DATA"])
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "diagnostics.json").write_text(json.dumps({"state": "BLOCKED" if os.environ.get("JOB_STATUS") != "success" else "COMPLETED",
        "run_id": os.environ.get("GITHUB_RUN_ID"), "job": os.environ.get("GITHUB_JOB"),
        "cycle": os.environ.get("CYCLE"), "base_sha": os.environ.get("BASE_SHA"), "spec_sha256": DIGEST,
        "governance_pin": PIN, "content_omitted": True}))

def record_blocked():
    require(os.environ.get("RECORD_BLOCKED") == "true", "blocked-state issue writes not authorized")
    policy()
    require(os.environ.get("ISSUE_NUMBER") == "7", "issue mismatch")
    run_id = os.environ["GITHUB_RUN_ID"]
    require(run_id.isdigit(), "run id")
    api(f"repos/{REPO}/issues/7/comments", {"body": f"Orchestration BLOCKED. Run https://github.com/{REPO}/actions/runs/{run_id}. Safe diagnostics are workflow artifacts; no A1 completion, merge or issue closure is asserted."})

if __name__ == "__main__":
    try:
        commands = {"gate": gate, "validate-tests": validate_tests, "pack": pack, "apply": apply, "head": head, "wait-ci": wait_ci,
                    "review": review, "safe-review-artifact": safe_review_artifact, "diagnostics": diagnostics, "record-blocked": record_blocked, "policy": policy}
        require(len(sys.argv) == 2 and sys.argv[1] in commands, "invalid command")
        commands[sys.argv[1]]()
    except (Blocked, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        print("Orchestration blocked: authority, policy, artifact, API or validation gate failed.")
        sys.exit(1)
