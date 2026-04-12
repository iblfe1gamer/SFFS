# SFFS — Phase 6: Complete Documentation

You are building SFFS (Smart File Fortify System). This is Phase 6: write all documentation files inside `docs/`.

**Assume Phases 0–5 are complete.** All code exists. Documentation must accurately reflect the actual implementation.

---

## Files to Create

---

### `docs/ARCHITECTURE.md`

Write a comprehensive architecture document covering:

**1. System Overview**
- One-paragraph description of SFFS
- The core problem it solves
- Why existing tools fail (VeraCrypt needs admin, BitLocker is Windows-only, etc.)

**2. Module Map** (ASCII art diagram)
```
┌─────────────────────────────────────────────────────────┐
│                    SFFS Application                      │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Student 1  │  │  Student 2   │  │  Student 3    │  │
│  │   code1/    │  │   code2/     │  │   code3/      │  │
│  │ ─────────── │  │ ──────────── │  │ ───────────── │  │
│  │ Crypto Core │  │ Runtime Sec  │  │ Architecture  │  │
│  │  AES-256    │  │  Sandbox     │  │  PyQt6 UI     │  │
│  │  RSA-2048   │  │  Auth        │  │  USB Detect   │  │
│  │  SHA-256    │  │  Monitor     │  │  Cloud Sync   │  │
│  └──────┬──────┘  └──────┬───────┘  └──────┬────────┘  │
│         └────────────────┴──────────────────┘           │
│                    main-code/sffs_core.py                │
└─────────────────────────────────────────────────────────┘
```

**3. Initialization Sequence** (step-by-step with which function is called)

**4. Encrypt Operation Flow** (complete call chain from UI click to .sffs file written)

**5. Decrypt Operation Flow** (complete call chain including integrity check)

**6. Emergency Lock Flow** (what happens, in order, when USB is pulled)

**7. Data Flow Diagram** (what data moves between modules and in what form — bytes, paths, tokens)

**8. The .sffs File Format** (full specification with field sizes and purpose)

**9. Cross-Platform Strategy** (how each platform difference is handled)

---

### `docs/API_REFERENCE.md`

Write a complete API reference for all 18 functions. For each function:

```markdown
## functionName(param1: type, param2: type = default) -> ReturnType

**Module:** code1/f01_generate_key_pairs.py  
**Student:** Student 1 — Crypto-Security

### Description
One paragraph explaining what this function does.

### Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| param1    | Path | Yes      | —       | ...         |

### Returns
Dict with fields:
| Field | Type | Description |
|-------|------|-------------|
| field | str  | ...         |

### Raises
| Exception | Condition |
|-----------|-----------|
| ValueError | If key_size < 2048 |

### Security Notes
- Bullet points of security-relevant behavior

### Example
\`\`\`python
from code1.f01_generate_key_pairs import generateKeyPairs
result = generateKeyPairs(Path("./keys"), key_size=2048)
print(result["key_id"])
\`\`\`

### Called By
- `SFFSCore.encryptFileOperation()`

### Calls
- `secureKeyStorage()` (must be called next)
```

Cover all 18 functions: F-01 through F-18.

---

### `docs/SECURITY_MODEL.md`

Write a detailed security model document covering:

**1. Threat Model**
- Who the adversary is (malware on infected PC, physical attacker with RAM dump tools)
- What the adversary can do (read files, read RAM, attach debuggers, intercept network)
- What the adversary cannot do (break AES-256, break RSA-2048, break SHA-256)

**2. Cryptographic Algorithms**

For each algorithm, explain:
- What it is
- Why it was chosen (vs alternatives)
- Security strength (equivalent bits, years to brute force)
- Implementation details (mode, parameters, key size)

Algorithms to cover:
- AES-256-GCM (encryption)
- RSA-2048 with OAEP (key wrapping)
- SHA-256 (integrity)
- Argon2id (password hashing) — with parameter justification (OWASP 2023)
- PBKDF2-SHA256 (key derivation for keystore) — with iteration count justification

**3. Security Properties**
- Confidentiality: how AES-256 ensures content privacy
- Integrity: how SHA-256 + GCM auth tag detect tampering
- Authentication: how Argon2id and RSA identity prevent unauthorized access
- Non-repudiation: how the audit log provides a tamper-evident trail

**4. Attack Mitigations**

For each attack, describe the mitigation:

| Attack | Mitigation |
|--------|-----------|
| Malware reading decrypted files | Isolated sandbox — files never touch host OS disk |
| Cold boot attack (RAM freeze) | secureMemoryWipe() — 3-pass DOD wipe of sensitive buffers |
| Debugger attachment | monitorProcess() — detects and triggers emergency lock |
| Brute-force password | Argon2id (memory-hard) + lockout policy |
| Rainbow table attack | Random salt per keystore |
| Ciphertext tampering | AES-GCM auth tag + SHA-256 pre-encryption hash |
| Key theft from USB | Private key AES-256-GCM encrypted with PBKDF2-derived key |
| Log tampering | Per-entry SHA-256 hash chain |
| Timing attack | hmac.compare_digest() for all hash comparisons |
| USB loss | Encrypted cloud backup of key bundles |

**5. Known Limitations**
- Python's GC means `bytes` and `str` objects cannot be reliably wiped
- Windows UAC may limit sandbox permission enforcement on some configurations
- Cloud backup requires internet — offline-only users have no remote recovery
- Side-channel attacks (power analysis, EM) are not in scope for this software implementation

---

### `docs/DEVELOPER_GUIDE.md`

Write a developer guide covering:

**1. Development Setup**
```bash
git clone <repo>
cd SFFS
pip install -r main-code/requirements.txt
pip install pytest pytest-cov
python main-code/main.py --headless  # verify setup
```

**2. Project Structure** (full annotated directory tree)

**3. How to Add a New Function**
- Where to put the file (which code folder, which student)
- Required docstring format
- Required logging call
- Required import comment format
- How to register it in `sffs_core.py`
- How to add tests

**4. Code Style Guide**
- All imports need WHY comments
- All functions need Args/Returns/Raises/Security docstrings
- Use `pathlib.Path` — never `os.path` string joins
- Use `bytearray` — never `bytes` — for sensitive data that will be wiped
- Always log entry and exit of security-critical functions
- Handle both Windows and Linux explicitly

**5. Running Tests**
```bash
pytest tests/ -v                          # all tests
pytest tests/test_student1.py -v          # one module
pytest tests/ --cov=code1 --cov-report=html  # coverage
```

**6. How the Modules Integrate** (call graph for the encrypt and decrypt operations)

**7. Common Issues & Solutions**
- PyQt6 on Linux: `sudo apt install python3-pyqt6 libgl1-mesa-glx` if pip install fails
- `pycryptodome` vs `pycrypto`: always use `pycryptodome` (pycrypto is unmaintained and has known vulnerabilities)
- SQLite on Windows: no issues; on Linux: ensure the USB is mounted with `exec` permission
- Google Drive API: `client_secret.json` must be in `config_dir` — never commit this to git

---

### `docs/USB_INSTALLATION.md`

*(This is covered separately in p07_usb_install.md — this file will be created there)*

---

## After All Files Created

Verify:
- [ ] `docs/ARCHITECTURE.md` contains the full ASCII module diagram
- [ ] `docs/API_REFERENCE.md` documents all 18 functions
- [ ] `docs/SECURITY_MODEL.md` covers all 10 attacks in the table
- [ ] `docs/DEVELOPER_GUIDE.md` has runnable code examples

Confirm **Checkpoint 6 PASSED**.
