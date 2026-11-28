# Login of other services with my.ortoloco

my.ortoloco is the login for other ortoloco services:

| Service | Protocol | Library | Endpoints |
|---|---|---|---|
| Nextcloud cloud.ortoloco.ch | OAuth2 | django-oauth-toolkit | `/o/…`, `/nextcloud/profile/` |
| WordPress instances | OpenID Connect | django-oauth-toolkit | `/o/…` |

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

Setting up a WordPress instance, using `wpxyz.ortoloco.ch` as the example:

1. once per server: the signing key ([RSA key](#1-rsa-key-once-per-server))
2. check the discovery document ([Test](#2-test-the-provider))
3. install the plugin ([WordPress](#3-prepare-wordpress))
4. one application per instance in my.ortoloco ([Application](#4-application-in-myortoloco))
5. configure the plugin ([Plugin settings](#5-plugin-settings))

### 1. RSA key (once per server)

django-oauth-toolkit signs the ID tokens with RS256. The private key is read from the environment variable
`ORTOLOCO_OIDC_RSA_PRIVATE_KEY` (`ortoloco/settings.py`). Without it, OpenID Connect under `/o/` is disabled and only
OAuth2 (Nextcloud) works. The key is never committed, never written to `settings.py`, and never sent by mail or chat.

Create it on the server, not on a laptop. The variable must be a single line with `\n` instead of line breaks, because
env files (e.g. Docker's `--env-file`) cannot hold several lines:

```bash
(umask 077; openssl genrsa -out oidc.key 4096)
```

```bash
awk 'NF {printf "%s\\n", $0}' oidc.key
```

Add the output to the file that holds the other `JUNTAGRICO_*` variables, without quotes:

    ORTOLOCO_OIDC_RSA_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\nMIIJ…\n-----END PRIVATE KEY-----\n

Then restart the container and delete `oidc.key` (or keep it in the password store).

A new key invalidates all ID tokens that were issued before. WordPress fetches the public key again from the JWKS
endpoint (cache: plugin setting *JWKS Cache TTL*), logged-in users stay logged in.

### 2. Test the provider

```bash
curl -s https://my.ortoloco.ch/o/.well-known/openid-configuration | python3 -m json.tool
```

```bash
curl -s https://my.ortoloco.ch/o/.well-known/jwks.json
```

| Check | Expected | Otherwise |
|---|---|---|
| status of both urls | 200 | 403: nginx blocks paths with a dot, see below. 404: the key is missing (OIDC disabled) |
| `issuer` | `https://my.ortoloco.ch/o` | `http://…`: the reverse proxy does not forward `https` to Django |
| `end_session_endpoint` | `https://my.ortoloco.ch/o/logout/` | missing: `OIDC_RP_INITIATED_LOGOUT_ENABLED` is off |
| `scopes_supported` | `openid`, `profile`, `email`, `groups`, `member_id`, `nextcloud` | |
| `claims_supported` | `sub`, `name`, `given_name`, `family_name`, `email`, `groups`, `id` | |
| `jwks.json` | `{"keys": [{"kty": "RSA", "alg": "RS256", "use": "sig", "kid": …}]}` | `{"keys": []}`: the key is missing |

`https://my.ortoloco.ch/o/userinfo/` without a token must answer 401.

nginx denies all paths that contain `/.` (hidden files). `/o/.well-known/` must be passed to Django before that rule,
with the same proxy lines as `location /`:

    location ^~ /o/.well-known/ {
        proxy_pass …;   # as in location /
    }

Locally: set the variable (e.g. in `myenv.txt`), start `python manage.py runserver` and open
`http://127.0.0.1:8000/o/.well-known/openid-configuration`. The tests use a throwaway key in
`ortoloco/settings_test.py` and test the flows of WordPress in `ortoloco/tests/test_login_clients.py`.

### 3. Prepare WordPress

1. *Plugins → Add New*, search for **OpenID Connect Generic Client** (by daggerhart, slug
   `daggerhart-openid-connect-generic`), install and activate it. Version 3.11 or newer is needed for *Quick Setup*.
2. *Settings → OpenID Connect Client*. At the bottom, under *Notes*, the plugin shows its **Redirect URI**, normally
   `https://wpxyz.ortoloco.ch/wp-admin/admin-ajax.php?action=openid-connect-authorize`. Copy it for the application.
3. Recommended, so the logout always returns to the same address: a must-use plugin
   `wp-content/mu-plugins/logout-redirect.php`

   ```php
   <?php
   add_filter('logout_redirect', fn() => home_url('/'), 99);
   ```

   Without it, WordPress returns to `https://wpxyz.ortoloco.ch/wp-login.php?loggedout=true&wp_lang=de_DE`, and the
   address changes with the language and with `redirect_to` links.

### 4. Application in my.ortoloco

One application per instance: if one WordPress is hacked, only its secret must be changed, and its ID tokens are not
valid for the other instances (`aud`). *Django OAuth Toolkit → Applications* (`/admin/oauth2_provider/application/`),
*Add*:

| Field | Value for `wpxyz.ortoloco.ch` |
|---|---|
| Client id | generated, enter it in WordPress |
| User | empty |
| Redirect uris | `https://wpxyz.ortoloco.ch/wp-admin/admin-ajax.php?action=openid-connect-authorize` |
| Post logout redirect uris | with the must-use plugin: `https://wpxyz.ortoloco.ch/`<br>without: `https://wpxyz.ortoloco.ch/wp-login.php?loggedout=true&wp_lang=de_DE https://wpxyz.ortoloco.ch/wp-login.php?loggedout=true` |
| Client type | Confidential |
| Authorization grant type | Authorization code |
| Client secret | generated, **copy it before saving**: it is hashed on save and cannot be shown again |
| Hash client secret | yes |
| Name | `wpxyz` |
| Skip authorization | yes (no consent page) |
| Algorithm | RSA with SHA-2 256 (an error on save means that the key is missing) |
| Allowed origins | empty |

Redirect uris and post logout redirect uris are compared **exactly**, including the query string (RFC 9700): every
parameter, its order and the trailing `/` count. Several uris are separated by spaces. If the address is wrong,
my.ortoloco answers *Mismatching redirect URI* (login) or *This client does not have this redirect uri registered*
(logout). The address WordPress sent is in the browser's address bar, parameter `redirect_uri` or
`post_logout_redirect_uri` (url-encoded).

### 5. Plugin settings

*Settings → OpenID Connect Client*:

1. Open **⚡ Quick Setup: Import from Discovery Document**, enter
   `https://my.ortoloco.ch/o/.well-known/openid-configuration` as *Discovery URL* and click *Load Configuration*.
   It fills in *Login Endpoint URL*, *Userinfo Endpoint URL*, *Token Validation Endpoint URL*,
   *End Session Endpoint URL*, *JWKS URI* and *Issuer* (but not the scope).
2. Fill in the other fields as below and click **Save Changes**. The import is not saved before that.

| Setting | Value | Why |
|---|---|---|
| Login Type | *OpenID Connect button on login form* | *Auto Login* sends everybody to my.ortoloco, also WordPress-only admins |
| Client ID | from the application | |
| Client Secret Key | from the application | the secret, not the hash shown in the admin after saving |
| OpenID Scope | `openid email profile` | `groups` is not needed: the plugin does not use it (see below) |
| Login Endpoint URL | `https://my.ortoloco.ch/o/authorize/` | from Quick Setup |
| Userinfo Endpoint URL | `https://my.ortoloco.ch/o/userinfo/` | from Quick Setup |
| Token Validation Endpoint URL | `https://my.ortoloco.ch/o/token/` | from Quick Setup |
| End Session Endpoint URL | `https://my.ortoloco.ch/o/logout/` | from Quick Setup. Logs out of my.ortoloco too; empty: logout in WordPress only |
| JWKS URI | `https://my.ortoloco.ch/o/.well-known/jwks.json` | from Quick Setup |
| Issuer | `https://my.ortoloco.ch/o` | from Quick Setup |
| JWKS Cache TTL, ACR values, HTTP Request Timeout, State time limit | default / empty | |
| Identity Key | `sub` | the user id of my.ortoloco, becomes the WordPress username. The default `preferred_username` is not delivered |
| Nickname Key | `given_name` | **must be a delivered claim**, otherwise the login fails with *No nickname found*. The default `preferred_username` is not delivered |
| Email Formatting | `{email}` | |
| Display Name Formatting | `{given_name} {family_name}` | |
| Identify with User Name | off | |
| Use PKCE | on | my.ortoloco supports S256 (it does not require it, because Nextcloud sends none) |
| Enable Refresh Token | on (default) | |
| Disable SSL Verify, Allow Internal IDP | off | |
| Link Existing Users | off | see below |
| Link Users Without Verified Email | off | |
| Create user if does not exist | on | |
| Redirect Back to Origin Page, Redirect to the login screen when session is expired, Enforce Privacy | as the site needs | |
| Enable Logging | on while setting up, then off | the log is shown below the settings |

The plugin recognizes accounts by `sub` (user meta `openid-connect-generic-subject-identity`), not by email or
username. *Link Existing Users* would link a login to an existing WordPress account with the same email. my.ortoloco
does not deliver `email_verified`, so this only works together with *Link Users Without Verified Email*, and then
every member who sets the email of a WordPress admin in my.ortoloco becomes that admin. Leave both off. Existing
local accounts keep their WordPress password.

**Users and roles:** a user is identified by the user id of my.ortoloco (`sub`, e.g. `1680`), which is also the
username. It is the Django user id, not the member id (Nextcloud uses the member id). Email, names and display name
are taken from my.ortoloco at the first login. The plugin does not support groups: it does not read the `groups`
claim and does not set roles. A new user gets the *New User Default Role* (*Settings → General*, keep it
*Subscriber*). Roles such as *Editor* or *Administrator* must be given by hand in WordPress (*Users*) after the
person's first login.

### Test the login

1. In a private window, open `https://wpxyz.ortoloco.ch/wp-login.php` and click the button: my.ortoloco asks for the
   login and returns to WordPress, logged in.
2. *Users*: the new user has the user id of my.ortoloco as username (e.g. `1680`), email, first and last name, and the
   display name *First Last*.
3. Log out: WordPress, then my.ortoloco log out, and the browser returns to the post logout redirect uri.

| Error | Cause |
|---|---|
| *Mismatching redirect URI* on my.ortoloco | redirect uri of the application ≠ *Redirect URI* in the plugin's notes (e.g. *Alternate Redirect URI* is on) |
| *invalid_client* / *Invalid client* | client id or secret wrong, or the hash was copied instead of the secret |
| *No nickname found in user claim using key* | *Nickname Key* is not a delivered claim (use `given_name`) |
| *No appropriate username found* | *Identity Key* is not `sub` and the claim is missing |
| *Your login could not be linked to an existing account* | *Link Existing Users* is on, see above |
| JWT / signature / issuer error in the plugin log | *JWKS URI* or *Issuer* wrong, or `/o/.well-known/` is blocked (test 2) |
| *This client does not have this redirect uri registered* on logout | post logout redirect uri not registered exactly (see application) |
| logout fails with *405 Method Not Allowed*, still logged in to my.ortoloco | *End Session Endpoint URL* is `https://my.ortoloco.ch/logout/`: it only logs out with POST, use `/o/logout/` |

### Claims

| Scope | Claims in the id token and in userinfo |
|---|---|
| `openid` | `sub` (user id) |
| `profile` | `name`, `given_name`, `family_name` |
| `email` | `email` |
| `groups` | `groups`, the Django groups of the user, only for clients that request this scope |
| `member_id` | `id` (member id, identifies the accounts in Nextcloud) |
| `nextcloud` | none. Legacy, access to `/nextcloud/profile/` |

The claims are defined in `ortoloco/oauth_validator.py`.
