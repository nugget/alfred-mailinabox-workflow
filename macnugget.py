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
    servers = configparser.ConfigParser()
    servers.read_string(os.environ.get("MIAB_SERVERS", ""))
    targets = os.environ.get("MIAB_TARGETS", "").strip().split(",")

    domains = []
    for s in servers.sections():
        for d in servers[s]["domains"].split(","):
            domains.append(d.strip())

    log(json.dumps(domains))
    return servers, targets, domains


def log(*args, **kwargs):
    """Emit a log line (stderr) for Alfredapp workflow debugger."""
    print(*args, file=sys.stderr, **kwargs)


def fatal(*args, **kwargs):
    """Emit a log line for Alfredapp and then exit the script with an errorcode."""
    print(*args, **kwargs)
    exit(-1)
