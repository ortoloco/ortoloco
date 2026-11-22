my.ortoloco.ch
==============
This was the original starting point of [juntagrico](https://juntagrico.org). Now it's just home of the instance [my.ortoloco.ch](https://my.ortoloco.ch) and development is happening over here: [github.com/juntagrico/juntagrico](https://github.com/juntagrico/juntagrico)

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
