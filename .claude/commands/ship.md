Full ship sequence for the current feature branch.

1. Run `pytest tests -q --tb=short` — stop and report if anything fails
2. Run `python sffs_usb_setup.py --verify` — stop if USB verify fails
3. Check for hardcoded secrets or keys in changed files (grep for API_KEY, password=, SECRET)
4. Check no writes to sffs_data/, security/, .env* were made
5. Create PR using /pr command
6. Summarize: what was shipped, which student module(s), what's left
