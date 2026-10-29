# Issues found in attendance_tracker.py

Line numbers are from the tool reports (before). Severity is Bandit's, or Pylint/Flake8 category.

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| TLS verification disabled (B501) | Security, High | 61 | `requests.post(..., verify=False)` accepts any certificate, so the ERP call can be intercepted (MITM). | Removed `verify=False` (default is verify=True). |
| Wildcard injection / shell=True in backup (B609, B602, B607) | Security, High | 65 | `Popen("tar ... *.csv", shell=True)`: a file named `--checkpoint-action=...` becomes a tar option. Partial path `tar`. | Replaced with Python `tarfile` + `glob`; no subprocess, no shell. |
| Hardcoded ERP API key | Security (found manually; no tool flagged it) | 13 | Live key committed in source. | Read from `os.environ["ERP_API_KEY"]`; rotate the leaked key. |
| Insecure TLS default (B503) | Security, Medium | 67 | `ssl.PROTOCOL_TLSv1` is deprecated and broken. | `ssl.create_default_context()` with `minimum_version = TLSv1_2`. |
| shell=True in job runner (B604) | Security, Medium | 70-74 | `run_job(..., shell=True)` allows command injection. | `run_job` takes an argument list and has no shell option. |
| No request timeout (B113 / W3101) | Security + Bug, Medium | 61 | `requests.post` can hang forever. | Added `timeout=10`. |
| Mutable default argument (W0102) | Bug | 19 | `register={}` is shared across all calls, so `main()` only appears to work because of it. | Default `None`, create a new dict inside; `main()` now passes its own register. |
| Eligibility off by one | Logic bug (no tool flags it) | 31 | `> 75` made exactly 75% not eligible (demo printed `Is 75% eligible? False`). | Changed to `>=`. |
| `latest_date` compares strings | Logic bug | 46-48 | `"2026-9-3"` sorts after `"2026-09-05"` as text, so the wrong date was returned. | Compare with `datetime.strptime` (also uses the `datetime` import). |
| Division by zero / truncation | Logic bug | 24-28 | A student with no records crashes; `int()` turned 66.67 into 66. | Return 0 when no records; `round(..., 2)`. |
| `shortage_list` returns None | Design | 33-40 | Callers must special-case None. | Return an empty list; use a list comprehension and `not`. |
| CSV/formula injection | Security (manual) | 50-57 | Name `=HYPERLINK(...)` is written as a live formula in Excel. | `_safe_cell()` prefixes `'` to cells starting with `= + - @`. |
| File not closed, no encoding | Pylint R1732 / W1514 | 51-57 | `open()` without `with`, and no encoding/newline. | `with open(path, "w", newline="", encoding="utf-8")`. |
| Unused imports | Pylint W0611, Flake8 F401 | 1, 4, 6 | `os`, `json`, `datetime` unused. | Removed `json`/`subprocess`; `os` and `datetime` are now used. |
| Naming (C0103) and missing docstrings (C0114/C0116) | Pylint | all functions | camelCase names, no docstrings. | snake_case names and one-line docstrings. |
| Comparison to False (C0121 / E712), `True if ... else False` (R1719), non-generator `any` (R1729), redundant comprehension (R1721), `.items()` (C0206) | Pylint/Flake8 | 31, 36, 44, 47, 54 | Style and idiom problems. | `not ...`, return the comparison directly, generator expression, `.items()`. |
| PEP 8 layout (E302, E305, E501) | Flake8 | many | One blank line between functions, lines over 79 chars. | Two blank lines, wrapped long lines, `if __name__ == "__main__":` guard. |

## Result

| Tool | Before | After |
|------|--------|-------|
| Pylint | 4.55/10 | 10.00/10 |
| Bandit | 2 High, 3 Medium, 3 Low | No issues |
| Flake8 | 23 findings | 0 |
