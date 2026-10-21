# Contributing

Thanks for helping! KeyGlow is young, so the most useful contributions right now are:

1. **Keyboard reports.** Try KeyGlow with your keyboard and open an issue saying what works
   and what doesn't. Include the output of `keyglow probe` and the keyboard name OpenRGB shows.
2. **Profiles.** Share profiles you made (plain `.json`). Only submit work that is yours or
   that has a license allowing redistribution, and credit the source.
3. **Code.** Bug fixes, importers for more formats, new effects.

## Development setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[app,hid,dev]"
pytest
keyglow-app        # run the desktop app from source
```

## Repository layout

```
keyglow/            the Python package
  app/              desktop app: local web server, light engine, games, UI (static/)
  backends/         hardware and preview outputs (OpenRGB, terminal/HTML, USB probe)
  formats/          other programs' formats (OpenRGB profiles)
  presets/          built-in profiles
  community/        built-in gallery; themes/ is generated, with its credits
docs/               documentation and screenshots
examples/           example profiles for the command line
tools/              build script and generators (icon, theme profiles)
tests/              pytest
```

## Guidelines

- Profiles are data, never code. Don't add anything that executes downloaded content.
- Keep the app working without optional dependencies where possible (the core library has none).
- Add a test for new behavior; run `pytest` before opening a pull request.
- User-facing text (UI, CLI, docs) is in English. Some code comments are still in Spanish;
  translating them is welcome.
