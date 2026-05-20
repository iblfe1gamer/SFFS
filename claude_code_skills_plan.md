# Claude Code — Skills Full-Coverage Testing Plan

> Feed this file to Claude Code with: `claude < claude_code_skills_plan.md`
> Or open a Claude Code session and paste each phase prompt one at a time.
> After every phase, confirm the checkpoint passes before moving on.

---

## Overview

```
Phase 0  →  Environment Check          [~5 min]
Phase 1  →  Install Built-in Skills    [~10 min]
Phase 2  →  Install Community Skills   [~20 min]
Phase 3  →  Functional Testing         [~30 min]
Phase 4  →  Edge-Case & Stress Tests   [~20 min]
Phase 5  →  Review & Audit             [~15 min]
Phase 6  →  Issue Resolution Plan      [~10 min]
```

---

## Phase 0 — Environment Check

Run these commands to confirm Claude Code is healthy before touching any skills.

```bash
# 1. Confirm Claude Code version
claude --version

# 2. Confirm Node.js ≥ 18 (required by Claude Code)
node --version

# 3. Confirm skills directory exists (create if missing)
mkdir -p ~/.claude/skills

# 4. List any skills already installed
ls ~/.claude/skills/ 2>/dev/null || echo "No personal skills installed yet"

# 5. List project-scoped skills (run inside your repo)
ls .claude/skills/ 2>/dev/null || echo "No project skills installed yet"

# 6. Open Claude Code and verify /skills command works
# Inside a session: /skills
```

### ✅ Checkpoint 0
- [ ] `claude --version` returns a version string
- [ ] Node.js ≥ 18 confirmed
- [ ] `~/.claude/skills/` directory exists
- [ ] `/skills` command lists available skills inside a session

---

## Phase 1 — Install Built-in / Bundled Skills

These ship with Claude Code and need no install — they just need to be verified.

Open a Claude Code session in any project, then run each command and confirm the output.

```
/help           → should list all available commands and bundled skills
/simplify       → should offer to simplify a code selection
/debug          → should launch the debug workflow
/loop           → should explain the loop agent skill
/batch          → should describe batch operation support
/claude-api     → should show Anthropic API usage skill
/deep-research  → bundled research skill (Explore agent fork)
```

### Manual verification prompts (paste into session):
```
Summarize the uncommitted changes in this repo.
Debug this error: TypeError: Cannot read properties of undefined
Simplify the following function: [paste any function]
```

### ✅ Checkpoint 1
- [ ] All bundled skills respond without error
- [ ] `/help` lists Skill entries in the Purpose column
- [ ] At least one bundled skill invoked successfully with real output

---

## Phase 2 — Install Community Skills

Run all of the following installation commands in your terminal (outside Claude Code).
After each group, restart Claude Code and confirm with `/skills`.

---

### 2A — Anthropic Official Skills (anthropics/skills repo)

```bash
# Clone official Anthropic skills
git clone https://github.com/anthropics/skills /tmp/anthropic-skills 2>/dev/null || true

# Install the original launch set
for skill in docx pdf pptx xlsx algorithmic-art canvas-design; do
  mkdir -p ~/.claude/skills/$skill
  cp -r /tmp/anthropic-skills/$skill/. ~/.claude/skills/$skill/ 2>/dev/null \
    || echo "Skill $skill not found in repo — skip"
done

echo "Anthropic official skills installed."
ls ~/.claude/skills/
```

---

### 2B — Agensi.io Marketplace (curl method)

```bash
# General-purpose skills via agensi.io
# Replace <slug> with each skill slug below — run one line per skill

mkdir -p ~/.claude/skills

# Code quality
mkdir -p ~/.claude/skills && curl -sL https://www.agensi.io/api/install/lint-and-validate | tar xz -C ~/.claude/skills/

# PR / commit helpers
curl -sL https://www.agensi.io/api/install/create-pr | tar xz -C ~/.claude/skills/
curl -sL https://www.agensi.io/api/install/commit-message | tar xz -C ~/.claude/skills/

# Documentation generator
curl -sL https://www.agensi.io/api/install/generate-docs | tar xz -C ~/.claude/skills/

# Test writer
curl -sL https://www.agensi.io/api/install/write-tests | tar xz -C ~/.claude/skills/

echo "Agensi skills installed."
ls ~/.claude/skills/
```

---

### 2C — Awesome Claude Skills (travisvn/awesome-claude-skills)

```bash
git clone https://github.com/travisvn/awesome-claude-skills /tmp/awesome-skills 2>/dev/null || true

# Browse the curated list in the README and manually copy skills you want:
# Example: context engineering skill by TÂCHES
mkdir -p ~/.claude/skills/taches-meta
cp -r /tmp/awesome-skills/taches-meta/. ~/.claude/skills/taches-meta/ 2>/dev/null \
  || echo "Copy manually from /tmp/awesome-skills"

echo "See /tmp/awesome-skills for full catalogue."
```

---

### 2D — Obra Superpowers (multi-agent workflow, 40k+ stars)

```bash
git clone https://github.com/obrasier/superpowers-for-claude /tmp/superpowers 2>/dev/null || true
mkdir -p ~/.claude/skills/superpowers
cp -r /tmp/superpowers/. ~/.claude/skills/superpowers/

echo "Superpowers installed. Invoke via /superpowers inside Claude Code."
```

---

### 2E — GStack by Garry Tan (AI engineering team framework)

```bash
git clone https://github.com/garrytan/gstack /tmp/gstack 2>/dev/null || true
mkdir -p ~/.claude/skills/gstack
cp -r /tmp/gstack/skills/. ~/.claude/skills/gstack/ 2>/dev/null \
  || echo "Check /tmp/gstack structure manually"

echo "GStack skills installed."
```

---

### 2F — Alirezarezvani community collection (245+ skills)

```bash
git clone https://github.com/alirezarezvani/claude-skills /tmp/ali-skills 2>/dev/null || true

# Install by domain — choose what's relevant to you:
# Engineering (24 core)
mkdir -p ~/.claude/skills/engineering
cp -r /tmp/ali-skills/engineering/. ~/.claude/skills/engineering/ 2>/dev/null || true

# Engineering advanced (25 powerful-tier)
mkdir -p ~/.claude/skills/engineering-advanced
cp -r /tmp/ali-skills/engineering-advanced/. ~/.claude/skills/engineering-advanced/ 2>/dev/null || true

# Product (12 skills)
mkdir -p ~/.claude/skills/product
cp -r /tmp/ali-skills/product/. ~/.claude/skills/product/ 2>/dev/null || true

echo "Ali collection installed."
```

---

### 2G — Plugin Marketplace (inside Claude Code session)

Open a Claude Code session, then:

```
/plugin
```

Navigate to **Discover**, install any skill you see, choosing scope:
- **User** → installs to `~/.claude/skills/` (all projects)
- **Project** → installs to `.claude/skills/` (this repo only)

### ✅ Checkpoint 2
- [ ] `ls ~/.claude/skills/` shows 8+ skill directories
- [ ] `/skills` inside Claude Code lists all installed skills
- [ ] No skill shows a parse error or missing SKILL.md on startup

---

## Phase 3 — Functional Testing

Open a Claude Code session inside a real project (or create a test repo).
Run each prompt exactly as written. Record pass/fail for each.

---

### 3A — Bundled Skills

| Test | Prompt to run | Expected result |
|------|---------------|-----------------|
| simplify | `/simplify` then paste a complex function | Simplified version returned |
| debug | `/debug` with a traceback | Hypothesis + fix suggested |
| batch | `/batch` then describe a multi-file task | Batch plan produced |
| loop | `/loop` + describe an iterative task | Loop agent kicked off |
| deep-research | `/deep-research What is the purpose of main.py?` | File references returned |
| claude-api | `/claude-api` | API usage guidance shown |

---

### 3B — Document Skills (docx / pdf / pptx / xlsx)

```
Create a Word document summarising this project's README.
Convert this markdown file to a PDF.
Build a three-slide PowerPoint overview of this codebase.
Export the test results from tests/ to a spreadsheet.
```

Expected: a file is created and offered as a download link.

---

### 3C — Code Quality Skills

```
Lint and validate every file in src/.
Write unit tests for the functions in utils.js.
Generate API documentation for all exported functions.
Create a pull request description for my current branch.
Write a conventional commit message for my staged changes.
```

---

### 3D — Engineering Skills (ali-skills collection)

```
/senior-architect Review the architecture of this project and identify improvements.
/code-review Review the last commit for bugs, security issues, and style.
/security-audit Scan this project for OWASP Top 10 vulnerabilities.
/performance-review Profile the hot paths in this codebase.
/refactor Refactor auth.js to use dependency injection.
```

---

### 3E — Multi-Agent Skills (Superpowers / GStack)

```
/superpowers I want to add a rate-limiting middleware to this Express app.
/office-hours Walk me through designing the database schema for a SaaS billing system.
/design-review Review the UI components in /components for accessibility and consistency.
/qa Run a structured QA review of the checkout flow.
```

---

### ✅ Checkpoint 3

For each test record: **PASS**, **FAIL**, or **SKIP** (if skill not installed).

| Skill | Result | Notes |
|-------|--------|-------|
| /simplify | | |
| /debug | | |
| /batch | | |
| /loop | | |
| /deep-research | | |
| docx | | |
| pdf | | |
| pptx | | |
| xlsx | | |
| lint-and-validate | | |
| write-tests | | |
| generate-docs | | |
| create-pr | | |
| commit-message | | |
| senior-architect | | |
| code-review | | |
| security-audit | | |
| superpowers | | |
| gstack | | |

---

## Phase 4 — Edge-Case & Stress Tests

These tests deliberately push skills into unusual conditions to surface hidden bugs.

```bash
# 4A — Empty repo (no files)
mkdir /tmp/empty-test && cd /tmp/empty-test && git init
claude
# Inside session:
/debug
/simplify
# Expected: graceful "nothing to analyse" message, not a crash

# 4B — Large file
dd if=/dev/urandom of=/tmp/large.txt bs=1M count=5 2>/dev/null
# Inside session:
# Ask Claude to summarise /tmp/large.txt
# Expected: summary produced or polite context-limit message

# 4C — Binary file
# Inside session:
# Ask Claude to lint an image file
# Expected: "not a source file" message, no crash

# 4D — Skill name collision (two skills with same /name)
mkdir -p ~/.claude/skills/duplicate-test/
echo "---
name: lint-and-validate
description: Duplicate skill test
---
# Duplicate" > ~/.claude/skills/duplicate-test/SKILL.md
# Inside session:
/skills
# Expected: conflict warning or one skill takes precedence — not silent failure

# 4E — Network-dependent skill offline
# Disconnect from the internet temporarily, then:
/deep-research fetch current Node.js LTS version
# Expected: graceful failure message, not a hang

# 4F — Skill with allowed-tools constraint
# Create a read-only skill and verify it cannot write files:
mkdir -p ~/.claude/skills/readonly-test
cat > ~/.claude/skills/readonly-test/SKILL.md << 'EOF'
---
name: readonly-test
description: Read-only exploration skill
allowed-tools: [Read, Glob, Grep]
---
Explore the codebase without writing anything.
EOF
# Inside session:
/readonly-test Try to create a file called test.txt
# Expected: tool denied, no file created
```

### ✅ Checkpoint 4
- [ ] Empty repo: no crash on any bundled skill
- [ ] Large file: handled gracefully
- [ ] Binary file: skill gives sensible refusal
- [ ] Duplicate skill names: warning surfaced, no silent fail
- [ ] Offline network skill: timeout handled gracefully
- [ ] allowed-tools restriction: write blocked as expected

---

## Phase 5 — Review & Audit

Run this full audit checklist after all tests. Document findings.

### 5A — Installation Integrity

```bash
# Check every skill has a valid SKILL.md
for d in ~/.claude/skills/*/; do
  if [ -f "$d/SKILL.md" ]; then
    echo "OK  $d"
  else
    echo "MISSING SKILL.md: $d"
  fi
done

# Check for skills that are too large (>1MB uncompressed)
du -sh ~/.claude/skills/*/ | sort -rh | head -20
```

### 5B — Security Review

For each installed skill, manually read its SKILL.md and check:

| Check | Description |
|-------|-------------|
| No hardcoded secrets | No API keys, tokens, or passwords embedded |
| No remote code execution | No `eval()`, `exec()`, or arbitrary shell from untrusted input |
| Trusted source | Skill comes from a known author / verified repo |
| Scoped tools | `allowed-tools` is as narrow as possible for the skill's purpose |
| No exfiltration paths | Skill does not silently POST data to external URLs |

Flag any skill that fails this check and **disable it immediately** with:
```bash
mv ~/.claude/skills/<skill-name> ~/.claude/skills/<skill-name>.disabled
```

### 5C — Performance Review

Inside a Claude Code session, time each skill invocation:
- Skills should load metadata in < 1 second (progressive disclosure: ~100 tokens)
- Full skill activation should add < 5k tokens to context
- Skills with bundled scripts should complete their task in < 30 seconds for normal inputs

Note any skill that is consistently slow and log it as an issue.

### 5D — Compatibility Matrix

| Skill | macOS | Linux | Windows (WSL) | Notes |
|-------|-------|-------|---------------|-------|
| docx | | | | Requires LibreOffice on Linux |
| pdf | | | | Requires poppler |
| pptx | | | | |
| superpowers | | | | Git worktrees required |
| security-audit | | | | Docker recommended |

Fill in PASS / FAIL / N/A after testing on your platform.

### ✅ Checkpoint 5
- [ ] All SKILL.md files present and parseable
- [ ] No skill failed the security checklist
- [ ] No skill >1MB (flag for review if so)
- [ ] Compatibility matrix filled for your platform

---

## Phase 6 — Issue Resolution Plan

After completing the audit, categorise every issue found using this template.

---

### Issue Log Template

For each issue discovered, fill in one entry:

```
ID:          ISSUE-001
Skill:       <skill name>
Phase found: <0-5>
Severity:    Critical / High / Medium / Low
Type:        Crash | Wrong output | Security | Performance | Missing feature | Compatibility
Description: <one paragraph>
Steps to reproduce:
  1. ...
  2. ...
Expected: ...
Actual:   ...
Fix plan: (see resolution tracks below)
Status:   Open / In Progress / Resolved
```

---

### Resolution Tracks

#### Track A — Skill not loading (SKILL.md missing or malformed)

```bash
# Regenerate a minimal SKILL.md for the broken skill
cat > ~/.claude/skills/<skill-name>/SKILL.md << 'EOF'
---
name: <skill-name>
description: <one sentence — Claude reads this to decide when to activate>
---
# <Skill Name>
<Paste the original instructions here, or write new ones>
EOF
```

#### Track B — Wrong output / skill misunderstood the task

1. Open `~/.claude/skills/<skill-name>/SKILL.md`
2. Add a `## Examples` section with 2–3 concrete worked examples
3. Tighten the `description:` frontmatter — it must unambiguously describe when to activate
4. Add a `## Out of scope` section listing tasks this skill should NOT handle
5. Re-run the failing test from Phase 3

#### Track C — Security concern

1. Disable the skill immediately: `mv ~/.claude/skills/<skill> ~/.claude/skills/<skill>.disabled`
2. Report to the skill's GitHub repo as an issue
3. If the skill is from the official Anthropic repo, file a report at https://www.anthropic.com/security
4. Do not re-enable until the upstream issue is resolved and you have reviewed the fix

#### Track D — Performance (skill too slow)

1. Check if the skill bundles large resources in `resources/` — move large assets to remote URLs and lazy-load them
2. Split a monolithic SKILL.md into a lean trigger + a detailed procedure that loads on demand
3. If the skill calls an external API, add a timeout: `await Promise.race([fetch(...), timeout(10_000)])`
4. Target: total skill activation < 5k tokens

#### Track E — Platform compatibility

1. Identify the platform-specific dependency (e.g. LibreOffice, poppler, Docker)
2. Add an install check at the top of the skill's script:
   ```python
   import shutil, sys
   if not shutil.which("libreoffice"):
       print("ERROR: LibreOffice not found. Install with: sudo apt install libreoffice")
       sys.exit(1)
   ```
3. Add a `## Requirements` section to SKILL.md listing OS dependencies with install commands
4. If the skill cannot be made cross-platform, add `platform: linux` to the frontmatter and document it

#### Track F — Skill name collision

1. Pick the skill you want to keep
2. Rename the duplicate's `name:` frontmatter field to `<original-name>-v2` or `<author>-<name>`
3. Restart Claude Code to reload
4. Verify `/skills` no longer shows a conflict

---

### Priority Resolution Order

1. **Critical / Security** — fix before starting any work session
2. **Crash bugs** — fix before relying on the skill
3. **Wrong output (High)** — fix within the same day
4. **Performance** — fix when it noticeably slows your workflow
5. **Compatibility** — document and fix opportunistically
6. **Low severity** — backlog, address in batches

---

## Final Verification

After all issues are resolved, run this complete sign-off sequence:

```bash
# 1. Confirm all skills load cleanly
claude --print "/skills"

# 2. Re-run the Phase 3 test table and confirm all were PASS

# 3. Re-run Phase 4 edge cases and confirm no regressions

# 4. Count installed skills
ls ~/.claude/skills/ | wc -l

# 5. Archive this plan with results
cp claude_code_skills_plan.md claude_code_skills_plan_COMPLETED_$(date +%Y%m%d).md
```

Expected final state:
```
✅ Built-in skills: 6/6 passing
✅ Community skills: all installed skills passing
✅ Edge cases: 6/6 handled gracefully
✅ Security: 0 flagged skills enabled
✅ Performance: all skills < 5k tokens, < 30s per task
✅ Platform: compatibility matrix complete
```

---

## Appendix — Quick Reference

### Skill directory locations
| Scope | Path |
|-------|------|
| Personal (all projects) | `~/.claude/skills/<skill-name>/SKILL.md` |
| Project (this repo) | `.claude/skills/<skill-name>/SKILL.md` |

### Useful Claude Code session commands
| Command | Purpose |
|---------|---------|
| `/skills` | List all loaded skills |
| `/plugin` | Open plugin browser |
| `/help` | All commands + skills |
| `/<skill-name>` | Invoke a skill directly |
| `/compact` | Compact context (save tokens) |

### Community skill directories
| Source | URL |
|--------|-----|
| Anthropic official | https://github.com/anthropics/skills |
| Awesome list | https://github.com/travisvn/awesome-claude-skills |
| Obra Superpowers | https://github.com/obrasier/superpowers-for-claude |
| Ali collection | https://github.com/alirezarezvani/claude-skills |
| Agensi marketplace | https://www.agensi.io |
| skills.sh directory | https://skills.sh |
| aitmpl catalogue | https://www.aitmpl.com/skills/ |

### Security reminder
> ⚠️ Skills can execute arbitrary code in Claude's environment.
> Only install skills from trusted sources.
> Always read SKILL.md and any scripts/ before enabling.
