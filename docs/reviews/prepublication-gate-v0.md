# P0 pre-publication gate — WorkCoord

**Status:** OPEN. This checklist is not a sign-off, a code-origin certification, or approval to merge.
**Baseline reviewed:** `5f26c841938cbf14f9a79b050daf7c7dc6963d4d` (draft PR #11, stacked on #1–#10).
**Protected branch:** `main` must remain unchanged until owner approval and required checks.

## Evidence available

- The latest PR #11 GitHub Actions run, `42177796386`, reports success for Python 3.10, 3.11, and 3.13. These are fictional deterministic correctness checks, not independent benchmark outcomes or safe-publication evidence.
- A limited, read-only connector inspection of high-priority files found no obvious credential patterns. This did not exhaustively examine all historical blobs, artifacts, PR comments, CI logs, or architectural confidentiality.
- `scripts/check_publication_hygiene.py` adds a **redacted, heuristic** scan of reachable Git blobs in fetched refs; `.github/workflows/publication-hygiene.yml` executes it on PRs. It prints categories and truncated object IDs only, never matched values. It does not claim to detect every secret or prove ownership.

## Blocking owner / reviewer tasks

- [ ] **Copyright and provenance:** individually review source, examples, fixtures, docs, history and derivation; confirm no copying or disguised translation of nonpublic implementations or restricted materials.
- [ ] **Semantic confidentiality:** inspect terminology, architecture, synthesized examples, issue names, logs, generated artifacts, PR comments and history for inferable private information; automated regex checks are insufficient.
- [ ] **Licensing:** select and approve a license (or explicitly keep no redistribution permission). Do not invent copyright holders, consent, licenses or grants.
- [ ] **History and artifacts:** conduct a separate full review of all accessible branches, Git history, downloadable CI artifacts, PR conversations and external releases; check for tokens and sensitive content; rotate any confirmed exposed keys immediately.
- [ ] **Trust boundaries:** confirm docs never imply authenticated reviewers/sources, a secure production authority, external semantic validity, or real-agent comparative success.
- [ ] **Merge policy:** turn on GitHub branch protection/ruleset with required status checks and explicit review; obtain a human sign-off and merge stacked PRs sequentially only with owner authorization.
- [ ] **External experiment:** choose Harbor/Terminal-Bench version and reproducible agent harness after this publication gate; no provider credentials in Git, CI artifacts or public trajectories.

## Scanner limits

The scanner examines reachable blobs in refs fetched by the checkout, not deleted/unreachable objects, all remote refs, logs, releases or private data. It skips objects larger than 2 MB and reports that limitation. A passing scan is **necessary hygiene only** and cannot approve public release.

## Exit record (fill manually)

- Reviewer and review date:
- Full reviewed commit SHA(s):
- License decision and evidence:
- Historical/confidentiality review scope:
- CI and hygiene-run links:
- Open findings / exceptions:
- Owner decision: **PENDING** (do not merge automatically)
