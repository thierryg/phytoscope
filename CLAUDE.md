# CLAUDE.md

This project follows `AGENTS.md`, which applies to every agent — Claude Code
included.

**Read `AGENTS.md` first.** It points, in order, to the requirements
(`constraints.md`), the state of the work (`.ai/etat.md`), the intervention log
(`.ai/journal.md`), and the design decisions (`.ai/decisions.md`).

Reminders that cost real time when they are forgotten:

- everything is written in **technical US English** — code, comments,
  docstrings, documentation, file names, and directory names. This reverses the
  earlier French-only rule, which was dropped on 2026-09-22; never reintroduce
  French into code or documentation;
- **never** run the software against the user's real configuration
  (`~/.config/phytoscope/`): point `XDG_CONFIG_HOME` at a temporary directory
  instead;
- measure before you claim: `cd src/phytoscope && make test`;
- record what you did in `.ai/journal.md` before you call it done.
