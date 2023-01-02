"""Methods and structures relating to Mail-in-a-Box servers."""
import base64
import json
from urllib.parse import urlencode
from io import BytesIO

import pycurl
import certifi

from macnugget import log, fatal, load_globals, success_marker


class Box:
    """Generic container to hold arbitrary global variables."""

    pass


_m = Box()
_m.servers, _m.targets, _m.domains = load_globals()


class Server:
    """A Mail-in-a-Box server connection."""

    def __init__(self):
        """Init the new server object."""
        self.name = ""
        self.url = ""
        self.domains = ""
        self.onepassword_uuid = ""

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
        outbuf["url"] = self.url
        outbuf["domains"] = self.domains
        outbuf["onepassword_uuid"] = self.onepassword_uuid

        if private:
            outbuf["private"] = True
            outbuf["_api_key"] = self._api_key

        return json.dumps(outbuf)

    def get_server_matching_email(self, email):
        """Select MiaB server which handles provided email address."""
        domain = email.split("@")[-1]
        for s in _m.servers.sections():
            for d in _m.servers[s]["domains"].split(","):
                if d.strip() == domain:
                    self.name = s
                    self.url = _m.servers[s].get("url")
                    self.domains = _m.servers[s].get("domains")
                    self._api_key = _m.servers[s].get("api_key")
                    self.onepassword_uuid = _m.servers[s].get("onepassword_uuid")
                    log(
                        "found server",
                        s,
                        _m.servers[s],
                        self._api_key,
                        self.onepassword_uuid,
                    )
                    return

        fatal("Cannot find a server to handle %s addresses" % (domain))

    def login(self, username, password):
        """Log in to MiaB server using API and obtain a session api_key."""
        log("Starting login process")

        if self.url == "":
            fatal("No Mail-in-a-Box server URL found for login")

        if self._api_key != "" and self._api_key is not None:
            # If we have an api_key then we're already logged in
            log("Skipping login, we already have an api_key", self._api_key)
            return

        buffer = BytesIO()

        c = self.Curl()
        log("debug login?", self.debug_login, c)

        authorization_header = encode_basic_auth_header(username, password)
        log("Encoded authorization header", authorization_header)
        custom_headers = ["authorization: " + authorization_header]
        c.setopt(c.HTTPHEADER, custom_headers)

        c.setopt(c.VERBOSE, self.debug_login)
        c.setopt(c.URL, self.url + "/login")
        c.setopt(c.WRITEDATA, buffer)
        c.setopt(c.CAINFO, certifi.where())

        c.setopt(c.POSTFIELDS, "{}")

        c.perform()

        response = json.loads(buffer.getvalue())

        log("login response", json.dumps(response))

        self._username = username
        self._api_key = response.get("api_key", "")
        if self._api_key == "":
            fatal(f'Login failure: {response["reason"]}')

        if self.debug_login:
            log("HTTP Code", c.getinfo(c.HTTP_CODE))
            log(response)

        return response

    def upsert_alias(self, alias, forwards_to):
        """Create or update an alias on the MiaB server."""
        log("Starting alias upsert")

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

        log("postfields", postfields)

        buffer = BytesIO()

        c = self.Curl()
        log("debug upsert?", self.debug_upsert, c)

        authorization_header = encode_basic_auth_header(self._username, self._api_key)
        log("Encoded authorization header", authorization_header)
        custom_headers = ["authorization: " + authorization_header]
        c.setopt(c.HTTPHEADER, custom_headers)

        c.setopt(c.VERBOSE, self.debug_upsert)
        c.setopt(c.URL, self.url + "/mail/aliases/add")
        c.setopt(c.WRITEDATA, buffer)
        c.setopt(c.CAINFO, certifi.where())

        c.setopt(c.POSTFIELDS, postfields)

        log("My post fields are", postfields, post_data)

        c.perform()

        response_code = c.getinfo(c.HTTP_CODE)
        response_text = buffer.getvalue().decode("utf-8")

        if response_code != 200:
            fatal(f"Mail-in-a-Box error {response_code}: {response_text}")
        else:
            print(f"{alias.strip()} {response_text} {success_marker()}")

        return


def server_name(query):
    """Return human-readable name (dict key) of the server for the supplied domain."""
    domain = query.split("@")[-1]
    for s in _m.servers.sections():
        for d in _m.servers[s]["domains"].split(","):
            if d.strip() == domain:
                return s

    return ""


def match_best_domain(query_domain):
    """Choose the best domain name for alias from empty or partial search from user."""
    domain = _m.domains[0] if _m.domains[0:] else "example.org"
    if len(query_domain) > 0:
        for d in _m.domains:
            if d.find(query_domain) == 0:
                return d

    return domain


def match_best_target(query_domain):
    """Choose the appropriate target email (forwards_to) for an alias."""
    if len(query_domain) > 0:
        for t in _m.targets:
            log("mbt target test", t)
            if t.find(query_domain) > 0:
                log("found!", t.find(query_domain))
                return t

            log("not found", t.find(query_domain))

    fatal(f"No target email addresses for domain '{query_domain}'")


def encode_basic_auth_header(username, password):
    """Generate an HTTP Basic Auth header from supplied credentials."""
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"
