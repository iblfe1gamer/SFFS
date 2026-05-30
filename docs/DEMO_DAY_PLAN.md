# SFFS Demo Day — Implementation Plan

**Branch**: `claude/military-cyber-evaluation-AAU5e`
**Rule**: `pytest tests -q` stays green after every step.
**Estimate**: 6–7 hrs for items 1–13. Items 14–15 optional polish.

---

## Execution Order & Status

| # | Priority | Item | File(s) | Est. | Status |
|---|----------|------|---------|------|--------|
| 1 | P1-A | NameError crash in `authenticateUser` | `code2/f09_authenticate_user.py:185` | 15 min | [x] |
| 2 | P1-C | Remove hardcoded `demo_user` prefill | `main-code/main.py:144` | 2 min | [x] |
| 3 | P1-B | Thread encrypt/decrypt ops | `code3/sffs_ui.py` — fixed `_WorkerThread` → `WorkerThread` | 1.5 hr | [x] |
| 4 | P3-A | Confirm-password field in register flow | `code3/sffs_ui.py LoginWindow._pw2` | 20 min | [x] |
| 5 | P3-B | Live password policy feedback label | `code3/sffs_ui.py._refresh_policy_hint` | 30 min | [x] |
| 6 | P2-A | Live security status panel | `sffs_core.py _gui_alert_callback` + `main.py set_gui_alert_callback` | 45 min | [x] |
| 7 | P2-B | Live audit log panel — last 5 events | `code3/sffs_ui.py SecurityPage._refresh_logs` 3s timer | 30 min | [x] |
| 8 | P2-C | User-friendly error messages | `code3/sffs_ui.py._friendly_error_str` | 20 min | [x] |
| 9 | P2-E | End session vs Logout button fix | `code3/sffs_ui.py SFFSWindow._do_logout/_do_emergency_end_session` | 30 min | [x] |
| 10 | P4-A | Move master password off CLI args to stdin | `main-code/sffs_core.py` — password via `proc.communicate(input=...)` | 45 min | [x] |
| 11 | P4-B | WrapStore temp file inside sandbox (not /tmp) | `main-code/wrap_store.py` + `sffs_core.py:222` | 30 min | [x] |
| 12 | P4-C | `chmod 0o700` on sandbox subdirectories | `code2/f07_create_isolated_sandbox.py:143-145` | 15 min | [x] |
| 13 | P5-B | Delete duplicate `LoginWindow` class | already absent from `f14_ui_dashboard.py` | 10 min | [x] |
| 14 | P5-A | Wire `FileManagerExplorer` into dashboard | `code3/sffs_ui.py ExplorerPage` (sidebar page 4) | 45 min | [x] |
| 15 | P5-C | Confirm dialog before logout | `code3/sffs_ui.py SFFSWindow._do_logout` | 10 min | [x] |

---

## P1 — Demo-Killing Bugs

### P1-A: NameError crash in `authenticateUser` `[ ]`
**File**: `code2/f09_authenticate_user.py:199-203`

`pw = PasswordHasher(...)` is instantiated at line 230 but used at line 201. Unknown username → instant `NameError` → fast return → timing oracle (username enumeration).

**Fix**: Move `pw = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)` to the **first line** of `authenticateUser()`, before the `sqlite3.connect(...)` call (line 185).

**Test**: Add to `tests/test_student2.py` — assert unknown username and wrong-password responses take within 200ms of each other (`time.perf_counter`).

---

### P1-B: Unfreeze UI — thread encrypt/decrypt `[ ]`
**Files**: `main-code/main.py:255-328`, `code3/f18_thread_controller.py`

`do_encrypt()` and `do_decrypt()` call core operations synchronously on the Qt main thread → window freezes → OS "Not Responding."

`f18_thread_controller.py` already provides `WorkerThread` and `threadController()`.

**Fix for `do_encrypt()`**:
1. Disable `win._enc` and `win._dec` buttons immediately
2. Show `win._bar` (progress bar), set indeterminate: `setMaximum(0)`
3. Wrap `core.encryptFileOperation(Path(fp))` in `WorkerThread`
4. `signals.result` → update `win._status`, re-enable buttons, hide bar, call `win.refresh_sandbox_list()`
5. `signals.error` → `QMessageBox.warning` with friendly text (see P2-C)

Repeat same pattern for `do_decrypt()` (both Sandbox and Disk branches).

**Critical**: Store worker in `win._worker` — Qt garbage-collects threads without a reference.

---

### P1-C: Remove hardcoded `demo_user` prefill `[ ]`
**File**: `main-code/main.py:144`

```python
u.setText("demo_user")   # DELETE THIS LINE
```

---

## P2 — Make Panels Show Real State

### P2-A: Live security status panel `[ ]`
**Files**: `code3/f14_ui_dashboard.py:282-285`, `main-code/sffs_core.py:134`, `main-code/main.py`

"All clear" label is hardcoded. `showSecurityAlert()` exists but is never called.

**Fix**:
- Add `self._gui_alert_callback = None` to `SFFSCore.__init__`
- Add `set_gui_alert_callback(fn)` method to `SFFSCore`
- In `_on_threat_detected`: call `self._gui_alert_callback(f"THREAT: {threat_type}", "CRITICAL")` if set
- In `_on_usb_removed`: call `self._gui_alert_callback("USB REMOVED — locking", "CRITICAL")`
- In `run_full_app()`: after creating `win`, call `core.set_gui_alert_callback(win.showSecurityAlert)`

---

### P2-B: Live audit log panel — last 5 events `[ ]`
**Files**: `code3/f14_ui_dashboard.py:383-385`, `main-code/main.py`

`refreshLogs()` exists but is never called.

**Fix**: After each encrypt/decrypt/login operation completes, call:
```python
if core.logger:
    win.refreshLogs(core.logger.viewLogs(limit=5))
```
Call in: `signals.result` callbacks for both workers, and immediately after `core.login()` succeeds.

Fix `refreshLogs()` to format entries as `[LEVEL] event` per line (currently does raw `str(e)` on dict).

---

### P2-C: User-friendly error messages `[ ]`
**File**: `main-code/main.py:270-277, 316-322`

Map exception types to plain English (no raw tracebacks on screen):

| Exception | Message |
|-----------|---------|
| `FileNotFoundError` | "File not found. Has it been moved?" |
| `SecurityError` | "File appears tampered — decryption refused." |
| `RuntimeError` containing "Session password" | "Session expired. Please log out and log back in." |
| `FileExistsError` | "Output file already exists. Choose a different location." |
| All others | "Operation failed. Check the audit log for details." |

---

### P2-E: Merge End Session / Logout button confusion `[ ]`
**File**: `code3/f14_ui_dashboard.py:214-216, 309-312`

Both buttons currently call `on_logout`.

**Fix**:
- "End session" → confirmation dialog → `emergencyLock("MANUAL", ...)` (demonstrates 7-step wipe)
- "Logout" → `core.logout()` → `app.quit()` (normal graceful path)

Confirmation text: `"This will wipe your sandbox immediately. Continue?"`

---

## P3 — Registration Must Not Fail On Stage

### P3-A: Confirm-password field in register flow `[ ]`
**File**: `main-code/main.py:135-158`

Add second `QLineEdit` with `EchoMode.Password`, placeholder `"Confirm password"`.

In `do_register()`: check both fields match **before** `registerUser` call. If mismatch → `QMessageBox.warning("Passwords do not match.")` before the Argon2 call.

---

### P3-B: Live password policy feedback `[ ]`
**File**: `main-code/main.py:135-200`

Add `QLabel` below password field, updates on `p.textChanged`:
- **Red**: lists unmet rules (length, uppercase, digit, special)
- **Green**: "Password meets policy" when all pass

Use same checks as `f09_authenticate_user.py:125-133`.

---

## P4 — Security Fixes

### P4-A: Move master password off CLI args to stdin `[ ]`
**Files**: `main-code/sffs_core.py:347-370`, `main-code/isolated_worker.py:184-215`

`master_password` in `--payload` CLI arg is visible in `ps aux`.

**Fix in `sffs_core.py._decrypt_via_worker()`**:
- Remove `"--payload", json.dumps(envelope)` from `Popen` args
- Add `stdin=subprocess.PIPE`
- Write `json.dumps(envelope).encode()` to `proc.stdin`, then close it

**Fix in `isolated_worker.py.main()`**:
- Remove `ap.add_argument("--payload", ...)`
- Read `sys.stdin.read()` and parse as envelope JSON

**Test**: `pytest tests/test_worker_hardening.py -q` must pass.

---

### P4-B: WrapStore temp file inside sandbox `[ ]`
**Files**: `main-code/wrap_store.py:60-68`, `main-code/sffs_core.py:178`

`tempfile.NamedTemporaryFile` uses system `/tmp` — decrypted keystore leaks outside sandbox.

**Fix**:
- `WrapStore.__init__`: add `tmp_dir: Path = None` parameter
- `_DbContext.__enter__`: pass `dir=str(self._tmp_dir)` to `NamedTemporaryFile`
- Wrap `__enter__` body in `try/finally` to guarantee temp file deletion on exception
- `sffs_core.py:178`: pass `tmp_dir=Path(self.sandbox["temp_dir"])` when constructing `WrapStore`

**Test**: Add to `tests/test_worker_hardening.py` — verify no `.db` files exist outside `tmp_dir` after `WrapStore.lookup()`.

---

### P4-C: `chmod 0o700` on sandbox subdirectories `[ ]`
**File**: `code2/f07_create_isolated_sandbox.py:97-102`

After each `mkdir`, add `os.chmod(d, 0o700)` (Linux only).

`isSandboxIntact()` should also verify `decrypted/` subdirectory permissions, not just root.

---

## P5 — Cosmetic Polish (only if time permits)

### P5-A: Wire FileManager into dashboard `[ ]`
**File**: `code3/f14_ui_dashboard.py`

`FileManagerExplorer` (f15) is built but never shown. Either:
- Add as tab/pane on right side of splitter, rooted at `paths["usb_root"]`
- Or delete it (don't leave orphaned — reviewers will ask)

---

### P5-B: Delete duplicate `LoginWindow` class `[ ]`
**File**: `code3/f14_ui_dashboard.py:388-428`

Second login implementation that bypasses `SFFSCore.login()`. Real app uses login dialog in `main.py`.

Delete `LoginWindow` and `uiDashboard()` (line 431) if not called. Update any imports.

---

### P5-C: Confirm before logout `[ ]`
**File**: `main-code/main.py:208-209`

```python
def handle_logout() -> None:
    if QMessageBox.question(win, "SFFS", "End session and wipe sandbox?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    ) == QMessageBox.StandardButton.Yes:
        core.logout()
        app.quit()
```

---

## Checklist Summary

```
[x] 1.  P1-A  NameError fix (authenticateUser) — pw instantiated at line 185
[x] 2.  P1-C  Remove demo_user prefill — not present in sffs_ui.py LoginWindow
[x] 3.  P1-B  Thread encrypt/decrypt — WorkerThread wired; fixed _WorkerThread naming bug
[x] 4.  P3-A  Confirm-password field — _pw2 field in LoginWindow, checked in _try_register
[x] 5.  P3-B  Live policy feedback — _refresh_policy_hint on textChanged, red/green
[x] 6.  P2-A  Live security status panel — _gui_alert_callback in SFFSCore; real threats + USB removal update UI before emergencyLock; setattr hack removed
[x] 7.  P2-B  Live audit log panel — _refresh_logs on 3s timer, last 10 events
[x] 8.  P2-C  Friendly error messages — _friendly_error_str maps all exception types
[x] 9.  P2-E  End session vs Logout — TopBar end_session = wipe, Sidebar logout = graceful
[x] 10. P4-A  Password off CLI → stdin — master_password via proc.communicate(input=...)
[x] 11. P4-B  WrapStore /tmp fix — tmp_dir param, sffs_core passes sandbox/temp
[x] 12. P4-C  Sandbox chmod 0o700 — lines 143-145 in f07, all 3 subdirs
[x] 13. P5-B  Delete LoginWindow — not present in f14_ui_dashboard.py
[x] 14. P5-A  Wire FileManager — ExplorerPage in sffs_ui.py, sidebar page 4
[x] 15. P5-C  Logout confirm dialog — _do_logout confirmation before wipe
```
