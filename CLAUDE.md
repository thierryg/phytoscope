# CLAUDE.md

Ce projet suit `AGENTS.md`, qui vaut pour tous les agents — Claude Code compris.

**Lisez `AGENTS.md` d'abord.** Il renvoie, dans l'ordre, au cahier des charges
(`constraints.md`), à l'état du travail (`.ai/etat.md`), au journal des
interventions (`.ai/journal.md`) et aux décisions de conception
(`.ai/decisions.md`).

Rappels qui coûtent cher quand on les oublie :

- tout est **en français**, code et commentaires compris ;
- **ne jamais** lancer le logiciel sur la configuration réelle de l'utilisateur
  (`~/.config/phytoscope/`) : passer par `XDG_CONFIG_HOME` vers un dossier
  temporaire ;
- vérifier avant d'affirmer : `cd src/phytoscope && make test` ;
- consigner l'intervention dans `.ai/journal.md` avant de conclure.
