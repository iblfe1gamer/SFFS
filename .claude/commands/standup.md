Generate today's standup update for the SFFS project.

1. Check `git log --since="24 hours ago" --oneline` for recent commits
2. Note which student modules (code1/code2/code3/main-code/tests) were touched
3. Check for any open test failures: run `pytest tests -q --tb=no` and note status
4. Format as:
   - Done: [list completed items]
   - Doing: [current work in progress]
   - Blockers: [anything blocking progress]
5. Keep under 5 bullet points total. Note which student(s) contributed.
