Full SFFS security and quality audit. Run in order:

1. Security sweep — check for:
   - Hardcoded keys/passwords/tokens in code1/, code2/, code3/, main-code/
   - SQL injection or shell injection risks
   - Insecure crypto usage (MD5, SHA1 for passwords, ECB mode)
   - Secrets in git history: `git log --all --full-diff -S "password" --oneline`
   - OWASP Top 10 relevant to file encryption + auth systems

2. Dependency audit:
   - `pip-audit -r requirements.txt` (install pip-audit if missing: `pip install pip-audit`)

3. Dead code detection — identify unused functions in code1/–code3/ that are never imported

4. Test coverage gaps — which functions in f01–f18 lack test coverage in tests/

5. Output prioritized findings: CRITICAL / HIGH / MEDIUM / LOW
