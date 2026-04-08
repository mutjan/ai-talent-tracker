---
phase: 1
slug: 脚本整合
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-08
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `python3 -m pytest tests/ -x -q` |
| **Full suite command** | `python3 -m pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/ -x -q`
- **After every plan wave:** Run `python3 -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | CONS-01 | unit | `python3 -m pytest tests/test_search.py::test_load_events -x -q` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | CONS-01 | unit | `python3 -m pytest tests/test_search.py::test_tavily_search_call -x -q` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | CONS-02 | unit | `python3 -m pytest tests/test_search.py::test_query_config_structure -x -q` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | CONS-03 | unit | `python3 -m pytest tests/test_search.py::test_domain_groups -x -q` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 1 | CONS-04 | unit | `python3 -m pytest tests/test_search.py::test_candidate_output_format -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/__init__.py` — package marker
- [ ] `tests/conftest.py` — shared fixtures (sample events, mock API responses)
- [ ] `tests/test_search.py` — stubs for all CONS-01 to CONS-04 tests
- [ ] `pip install pytest` — if not already installed

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Old scripts deleted | CONS-01 | File deletion is environment-specific | Verify `scripts/talent_search.py` and `scripts/tavily_search.py` no longer exist |
| Manual dry-run end-to-end | CONS-01, CONS-04 | Requires TAVILY_API_KEY | Run `python3 scripts/search.py --days 1` and verify output format |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
