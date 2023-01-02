"""Methods and structures relating to Mail-in-a-Box servers."""
import base64
import json
from urllib.parse import urlencode
from io import BytesIO

import pycurl
import certifi

from macnugget import log, fatal, success_marker


class Server:
    """A Mail-in-a-Box server connection."""

    def __init__(self):
        """Init the new server object."""
        self.name = ""
        self.url = ""
        self.domains = ""

        self.debug_login = False
        self.debug_upsert = False

        self._username = ""
        self._api_key = ""
        self._c = None

    def Curl(self):
        """Return Curl session handle (new or reused)."""
        if self._c:
            log("Reusing existing Curl session", self._c)
        else:
            log("Opening new Curl session")
            self._c = pycurl.Curl()

        return self._c

    def close(self):
        """Close curl session."""
        self._c.close()
        self._c = None
        log("Closed Curl connection")

    def dumps(self, private=False):
        """Return debugging structure suitable for text output."""
        outbuf = {}
        outbuf["name"] = self.name
        outbuf["url"] = self.url
        outbuf["domains"] = self.domains

        if private:
            outbuf["_api_key"] = self._api_key

        return json.dumps(outbuf)

    def login(self, url, username, password):
        """Log in to MiaB server using API and obtain a session api_key."""
        log("Starting login process")

        if self._api_key != "" and self._api_key is not None:
            # If we have an api_key then we're already logged in
            log("Skipping login, we already have an api_key", self._api_key)
            return

        buffer = BytesIO()

        c = self.Curl()

        authorization_header = encode_basic_auth_header(username, password)
        log("Encoded authorization header", authorization_header)
        custom_headers = ["authorization: " + authorization_header]
        c.setopt(c.HTTPHEADER, custom_headers)

        c.setopt(c.VERBOSE, self.debug_login)
        c.setopt(c.URL, url + "/login")
        c.setopt(c.WRITEDATA, buffer)
        c.setopt(c.CAINFO, certifi.where())

        c.setopt(c.POSTFIELDS, "{}")

        c.perform()

        response = json.loads(buffer.getvalue())

        self._username = username
        self._api_key = response.get("api_key", "")
        if self._api_key == "":
            fatal(f'Login failure: {response["reason"]}')

        # Successful login, let's retain the URL for future activity
        self.url = url

        if self.debug_login:
            log("HTTP Code", c.getinfo(c.HTTP_CODE))
            log(json.dumps(response))

        return response

    def upsert_alias(self, alias, forwards_to):
        """Create or update an alias on the MiaB server."""
        log(f"Creating alias {alias} -> {forwards_to})")

        if self.url == "":
            fatal("No Mail-in-a-Box server URL found for login")

        if self._api_key == "" or self._api_key is None:
            fatal("Missing API Key")

        if alias == "" or alias is None:
            fatal("Cannot create an empty alias!")

        post_data = {
            "update_if_exists": 1,
            "address": alias,
            "forwards_to": forwards_to,
            "permitted_senders": "",
        }

        postfields = urlencode(post_data)

        if self.debug_upsert:
            log("postfields", postfields)

        buffer = BytesIO()

        c = self.Curl()

        authorization_header = encode_basic_auth_header(self._username, self._api_key)

        if self.debug_upsert:
            log("Encoded authorization header", authorization_header)

        custom_headers = ["authorization: " + authorization_header]
        c.setopt(c.HTTPHEADER, custom_headers)

        c.setopt(c.VERBOSE, self.debug_upsert)
        c.setopt(c.URL, self.url + "/mail/aliases/add")
        c.setopt(c.WRITEDATA, buffer)
        c.setopt(c.CAINFO, certifi.where())

        c.setopt(c.POSTFIELDS, postfields)

        if self.debug_upsert:
            log("My post fields are", postfields, post_data)

        c.perform()

        response_code = c.getinfo(c.HTTP_CODE)
        response_text = buffer.getvalue().decode("utf-8")

        if response_code != 200:
            fatal(f"Mail-in-a-Box error {response_code}: {response_text}")
        else:
            print(f"{alias.strip()} {response_text} {success_marker()}")

        return


def encode_basic_auth_header(username, password):
    """Generate an HTTP Basic Auth header from supplied credentials."""
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"
