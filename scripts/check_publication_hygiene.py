"""Conservative public-repository hygiene scan; NOT a rights or secrets audit.

Reads each reachable Git blob once, including historical versions present in
the fetched refs. Never prints matched credential values or file contents.
This does not inspect external artifacts, PR comments, CI logs, or private code.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

PATTERNS = {
    "openai_like_token": re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    "github_classic_token": re.compile(rb"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b"),
    "github_fine_grained_token": re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{50,}\b"),
    "aws_access_key_id": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "google_api_key": re.compile(rb"\bAIza[0-9A-Za-z_-]{35}\b"),
    "slack_like_token": re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    "pem_private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "credentialed_url": re.compile(rb"https?://[^\s/@:]+:[^\s/@]+@[A-Za-z0-9.-]+"),
}

MAX_BLOB_BYTES = 2_000_000
SUSPICIOUS_NAMES = {".env", ".env.local", ".env.production", "id_rsa",
                    "id_ed25519", "credentials.json", "service-account.json"}


def git(*args: str) -> bytes:
    proc = subprocess.run(["git", *args], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=False)
    if proc.returncode:
        raise RuntimeError("git command failed; check repository and fetch scope")
    return proc.stdout


def scan_blob(data: bytes) -> list[str]:
    return [name for name, regex in PATTERNS.items() if regex.search(data)]


def self_test() -> None:
    assert "openai_like_token" in scan_blob(b"prefix sk-" + b"A" * 26)
    assert "github_classic_token" in scan_blob(b"ghp_" + b"B" * 36)
    assert "aws_access_key_id" in scan_blob(b"AKIA" + b"Q" * 16)
    assert "pem_private_key" in scan_blob(
        b"-----BEGIN PRIVATE KEY-----\nsynthetic\n")
    assert scan_blob(b"ordinary synthetic source without credentials") == []
    print("Hygiene pattern self-tests PASS")


def scan_history() -> int:
    head = git("rev-parse", "HEAD").decode("ascii").strip()
    lines = git("rev-list", "--objects", "--all").decode("utf-8", "replace").splitlines()
    blob_count = 0
    oversized = 0
    suspicious_filenames = set()
    alerts: list[dict] = []
    for line in lines:
        sha, _, path = line.partition(" ")
        if not re.fullmatch(r"[0-9a-f]{40,64}", sha):
            continue
        if path and Path(path).name.lower() in SUSPICIOUS_NAMES:
            suspicious_filenames.add(path)
        if git("cat-file", "-t", sha).strip() != b"blob":
            continue
        blob_count += 1
        size = int(git("cat-file", "-s", sha).strip())
        if size > MAX_BLOB_BYTES:
            oversized += 1
            continue
        blob = git("cat-file", "blob", sha)
        for kind in scan_blob(blob):
            # No matched text, raw data, credentials, or source excerpts.
            alerts.append({"category": kind, "blob_sha_prefix": sha[:12]})

    tracked = git("ls-files", "-z").decode("utf-8", "replace").split("\0")
    tracked = [name for name in tracked if name]
    license_present = any(
        Path(name).name.upper().startswith(("LICENSE", "LICENCE", "COPYING"))
        for name in tracked
    )
    report = {
        "schema": "workcoord.publication-hygiene/v0",
        "head": head,
        "scope": "reachable_git_blobs_in_fetched_refs_not_all_remote_history",
        "git_objects_enumerated": len(lines),
        "blobs_scanned": blob_count - oversized,
        "oversized_blobs_skipped": oversized,
        "credential_pattern_alerts": sorted(alerts, key=lambda x: (x["category"], x["blob_sha_prefix"])),
        "suspicious_filenames": sorted(suspicious_filenames),
        "license_file_present": license_present,
        "human_provenance_and_confidentiality_approved": False,
        "external_artifacts_and_pr_comments_scanned": False,
        "publication_authorized": False,
        "note": "A clean pattern scan cannot establish rights, absence of secrets, or safe publication.",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if alerts or suspicious_filenames or oversized:
        print("Hygiene scan BLOCKED: review findings without revealing values.", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--self-test", action="store_true")
    cli.add_argument("--history", action="store_true")
    args = cli.parse_args()
    if args.self_test:
        self_test()
    if args.history:
        return scan_history()
    if not args.self_test:
        cli.error("specify --self-test and/or --history")
    return 0


if __name__ == "__main__":
    sys.exit(main())
