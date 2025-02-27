from datasette import hookimpl, Response
from urllib.parse import urlencode
import baseconv
import httpx
import secrets
import time


async def oauth2_login(request, datasette):
    redirect_uri = datasette.absolute_url(
        request, datasette.urls.path("/-/oauth2-callback")
    )
    try:
        config = _config(datasette)
    except ConfigError as e:
        return _error(datasette, request, str(e))
    state = secrets.token_hex(16)
    url = "{}?".format(config["auth_url"]) + urlencode(
        {
            "response_type": "code",
            "client_id": config["client_id"],
            "redirect_uri": redirect_uri,
            "scope": config.get("scope") or "openid profile email",
            "state": state,
        }
    )
    response = Response.redirect(url)
    response.set_cookie("oauth2-state", state, max_age=3600)
    return response


async def oauth2_callback(request, datasette):
    try:
        config = _config(datasette)
    except ConfigError as e:
        return _error(datasette, request, str(e))
    code = request.args["code"]
    state = request.args.get("state") or ""
    # Compare state to their cookie
    expected_state = request.cookies.get("oauth2-state") or ""
    if not state or not secrets.compare_digest(state, expected_state):
        return _error(
            datasette,
            request,
            "state check failed, your authentication request is no longer valid",
        )

    # Exchange the code for an access token
    response = httpx.post(
        "{}".format(config["token_url"]),
        data={
            "grant_type": "authorization_code",
            "redirect_uri": datasette.absolute_url(
                request, datasette.urls.path("/-/oauth2-callback")
            ),
            "code": code,
        },
        auth=(config["client_id"], config["client_secret"]),
    )
    if response.status_code != 200:
        return _error(
            datasette,
            request,
            "Could not obtain access token: {}".format(response.status_code),
        )
    # This should have returned an access token
    access_token = response.json()["access_token"]
    # Exchange that for the user info
    profile_response = httpx.get(
        "{}".format(config["userinfo_url"]),
        headers={"Authorization": "Bearer {}".format(access_token)},
    )
    if profile_response.status_code != 200:
        return _error(
            datasette,
            request,
            "Could not fetch profile: {}".format(response.status_code),
        )
    # Set actor cookie and redirect to homepage
    redirect_response = Response.redirect("/")
    expires_at = int(time.time()) + (24 * 60 * 60)
    redirect_response.set_cookie(
        "ds_actor",
        datasette.sign(
            {
                "a": {
                    "name": profile_response.json()['preferred_username'],
                    "id": "root"
                },
                "e": baseconv.base62.encode(expires_at),
            },
            "actor",
        ),
    )
    return redirect_response


@hookimpl
def register_routes():
    return [
        (r"^/-/oauth2-login$", oauth2_login),
        (r"^/-/oauth2-callback$", oauth2_callback),
    ]


class ConfigError(Exception):
    pass


def _config(datasette):
    config = datasette.plugin_config("datasette-oauth2")
    missing = [
        key for key in ("userinfo_url", "token_url", "auth_url", "client_id", "client_secret") if not config.get(key)
    ]
    if missing:
        raise ConfigError(
            "The following oauth2 plugin settings are missing: {}".format(
                ", ".join(missing)
            )
        )
    return config


def _error(datasette, request, message):
    datasette.add_message(request, message, datasette.ERROR)
    return Response.redirect("/")


@hookimpl
def menu_links(datasette, actor):
    config = datasette.plugin_config("datasette-oauth2")
    if not actor:
        return [
            {
                "href": datasette.urls.path("/-/oauth2-login"),
                # "label": config["sign_in_message"] or "Sign in with OAuth2"
                "label": "Sign in with OAuth2"
            },
        ]
