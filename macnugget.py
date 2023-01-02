"""Container module for miscellaneous helper functions."""

import os
import sys
import configparser
import json


def success_marker():
    """Emit the magic character that indicates success."""
    return "☺".strip()


def load_globals():
    """Parse and process the environment variables set by Alfredapp."""
    miab_servers = configparser.ConfigParser()
    miab_servers.read_string(os.environ.get("MIAB_SERVERS", ""))
    targets = os.environ.get("MIAB_TARGETS", "").strip().split(",")

    domains = []
    for server in miab_servers.sections():
        for domain in miab_servers[server]["domains"].split(","):
            domains.append(domain.strip())

    log(json.dumps(domains))
    return miab_servers, targets, domains


def log(*args, **kwargs):
    """Emit a log line (stderr) for Alfredapp workflow debugger."""
    print(*args, file=sys.stderr, **kwargs)


def fatal(*args, **kwargs):
    """Emit a log line for Alfredapp and then exit the script with an errorcode."""
    print(*args, **kwargs)
    sys.exit(-1)
