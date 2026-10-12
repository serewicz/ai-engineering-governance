"""Validate local Markdown targets and key cross-document candidate invariants.

Semantic review and remote URL verification remain separate responsibilities.
"""
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
CORE = ("AI_ENGINEERING_GOVERNANCE.md", "AGENT_WORKFLOW.md", "PROJECT_AGENT_CONFIG.md", "AGENT_HANDOFF_TEMPLATE.md", "README.md", "TIER_ROUTING.md", "proposals/HARVESTGUARD_ADOPTION_V1.1.0.md")


def anchors(text):
    found = set()
    counts = {}
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, re.M):
        slug = re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
        count = counts.get(slug, 0)
        found.add(slug if not count else f"{slug}-{count}")
        counts[slug] = count + 1
    return found


def validate():
    failures = []
    texts = {}
    for name in CORE:
        p = ROOT / name
        if not p.is_file():
            failures.append(f"Missing required document: {name}")
        else:
            texts[name] = p.read_text()
    for path in ROOT.rglob("*.md"):
        text = path.read_text()
        for raw in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
            url = urlsplit(raw)
            if url.scheme or url.netloc:
                continue
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            if not target.is_relative_to(ROOT) or not target.is_file():
                failures.append(f"Invalid local link in {path.relative_to(ROOT)}: {raw}")
            elif url.fragment and unquote(url.fragment) not in anchors(target.read_text()):
                failures.append(f"Missing anchor in {path.relative_to(ROOT)}: {raw}")
        if not text.endswith("\n"):
            failures.append(f"Missing final newline: {path.relative_to(ROOT)}")
        for pattern in (r"-----BEGIN .*PRIVATE KEY", r"\b(?:ghp_|github_pat_|AKIA|sk-proj-)[A-Za-z0-9_]+", r"/(?:Users|home|private|tmp)/"):
            if re.search(pattern, text):
                failures.append(f"Sensitive token or local path pattern: {path.relative_to(ROOT)}")
    # These are limited structural assertions, not proof of semantic equivalence.
    expected = {
        "AI_ENGINEERING_GOVERNANCE.md": ("**Version:** 1.1.0", "## Non-negotiable controls", "### Tier 0", "### Tier 1", "### Tier 2", "Every task starts at **Tier 2**", "Owner determines merge authority", "`IMPORTANT`", "## Release gate", "MINOR adds compatible procedures", "## Project merge authorization and delegation", "no universal human-only merge gate"),
        "AGENT_WORKFLOW.md": ("1.1.0 candidate", "start at Tier 2", "cycle 0", "two corrections", "three corrections", "Owner-approved project policy", "justified `NOT REQUIRED`"),
        "PROJECT_AGENT_CONFIG.md": ("Reusable template", "1.1.0 candidate", "adoption inactive", "exact commit", "independent of builder", "Deviation register", "initial review is cycle 0"),
        "AGENT_HANDOFF_TEMPLATE.md": ("1.1.0 candidate", "Positive eligibility evidence", "Reviewed exact SHA", "Security disposition", "IMPORTANT", "Separate release/publication authorization"),
        "README.md": ("v1.1.0", "not a published release", "bb08e871568f953f36e061d7fd89e467598bdcac"),
        "TIER_ROUTING.md": ("1.1.0 candidate", "1 |", "2–4", "not a production authorization gate"),
        "proposals/HARVESTGUARD_ADOPTION_V1.1.0.md": ("adoption inactive", "77b52ac56833d9821008d1466683bb9969ed7641", "initial review is cycle 0", "3 automated correction", "No live settings change", "fixture", "checkpoints"),
    }
    for name, phrases in expected.items():
        for phrase in phrases:
            if phrase.lower() not in texts.get(name, "").lower():
                failures.append(f"Missing invariant phrase in {name}: {phrase}")
    # Active reusable guidance must not revive the superseded universal gate.
    for name in ("AI_ENGINEERING_GOVERNANCE.md", "AGENT_WORKFLOW.md", "README.md", "TIER_ROUTING.md"):
        for obsolete in ("Merge remains human-only", "Retain human-only merge authority", "Human-only merge and every mandatory control", "Unresolved version decision", "label is provisional"):
            if obsolete.lower() in texts.get(name, "").lower():
                failures.append(f"Superseded gate/version language in {name}: {obsolete}")
    contract = texts.get("AI_ENGINEERING_GOVERNANCE.md", "")
    for phrase in ("approved project policy", "bounded automated", "independent review", "exact PR head SHA", "required successful checks", "stop execution and escalate", "HarvestGuard's human-only merge requirement is mandatory"):
        if phrase not in contract:
            failures.append(f"Missing merge authority safeguard: {phrase}")
    return failures


if __name__ == "__main__":
    errors = validate()
    if errors:
        print("\n".join(errors))
        sys.exit(1)
    print("PASS: required documents, local links/anchors, candidate versions, structural invariants and sensitive-path/token patterns.")
