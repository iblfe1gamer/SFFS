Create a pull request for the current branch.

1. Run `git diff main` and summarize all changes across code1/, code2/, code3/, main-code/, tests/
2. Generate a conventional commit PR title (feat/fix/chore/docs/refactor)
3. Write a description with: summary of changes, which student module(s) affected, testing done, any breaking changes or migration notes
4. Check if any security-sensitive files (sffs_data/, security/, .env) were modified — flag if so
5. Use `gh pr create` to create the PR and output the link
