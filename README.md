my.ortoloco.ch
==============
This was the original starting point of [juntagrico](https://juntagrico.org). Now it's just home of the instance [my.ortoloco.ch](https://my.ortoloco.ch) and development is happening over here: [github.com/juntagrico/juntagrico](https://github.com/juntagrico/juntagrico)

Development setup
-----------------
Python 3.12 and PostgreSQL (production) or sqlite (default without database settings).

    python3.12 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    source myenv.txt  # environment variables, see below. myenv.txt is not committed
    python manage.py migrate
    python manage.py runserver

`juntagrico` is installed in the version required by `juntagrico-billing@releases/2.1` (a git branch), not from PyPI.

Environment variables
---------------------
| Variable | Purpose |
|---|---|
| `JUNTAGRICO_SECRET_KEY` | Django secret key |
| `JUNTAGRICO_DEBUG` | `True` or `False`. **Defaults to `True`**: must be `False` in production |
| `JUNTAGRICO_DATABASE_ENGINE`, `_NAME`, `_USER`, `_PASSWORD`, `_HOST`, `_PORT` | database, sqlite `ortoloco.db` if not set |
| `JUNTAGRICO_EMAIL_HOST`, `_PORT`, `_USER`, `_PASSWORD`, `_TLS`, `_SSL` | SMTP server |
| `JUNTAGRICO_EMAIL_WHITELISTED1`, `…2`, … | with `DEBUG`, emails are only sent to these addresses (and `JUNTAGRICO_EMAIL_USER`) |
| `JUNTAGRICO_ADMIN_EMAIL`, `JUNTAGRICO_DS_EMAIL` | receive error reports (`ADMINS`) |
| `JUNTAGRICO_STAGING` | `1` on the staging instance: no emails, staging styles |
| `DEBUG_TOOLBAR` | `True` shows the django-debug-toolbar to superusers |
| `ORTOLOCO_OIDC_RSA_PRIVATE_KEY` | signs the logins of WordPress (OpenID Connect), see [docs/login-clients.md](docs/login-clients.md). Without it, OpenID Connect under `/o/` is disabled |
| `ORTOLOCO_VELO_CODE` | bike lock code shown in the user menu to members with an active subscription |
| `WP_USER`, `WP_PASSWORD` | access to news.ortoloco.ch (news embedding, currently disabled) |

Scheduled jobs
--------------
Crontab on the server (2026-11):

    45 23 * * * docker exec ortoloco python -m manage generate_depot_list
    */10 * * * * docker exec ortoloco python manage.py remind_members
    0 8 * * *  docker exec ortoloco python manage.py upcoming_jobs

- `generate_depot_list` (juntagrico): runs every night, but creates the depot lists only on the days of
  `DEPOT_LIST_GENERATION_DAYS` (`[3]`: Thursday, for the deliveries of the next week) and notifies the admins.
- `remind_members` (juntagrico): reminds members of their jobs in the next 48 hours, each reminder only once.
- `upcoming_jobs` (ortoloco): emails the jobs and participants in N days to the coordinators of the areas in
  `ORTOLOCO_AREA_NOTIFY` (`Verteilen`: 2 days). Every call sends the emails again, so run it only once a day.

Deployment
----------
1. backup the database
2. `pip install -r requirements.txt`
3. `python manage.py migrate`
4. `python manage.py collectstatic`

Once per server: the signing key for OpenID Connect, see [docs/login-clients.md](docs/login-clients.md).

Yearly maintenance
------------------
- `ORTOLOCO_RECURRING_MESSAGES` (settings.py): the depot list messages with and without tofu are defined per year.
  Add the next year until December 1st, `ortoloco/tests/test_settings.py` fails from then on otherwise.
- When subscription types, products, tours or depots change: `python manage.py export_test_config`
  on a copy of the production database, to keep the test data up to date.

Depot lists and the garden computer
-----------------------------------
The lists are configured in `DEPOT_LISTS` with ortoloco's templates in `ortoloco/templates/exports_oooo`.
"Listen Drucken.bat" on the garden computer logs in and downloads `https://my.ortoloco.ch/list/<name>`
(`depotlist`, `amountoverview`, `depotoverview`, `touroverview`) to print them: the keys of `DEPOT_LISTS`
must not change. `ortoloco/tests/test_print_script.py` replays the script.

Impersonation
-------------
Only members of the group `impersonators` may impersonate (django-impersonate, `IMPERSONATE` in settings.py).
Superusers may impersonate everybody, all others only users without staff status, groups, permissions
or coordinated areas. In the admin (`/admin/`) only superusers impersonate, everybody else stays themselves
(`ortoloco.middleware.AdminImpersonateMiddleware`). Superusers also need the group `impersonators`.

Login of other services
-----------------------
Nextcloud (OAuth2) and the WordPress instances (OpenID Connect) log in with my.ortoloco,
see [docs/login-clients.md](docs/login-clients.md), also for adding new clients.

Tests
-----
The tests run on an in-memory sqlite database, no setup needed:

    python manage.py test ortoloco --settings=ortoloco.settings_test

To test against the PostgreSQL database configured with the `JUNTAGRICO_DATABASE_*` environment variables
(like production and the GitHub workflow), set `ORTOLOCO_TEST_DATABASE=env`.

The test data comes from juntagrico (`juntagrico.tests.JuntagricoTestCase`: members, permissions, jobs and special
cases). `ortoloco.tests.OrtolocoTestCase` adds ortoloco's world:

- `ortoloco/fixtures/ortoloco_config.json`: the real subscription types, products, tours and depots with their ids,
  only public configuration (no members, subscriptions, contacts, descriptions or access information of depots).
  Refresh it from a copy of the production database with `python manage.py export_test_config`.
- synthetic members with subscriptions in these depots (`ORTOLOCO_SUBSCRIPTIONS`), so the depot lists show
  realistic numbers for Tuesday and Thursday,
- the area of the cron notification, the tofu messages of the depot lists and the account of the print script
  on the garden computer.

`ortoloco/tests/test_overrides.py` guards the template overrides against juntagrico releases: it fails if an override
uses a removed tag or filter, overrides a block that no longer exists, or if juntagrico changed a template that ortoloco
replaces completely (`REPLACED_UPSTREAM`). The GitHub workflow additionally runs the tests weekly against juntagrico `main`.
