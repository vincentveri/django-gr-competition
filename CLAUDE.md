# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Django web application for managing Rhythmic Gymnastics (Ginnastica Ritmica) competitions. Handles athletes, clubs (societies), categories, and competitions. All model/field names and UI copy are in Italian.

## Commands

```bash
# Activate virtual environment (Windows)
.venv\Scripts\activate

# Run development server
python manage.py runserver

# Apply migrations
python manage.py migrate

# Create and apply new migrations after model changes
python manage.py makemigrations
python manage.py migrate

# Frontend (Tailwind + webpack) - run after `npm install`
npm run build   # production build -> static/dist/
npm run dev     # rebuild on change

# Run tests
python manage.py test

# Run tests for a single app
python manage.py test anagrafiche
python manage.py test competizioni

# Open Django shell
python manage.py shell
```

## Architecture

Two Django apps under the project config in `core/`:

- **`anagrafiche/`** — the active app. Manages registries: societies (`Societa`), athletes (`Atleta`), categories (`Categoria`), bands (`Fascia`), levels (`Livello`), equipment (`Attrezzo`), and competitions (`Competizione`).
- **`competizioni/`** — stub app, no models or views yet. Intended to handle competition-specific workflows.

Root URLs (`core/urls.py`) mount `anagrafiche.urls` at `/`.

Templates live in `templates/` (project-level), not inside app directories. The base template (`templates/base.html`) uses **Tailwind CSS v4** (built with webpack, see Frontend below).

Views are function-based. No class-based views or REST API — this is a server-rendered Django app only.

## Frontend

- Sources in `frontend/src/` (`main.css` = Tailwind + theme, `index.js` = entry: theme toggle and mobile sidebar). Webpack (`webpack.config.js`, `postcss.config.js`) outputs `static/dist/main.css` and `main.js`, which `base.html` loads. `static/dist/` and `node_modules/` are git-ignored: run `npm run build` before serving.
- Tailwind scans `templates/` for classes (`@source` in `main.css`), so rebuild after adding new classes.
- **Palette is fixed** (documented at the top of `main.css`): Tailwind's default colors are removed; use only semantic utilities `primary`, `on-primary`, `background`, `surface`, `line`, `text`, `muted`, `success`, `warning`, `danger`. Never use raw hex or other Tailwind colors. Reusable component classes: `.box`, `.label`, `.input`, `.btn`, `.menu-label`, `.menu-link`.
- Dark mode: `<html data-theme="light|dark">`, set before paint by an inline script in `base.html` and persisted in `localStorage`. Palette variables (`--gr-*`) swap per theme, so components need no `dark:` variants.
- Font: Inter (Google Fonts), root font size 14px. Layout: top navbar + left sidebar from the `md` breakpoint (768px), burger menu below.
- Forms use Django `ModelForm`s (`anagrafiche/forms.py`), rendered via the `anagrafiche/_field.html` include.

## Key Models (`anagrafiche/models.py`)

- `Societa` — club/society with address, contact info, and fiscal codes
- `Atleta` — athlete with `ForeignKey` to `Societa`, `Categoria`, `Fascia`, `Livello` (all nullable, `SET_NULL` on delete)
- `Competizione` — standalone competition with date ranges (registration, event, payment deadline) and address
- `Categoria`, `Fascia`, `Livello`, `Attrezzo` — lookup/reference tables, each with just a `nome` field

## Database

PostgreSQL. Credentials loaded from `.env` via `python-dotenv`. The `.env` file must exist at the project root with `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` set.

## Dependencies

Managed via `requirements.txt`. Key packages: Django 5.2, psycopg2-binary, python-dotenv, dj-database-url. Frontend (`package.json`): webpack, tailwindcss, @tailwindcss/postcss.
