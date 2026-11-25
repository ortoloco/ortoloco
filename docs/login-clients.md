# Login of other services with my.ortoloco

my.ortoloco is the login for other ortoloco services:

| Service | Protocol | Library | Endpoints |
|---|---|---|---|
| Nextcloud cloud.ortoloco.ch | OAuth2 | django-oauth-toolkit | `/o/…`, `/nextcloud/profile/` |
| WordPress instances, new | OpenID Connect | django-oauth-toolkit | `/o/…` |
| WordPress instances, until moved | OpenID Connect | django-oidc-provider | `/openid/…` |

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

- `OAUTH2_PROVIDER['SCOPES']` contains `nextcloud`, `OAUTH2_PROVIDER['DEFAULT_SCOPES']` is `nextcloud` for requests
  without scope (the default are all scopes, `openid` fails without algorithm).
- `OAUTH2_PROVIDER['PKCE_REQUIRED'] = False`: Social Login sends no PKCE `code_challenge`. Since
  django-oauth-toolkit 2.0 PKCE is required by default, without this setting nobody can log in to Nextcloud.
- The profile view is protected with `oauth2_provider`'s `protected_resource` and needs an access token with the scope
  `nextcloud`. `OAuth2TokenMiddleware` and `OAuth2Backend` of oauth2_provider are not used on purpose: with them, an
  access token of any client would log in on every page, and a hacked WordPress could act as its users in my.ortoloco.

Nextcloud must stay a custom *OAuth2* provider: it identifies accounts by the member id of the profile. With OpenID
Connect this would be the user id (`sub`), which is a different number. Accounts would be mixed up.

`/nextcloud/profile/` could be replaced by `/o/userinfo/` while staying custom OAuth2: Social Login uses the claim `id`
(member id, scope `member_id`) before `sub`. Without this scope it would use `sub` and mix up accounts.
This needs the scopes `openid profile email groups member_id`, the algorithm
RSA with SHA-2 256 in the application and the groups claim `groups`. Try it with a test instance first.

## WordPress (OpenID Connect with django-oauth-toolkit)

### Once per server

Create a key, add it to the environment as `ORTOLOCO_OIDC_RSA_PRIVATE_KEY` (one line, `\n` instead of line breaks) and
restart. Never commit it.

    openssl genrsa 4096 | awk 'NF {printf "%s\\n", $0}'

### Add a client for a new WordPress instance

*Django OAuth Toolkit → Applications* (`/admin/oauth2_provider/application/`), add:

| Field | Value |
|---|---|
| Client id, client secret | generated, **copy the secret before saving**: it is hashed on save and cannot be shown again |
| User | empty |
| Redirect uris | `https://wpxyz.ortoloco.ch/wp-admin/admin-ajax.php?action=openid-connect-authorize` |
| Post logout redirect uris | the urls WordPress returns to after logout, separated by space, must match exactly including parameters |
| Client type | Confidential |
| Authorization grant type | Authorization code |
| Hash client secret | yes |
| Name | the instance, e.g. `wpxyz` |
| Skip authorization | yes (no consent page) |
| Algorithm | RSA with SHA-2 256 (an error means that the key is missing) |

### WordPress plugin "OpenID Connect Client"

| Setting | Value |
|---|---|
| Client ID / Client Secret Key | from the application |
| OpenID Scope | `openid email profile` |
| Login Endpoint URL | `https://my.ortoloco.ch/o/authorize/` |
| Userinfo Endpoint URL | `https://my.ortoloco.ch/o/userinfo/` |
| Token Validation Endpoint URL | `https://my.ortoloco.ch/o/token/` |
| End Session Endpoint URL | `https://my.ortoloco.ch/o/logout/` (empty: logout in WordPress only) |
| JWKS Endpoint URL | `https://my.ortoloco.ch/o/.well-known/jwks.json` |
| Issuer | `https://my.ortoloco.ch/o` |

### Claims

| Scope | Claims in the id token and in userinfo |
|---|---|
| `openid` | `sub` (user id) |
| `profile` | `name`, `given_name`, `family_name` |
| `email` | `email` |
| `groups` | `groups`, the Django groups of the user, only for clients that request this scope |
| `member_id` | `id` (member id, identifies the accounts in Nextcloud) |
| `nextcloud` | none. Legacy, access to `/nextcloud/profile/` |

### Move an instance from django-oidc-provider

1. Add an application as above. With client id and secret of the old client, only the endpoints and the issuer change
   in WordPress.
2. Change the endpoints and the issuer in the plugin. The claims are the same as with django-oidc-provider,
   except for `nickname` which is not delivered any more (`ortoloco/oauth_validator.py`), WordPress recognizes existing accounts by `sub`.
3. When all instances are moved, remove django-oidc-provider.

## WordPress (OpenID Connect with django-oidc-provider, until moved)

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
