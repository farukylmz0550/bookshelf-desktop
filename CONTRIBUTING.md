# Contributing

Contributions are welcome. Please keep a few rules in mind:

1. **One file, one job.** Every module has a single responsibility; keep it that way.
2. **English only.** Code, comments, commits, and documentation are English. Translations live in `assets/lang/*.json`.
3. **No GUI in the core.** `core/`, `services/`, and `shared/` must not import GTK. All UI code lives in `ui/`.
4. **Test what is testable.** Anything in `core/` or `shared/` gets unit tests (`python3 -m pytest`).
5. **Format.** Keep the existing style; a quick `ruff check src` is enough.

## Reporting bugs

Open an issue with the steps to reproduce and the log file (`katipcelebi.log` inside your library folder).
