# Learning Archive

A small Django site for publishing articles, papers and learning resources, with a management panel that a non-technical team can use.

I built this as a sample project for an education-publication brief: visitors browse content by category, and the people running the site add, edit and publish everything from a simple panel, without touching code.

It's a prototype. It runs, and I've used it locally, but it hasn't been deployed anywhere or load-tested, so treat it as a solid starting point rather than a finished product.

## What it does

**For visitors**

- Home page with a search box, featured items, a category index and the latest additions
- A browse page with keyword search, filters (category and type), sorting and pagination
- Category pages and detail pages, with a download button and/or a link to the original source
- Simple pages such as About or Contact
- Basics for search engines: page titles and descriptions, canonical tags, a sitemap and a robots.txt

**For the team (at `/manage/`)**

- Staff-only sign-in
- A dashboard with counts and recently edited items
- Create, edit, search and delete publications, categories and pages
- Draft or published status, with a future date if you want to schedule something
- File uploads (PDF, Word, PowerPoint, Excel, EPUB, text, ZIP) with type and size checks

The management panel is built from ordinary Django views, forms and templates. I deliberately didn't use Django Admin, and it isn't installed.

## Tech

Python, Django 5.2, PostgreSQL (SQLite works for trying it out), plain HTML/CSS with a tiny bit of JavaScript for the mobile menu. WhiteNoise serves static files, Gunicorn is included for production.

## Running it locally

You need Python 3.11 or newer.

```bash
git clone https://github.com/fe-ag/Learning-Archive.git
cd Learning-Archive

python -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env             # on Windows PowerShell: Copy-Item .env.example .env
```

Open `.env`. If you just want to look around and don't have PostgreSQL, change this one line:

```
DB_ENGINE=sqlite
```

Then:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo       # optional: fills the site with fictional sample content
python manage.py runserver
```

- The site is at http://127.0.0.1:8000/
- The management panel is at http://127.0.0.1:8000/manage/login/. Sign in with the account you just created.

`seed_demo` adds eight categories, a few dozen publications (including a couple of drafts and one scheduled item) and some pages, so every part of the site has something to show. All of it is made up. You can run the command more than once without creating duplicates.

## Using PostgreSQL

Create a database and a user, then fill in the `POSTGRES_*` values in `.env`:

```sql
CREATE USER publication_user WITH PASSWORD 'pick-a-strong-password';
CREATE DATABASE publication_site OWNER publication_user;
```

## Everyday use

1. Sign in at `/manage/login/`.
2. Add a category first (**Categories → New category**).
3. Add a publication: pick a type and category, write a short summary, then add some text, upload a file, or link to the source.
4. Set the status to Published. Leave the date empty to publish right away, or choose a future date to schedule it.
5. Use **Pages** to edit things like About. Tick "Show in menu" to put a page in the header.

The body text is plain text: a blank line starts a new paragraph. I kept it plain on purpose, so nobody can paste something unsafe into a page.

## Tests

There's a test suite for the public pages, sign-in, permissions, CSRF, the management forms, uploads, search, filters, pagination and the sitemap:

```bash
python manage.py check
python manage.py test
```

With PostgreSQL, Django needs permission to create a temporary test database (`ALTER USER publication_user CREATEDB;`).

## Putting it online

```bash
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

A few things to set up:

- In `.env`, set `DJANGO_DEBUG=False`, a real `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS`.
- Django doesn't serve uploaded files when debug is off. Point your web server (Nginx, for example) at the `media/` folder under `/media/`.
- Once you're on HTTPS, turn on `SECURE_SSL_REDIRECT` and set `SECURE_HSTS_SECONDS`. If a reverse proxy handles HTTPS, set `DJANGO_BEHIND_PROXY=True`.
- Back up the database and the `media/` folder.

Django needs Python support on the host, so plain shared PHP hosting won't work. A small VPS or any host that runs Python apps will.

## Project layout

```
config/          settings and URLs
publications/    models, public views, sitemap, the seed_demo command
dashboard/       the management panel
templates/       public and management templates
static/          CSS and the menu script
```

## Things to know

- There's no rate limiting on the sign-in page. If the site is public, put a limit in front of it or add something like `django-axes`.
- Uploaded files are reachable by anyone who knows the URL, including files attached to drafts. Don't upload anything confidential.
- There's no rich-text editor and no images inside articles. That was a choice, not an oversight, but it's the first thing I'd add for a real client.
- There's no preview mode: drafts only show up in the management panel.
- Search is simple case-insensitive matching, not ranked full-text search.
- The interface is English only.
- The home page text itself lives in a template. Pages like About are editable from the panel, but the home page headline isn't yet.

## Contact

Mahdi, [github.com/fe-ag](https://github.com/fe-ag)