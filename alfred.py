"""Methods for Alfred app."""

import os
import configparser
from macnugget import log, fatal


class Config:
    """Object that holds our workflow configuration from Alfred."""

    def __init__(self):
        """Initialize config items."""
        self._servers = configparser.ConfigParser()
        self._servers.read_string(os.environ.get("MIAB_SERVERS", ""))
        self._targets = os.environ.get("MIAB_TARGETS", "").strip().split(",")

        self._domains = []
        for server in self._servers.sections():
            for domain in self._servers[server]["domains"].split(","):
                self._domains.append(domain.strip())

        log(os.environ.get("MIAB_TARGETS"))
        log(self._targets)
        log("Workflow configuration initialized")

    def servers(self):
        """Return parsed MIAB_SERVERS configuration."""
        return self._servers

    def targets(self):
        """Return array of target email addresses."""
        return self._targets

    def domains(self):
        """Return array of supported email domains."""
        return self._domains

    def server_for_email_address(self, email):
        """Return the MiaB server config for the provided email address."""
        email_domain = email.split("@")[-1]

        for name in self._servers.sections():
            for domain in self._servers[name]["domains"].split(","):
                if domain.strip() == email_domain:
                    self._servers[name]["name"] = name
                    return self._servers[name]

        fatal(f"No Mail-in-a-Box server is configured to handle {email_domain}")

    def server_name(self, email):
        """Return name (dict key) of MiaB server for the provided email address."""
        server = self.server_for_email_address(email)
        return server["name"]

    def match_best_domain(self, query_domain):
        """Choose the matching domain name for empty or partial search from user."""
        domain = self._domains[0] if self._domains[0:] else "example.org"
        if len(query_domain) > 0:
            for d in self._domains:
                if d.find(query_domain) == 0:
                    return d

        return domain

    def match_best_target(self, query_domain):
        """Choose the appropriate target email (forwards_to) for an alias."""
        if len(query_domain) > 0:
            for t in self._targets:
                if t.find(query_domain) > 0:
                    return t

        fatal(f"No target email addresses for domain '{query_domain}'")
