# datasette-oauth2

[![PyPI](https://img.shields.io/pypi/v/datasette-oauth2.svg)](https://pypi.org/project/datasette-oauth2/)
[![Changelog](https://img.shields.io/github/v/release/simonw/datasette-oauth2?include_prereleases&label=changelog)](https://github.com/simonw/datasette-oauth2/releases)
[![Tests](https://github.com/simonw/datasette-oauth2/workflows/Test/badge.svg)](https://github.com/simonw/datasette-oauth2/actions?query=workflow%3ATest)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/simonw/datasette-oauth2/blob/main/LICENSE)

Datasette plugin that authenticates users using OAuth2.

See [Simplest possible OAuth authentication with Auth0](https://til.simonwillison.net/oauth2/oauth-with-oauth2) for more about how this plugin works.

## Installation

Install this plugin in the same environment as Datasette.

    $ datasette install datasette-oauth2

## Demo

You can try this out at [datasette-oauth2-demo.datasette.io](https://datasette-oauth2-demo.datasette.io/) - click on the top right menu icon and select "Sign in with Auth0".

## Initial configuration (Keycloak)

First, create a new client in Keycloak. You will need the domain, client ID and client secret for that application.

Add `http://127.0.0.1:8001/-/oauth2-callback` to the list of Allowed Callback URLs.

Then configure these plugin secrets using `metadata.yml`:

```yaml
plugins:
  datasette-oauth2:
    userinfo_url: 
      "$env": OAUTH2_USERINFO_URL
    token_url: 
      "$env": OAUTH2_TOKEN_URL
    authorize_url: 
      "$env": OAUTH2_AUTH_URL
    client_id:
      "$env": OAUTH2_CLIENT_ID
    client_secret:
      "$env": OAUTH2_CLIENT_SECRET
```
Only the `client_secret` needs to be kept secret, but for consistency I recommend using the `$env` mechanism for all five.

In development, you can run Datasette and pass in environment variables like this:
```
OAUTH2_DOMAIN="your-domain.us.oauth2.com" \
OAUTH2_CLIENT_ID="...client-id-goes-here..." \
OAUTH2_CLIENT_SECRET="...secret-goes-here..." \
OAUTH2_TOKEN_URL="https://$KEYCLOAK_DOMAIN/realms/REALM_NAME/protocol/openid-connect/token" \
OAUTH2_AUTH_URL="https://$KEYCLOAK_DOMAIN/realms/REALM_NAME/protocol/openid-connect/auth" \
OAUTH2_USERINFO_URL="https://$KEYCLOAK_DOMAIN/realms/REALM_NAME/protocol/openid-connect/userinfo" \
datasette -m metadata.yml
```

If you are deploying using `datasette publish` you can pass these using `--plugin-secret`. For example, to deploy using Cloud Run you might run the following:
```
datasette publish cloudrun mydatabase.db \
--install datasette-oauth2 \
--plugin-secret datasette-oauth2 client_id "your-client-id" \
--plugin-secret datasette-oauth2 client_secret "your-client-secret" \
--plugin-secret datasette-oauth2 token_url "https://$KEYCLOAK_DOMAIN/realms/REALM_NAME/protocol/openid-connect/token" \
--plugin-secret datasette-oauth2 auth_url "https://$KEYCLOAK_DOMAIN/realms/REALM_NAME/protocol/openid-connect/auth" \
--plugin-secret datasette-oauth2 userinfo_url "https://$KEYCLOAK_DOMAIN/realms/REALM_NAME/protocol/openid-connect/userinfo" \ 
--service datasette-oauth2-demo
```
Once your Datasette instance is deployed, you will need to add its callback URL to the "Allowed Callback URLs" list in Auth0.

The callback URL should be something like:

    https://url-to-your-datasette/-/oauth2-callback

## Usage

Once installed, a "Sign in with Auth0" menu item will appear in the Datasette main menu.

You can sign in and then visit the `/-/actor` page to see full details of the `oauth2` profile that has been authenticated.

You can then use [Datasette permissions](https://docs.datasette.io/en/stable/authentication.html#configuring-permissions-in-metadata-json) to grant or deny access to different parts of Datasette based on the authenticated user.

## Development

To set up this plugin locally, first checkout the code. Then create a new virtual environment:

    cd datasette-oauth2
    python3 -mvenv venv
    source venv/bin/activate

Now install the dependencies and test dependencies:

    pip install -e '.[test]'

To run the tests:

    pytest
