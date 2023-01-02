#!/usr/bin/env python3

"""Structures and functions for interacting with Mail-in-a-Box servers."""

import sys
import os
import json
import random
from urllib.parse import urlparse

import miab
from macnugget import log, load_globals


class Box:
    """Generic container to hold arbitrary global variables."""

    pass


_m = Box()
_m.api_key = ""
_m.servers, _m.targets, _m.domains = load_globals()
_m.current_url_string = os.environ.get("CURRENT_URL", "")
_m.current_url = urlparse(_m.current_url_string)


def generate_item(username, domain):
    """
    Return a JSON code block representing a single Alfredapp search result item.

    This function produces a JSON-formatted code block which adheres to the
    Alfredapp JSON specification for search result items.  The specification
    documentation can be viewed here:

    https://www.alfredapp.com/help/workflows/inputs/script-filter/json/

    The returned item corresponds to a proposed new email alias which can be
    created on the server by this workflow built from the following inputs:

    :username: is the base, left-hand side of the email alias
    :domain: is the right-hand side of the email alias
    """
    email = username + "@" + domain
    i = {
        "type": "default",
        "title": "TITLE",
        "subtitle": "SUBTITLE",
        "arg": "ARG",
        "autocomplete": "Desktop",
        "icon": {"path": "icon.png"},
        "mods": {
            "cmd": {
                "arg": "ARG",
                "subtitle": "SUBTITLE",
            }
        },
    }

    i["title"] = email
    i["arg"] = email
    i["subtitle"] = (
        "Create alias " + username + " on the " + miab.server_name(email) + " server"
    )

    i["mods"]["cmd"]["arg"] = username + random_number() + "@" + domain
    i["mods"]["cmd"]["subtitle"] = (
        "Create alias "
        + username
        + random_number()
        + " on the "
        + miab.server_name(email)
        + " server"
    )

    return i


def parse_query():
    """Split a user-supplied search term into a username and domain."""
    query = sys.argv[1] if sys.argv[1:] else ""
    query_username = query.split("@")[0] if query.split("@")[0:] else ""
    query_domain = query.split("@")[1] if query.split("@")[1:] else ""
    return query_username, query_domain


def random_number():
    """Generate a random number between 100 and 999 and return as a string."""
    rand = random.randint(100, 999)
    return str(rand)


def random_word():
    """Choose a random word from the dictionary."""
    source_file = "/usr/share/dict/words"
    with open(source_file, "r", encoding="utf-8") as dictionary:
        size = os.path.getsize(source_file)
        spot = random.randint(0, size)
        dictionary.seek(spot)

        # Our random, byte-position seek into the dictionary file has almost
        # certainly landed us in the middle of a word. Here we do a gratuitious
        # readline to clear out the word fragment.
        _ = dictionary.readline()

        word = dictionary.readline().strip()

    return word


def current_url_base():
    """Reduce a FQDN to just a single, hopefully-meaningful word."""
    if _m.current_url_string:
        return _m.current_url.hostname.split(".")[-2]
    return ""


query_username, query_domain = parse_query()
domain = miab.match_best_domain(query_domain)

items = []
if len(query_username) > 0:
    log(f"Adding item from query_username {query_username}")
    items.append(generate_item(query_username, domain))

if len(current_url_base()) > 0:
    log(f"Adding item from url_base {current_url_base}")
    items.append(generate_item(current_url_base(), domain))

log("Adding 3 random word items")
items.append(generate_item(random_word(), domain))
items.append(generate_item(random_word(), domain))
items.append(generate_item(random_word(), domain))

log(f"Prepared {len(items)} items for Alfred")
outdict = {"items": items}

outbuf = json.dumps(outdict)

sys.stdout.write(outbuf)
