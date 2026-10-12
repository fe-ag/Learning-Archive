# Learning Archive – Education Publication Site

A Django website for an education-focused publication archive. Visitors browse
articles, papers and learning resources by category. A custom management area
(built with ordinary Django views, templates and forms – **Django Admin is not
installed**) lets the team add titles, assign categories, edit metadata and
publish content without touching code.

> **Status of this delivery – please read.**
> This code was written in an environment that had no Django installation and
> no internet access. It was syntax-checked (`python -m py_compile`) and the
> template tags were checked for balance, but **`manage.py check`, `migrate`
> and the test suite have not been run**. Run the commands in section 8 first
> and fix anything they report before deploying. The migration file was
> written by hand; if `python manage.py makemigrations --check` reports
> changes, run `makemigrations` and commit the result.

## 1. Features

Public site
- Home page with search, featured items, category index and latest additions
- Archive listing with keyword search (title, summary, authors, body), filters
  (category, type), sorting and pagination
- Category pages, publication detail pages with file download and/or link to the source
- Simple pages (About, Contact …) editable from the management area
- SEO: unique titles and descriptions, canonical URLs, Open Graph tags,
  `sitemap.xml`, `robots.txt`, semantic HTML, mobile-first responsive layout
- Custom 403, 404 and 500 pages

Management area (`/manage/`)
- Staff-only sign-in, sign-out, dashboard with counts and recent edits
- Create, edit, delete and search publications, categories and pages
- Publish / unpublish with one click, scheduled publishing (future date)
- File upload with type and size validation (default 20 MB)
- Success and error messages, form validation, server-side permission checks
- Categories that still contain publications cannot be deleted

Not included (not in the project brief): shop, cart, payments, user
registration for visitors, comments, newsletter.

## 2. Requirements

- Python 3.11 or newer
- PostgreSQL 14 or newer (SQLite works for a quick local try-out only)
- Packages in `requirements.txt` (Django 5.2 LTS, psycopg 3, WhiteNoise, Gunicorn, python-dotenv).
  Version ranges are used because exact pins could not be verified offline; run
  `pip freeze > requirements.lock` after your first successful install if you want exact pins.

## 3. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 4. Configure PostgreSQL

```sql
CREATE USER publication_user WITH PASSWORD 'choose-a-strong-password';
CREATE DATABASE publication_site OWNER publication_user;
```

## 5. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`. At minimum set `DJANGO_SECRET_KEY`, the `POSTGRES_*` values and,
in production, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS` and
`DJANGO_CSRF_TRUSTED_ORIGINS`. The file is read from the project root;
real environment variables also work. Never commit `.env`.

For a quick try-out without PostgreSQL set `DB_ENGINE=sqlite`.

## 6. Migrate, create the first manager, run

```bash
python manage.py migrate
python manage.py createsuperuser        # this account is also a staff account
python manage.py seed_demo              # optional: sample categories, items and an About page
python manage.py runserver
```

- Public site: http://127.0.0.1:8000/
- Management sign-in: http://127.0.0.1:8000/manage/login/
- Other managers: create users with `createsuperuser`, or in `python manage.py shell`
  create a user with `is_staff=True`. Only accounts with `is_staff` can enter `/manage/`.

## 7. Production deployment

```bash
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

- Static files are served by WhiteNoise from `staticfiles/`.
- **Uploaded files** live in `media/` and are **not** served by Django when
  `DJANGO_DEBUG=False`. Configure your web server to serve `/media/` from the
  `media/` directory (for example an Nginx `location /media/ { alias /path/to/media/; }`).
- Serve the site over HTTPS, then set `SECURE_SSL_REDIRECT=True`, a non-zero
  `SECURE_HSTS_SECONDS` and, behind a reverse proxy that sets
  `X-Forwarded-Proto`, `DJANGO_BEHIND_PROXY=True`.
- Back up the PostgreSQL database and the `media/` directory.

## 8. Run the checks and tests

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

PostgreSQL users need the `CREATEDB` privilege so Django can create a test
database (`ALTER USER publication_user CREATEDB;`). The tests cover routing,
authentication, staff-only access, CSRF, create/edit/delete for all content
types, validation, uploads, search, filters, sorting, pagination, scheduling,
sitemap and robots.txt.

## 9. Routine tasks for editors

1. Sign in at `/manage/login/`.
2. **Categories → New category** before adding publications.
3. **Publications → New publication**: choose type and category, write a
   summary, then add body text, upload a file, or link to the source.
4. Set **Status** to Published (leave the date blank to publish now, or pick a
   future date to schedule).
5. **Pages** edits the About page and similar content. Tick “Show in menu” to link it in the header.
6. Body text is plain text: a blank line starts a new paragraph. HTML is escaped on purpose.

## 10. Project layout

```
config/          settings, URLs, WSGI/ASGI
publications/    models, public views, sitemap, seed_demo command, tests
dashboard/       custom management area (views, forms, URLs, tests)
templates/       public site, management area, shared partials
static/          CSS and a small menu script
```

## 11. External services

None are required. No email, payment or third-party API is used.

## 12. Known limitations

- Not yet executed or tested by the author’s tooling (see the note at the top).
- No login rate limiting. Put the site behind a reverse proxy rate limit or add
  a package such as `django-axes` if the sign-in page is exposed publicly.
- Files in `media/` are public if the URL is known, including attachments of
  draft items. Do not upload confidential files.
- Body text has no rich-text editor or inline images by design (safe plain text).
- Search uses simple case-insensitive matching, not full-text ranking.
- The interface is English only.
- There is no preview mode: drafts and hidden pages are visible only in the management lists, not on the public site.
