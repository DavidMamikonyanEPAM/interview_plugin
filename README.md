# interview plugin

Mock front-end interview for interns, run entirely in the terminal inside Claude Code / CodeMie Claude Code.

## Use

```
/interview            # shows the topic menu
/interview React, CSS # preselect topics
```

Flow: choose topics (and optionally difficulty) → answer questions one by one → get `interview-report-<name>-<date>.md` in the current folder with each answer, the best answer, a 0-3 score and feedback.

## Install (for interns)

Inside Claude Code / CodeMie Claude Code:

```
/plugin marketplace add <repo-url>
/plugin install interview@interview-tools
```

Then run `/interview`. To get new versions later: `/plugin marketplace update interview-tools`.

Requires `python3` (standard library only, no packages to install).

## Install (local test)

```
claude --plugin-dir /path/to/interview-plugin
```

## Note

`data/question-bank.xlsx` is based on internal EPAM KB content. Keep the repository private or internal.

## Updating questions

Replace `data/question-bank.xlsx` with a new version. Keep the `Question Bank` sheet and these columns: ID, Skill, Topic, Type, Difficulty, Question, Expected answer / key points, Follow-up. New skills appear in the menu automatically.

To test with another file without replacing it: `INTERVIEW_QUESTION_BANK=/path/file.xlsx`.

## Scripts

`scripts/question_bank.py` has three commands: `skills`, `questions --skills A,B [--difficulty Basic,Core]`, `answers --ids Q001,Q002`. Expected answers are only fetched after the interview ends so the intern never sees them early.
