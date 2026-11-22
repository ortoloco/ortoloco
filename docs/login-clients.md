# Login of other services with my.ortoloco

my.ortoloco is the login for other ortoloco services:

| Service | Protocol | Library | Endpoints |
|---|---|---|---|
| Nextcloud cloud.ortoloco.ch | OAuth2 | django-oauth-toolkit | `/o/…`, `/nextcloud/profile/` |
| WordPress instances | OpenID Connect | django-oidc-provider | `/openid/…` |

The flows are tested as the services run them in `ortoloco/tests/test_login_clients.py`.
Clients are configured in the database (Django admin), not in the code. Client secrets are never committed.

## Nextcloud (OAuth2)

Nextcloud uses the app *Social Login* with a custom OAuth2 provider `my.ortoloco`. After the login it reads
`https://my.ortoloco.ch/nextcloud/profile/` (`ortoloco/views.py`):

```json
{"id": 123, "email": "…", "firstName": "…", "lastName": "…", "displayName": "… …", "roles": ["Gruppe", "…"]}
```

`roles` are the Django groups of the user. Nextcloud maps them to its groups.

### Application in the admin

*Django OAuth Toolkit → Applications* (`/admin/oauth2_provider/application/`), one application `nextcloud`:

| Field | Value |
|---|---|
| Name | `nextcloud` |
| Client id | generated, enter in Nextcloud |
| User | admin |
| Redirect uris | `https://cloud.ortoloco.ch/index.php/apps/sociallogin/custom_oauth2/my.ortoloco`<br>`https://cloud.ortoloco.ch/apps/sociallogin/custom_oauth2/my.ortoloco` |
| Client type | Confidential |
| Authorization grant type | Authorization code |
| Client secret | generated, **copy it before saving**: it is hashed on save and cannot be shown again |
| Hash client secret | yes |
| Skip authorization | yes (no consent page) |
| Algorithm | No OIDC support |

### Endpoints for Nextcloud

| | |
|---|---|
| Authorize url | `https://my.ortoloco.ch/o/authorize/` |
| Token url | `https://my.ortoloco.ch/o/token/` |
| User info / profile url | `https://my.ortoloco.ch/nextcloud/profile/` |
| Scope | `nextcloud` |
| Groups | field `roles` |

### Settings this depends on (`ortoloco/settings.py`)

- `OAUTH2_PROVIDER['SCOPES']` contains `nextcloud`.
- `OAUTH2_PROVIDER['PKCE_REQUIRED'] = False`: Social Login sends no PKCE `code_challenge`. Since
  django-oauth-toolkit 2.0 PKCE is required by default, without this setting nobody can log in to Nextcloud.
- `oauth2_provider.middleware.OAuth2TokenMiddleware` and `oauth2_provider.backends.OAuth2Backend` authenticate the
  profile request with the access token. `ortoloco.auth.SafeAuthenticateWithEmail` keeps this working with users
  without member (production error 2026-11, fixed in juntagrico 2.1.1).

Note: `/nextcloud/profile/` accepts any valid access token or browser session, it does not check the scope.

## WordPress (OpenID Connect)

### Once per server

django-oidc-provider signs the ID tokens with an RSA key, created once with

    python manage.py creatersakey

### Add a client for a new WordPress instance

*OpenID Connect Provider → Clients* (`/admin/oidc_provider/client/`), add:

| Field | Value |
|---|---|
| Name | the instance, e.g. `wpxyz` |
| Client type | Confidential |
| Response types | `code` |
| Redirect URIs | `https://wpxyz.ortoloco.ch/wp-admin/admin-ajax.php?action=openid-connect-authorize` |
| Post logout redirect URIs | the url WordPress returns to after logout, e.g. `https://wpxyz.ortoloco.ch/` |
| JWT algorithm | RS256 |
| Require consent | no |
| Reuse consent | yes |

Client ID and secret are generated on save, enter them in WordPress.

### WordPress plugin "OpenID Connect Client"

| Setting | Value |
|---|---|
| Client ID / Client Secret Key | from the client in the admin |
| OpenID Scope | `openid email profile` |
| Login Endpoint URL | `https://my.ortoloco.ch/openid/authorize` |
| Userinfo Endpoint URL | `https://my.ortoloco.ch/openid/userinfo` |
| Token Validation Endpoint URL | `https://my.ortoloco.ch/openid/token` |
| End Session Endpoint URL | `https://my.ortoloco.ch/openid/end-session` |
| JWKS Endpoint URL | `https://my.ortoloco.ch/openid/jwks` |
| Issuer | `https://my.ortoloco.ch/openid` |

The End Session Endpoint must be `/openid/end-session`, not `https://my.ortoloco.ch/logout`: the logout page of
juntagrico only logs out with POST, the browser redirect of WordPress gets *405 Method Not Allowed* and the user
stays logged in to my.ortoloco. `/openid/end-session` logs out and returns to WordPress if the url is one of the
client's *Post logout redirect URIs*, otherwise it shows a confirmation page.

The discovery document `https://my.ortoloco.ch/openid/.well-known/openid-configuration` lists all endpoints.
Issuer and endpoints are built from the url of the request: Django must see `https`
(the reverse proxy forwards it to gunicorn).

### Claims

With the scopes `openid email profile` the userinfo contains `sub` (user id), `email`, `name`, `given_name`,
`family_name` and `nickname` (`ortoloco/oidc_provider_settings.py`, `userinfo`). There is no `preferred_username`:
the plugin's *Identity Key* must be one of the claims above, e.g. `sub` or `email`.

The additional scope `groups` adds the Django groups of the user as `groups` (`CustomScopeClaims`).
