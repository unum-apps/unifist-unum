# Changelog

## 0.1.0

- The Unifist Unum app: an API and a GUI over the six tables everything else uses, `Sequence`, `Slug` and `Journal` (relations-unifist) and `Route`, `Scribe` and `Clash` (relations-unum).
- The API owns and migrates those tables, and serves them under `/model`.
- Create a `Route` through the API or the GUI and it works.
- Images are on Python 3.13 and Debian, not Alpine: `python:3.13` for the API, `nginx:1.28` for the GUI. `cryptography` is a requirement instead of coming from a special base image.
- `Route`, `Scribe` and `Clash` live in the `unum` schema (relations-unum 0.4.2, relations-unifist 0.4.1, relations-dil 0.7.0), the others in `unifist`.
- Dependencies are brought up to date, with `debugpy` in place of `ptvsd`.
- Other apps can install the interface, `unifist_unum`, from a tagged version of this repo (`setup.py` and `make setup`; Jenkins runs `make setup` on every build and, on main, tags the version with `make tag`, which does nothing if the tag is already there), as the ledger does (unum-apps/unifist-unum#6).
