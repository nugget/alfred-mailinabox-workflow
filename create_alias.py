#!/usr/bin/env python3

"""Script creates/updates an alias on a Mail-in-a-Box server."""
import sys

import miab
import onepassword
from macnugget import log


def main(*args):
    """Create/Update an alias on server."""
    alias = args[1] if args[1:] else ""
    _, alias_domain = alias.split("@")
    target = miab.match_best_target(alias_domain)

    server = miab.Server()
    server.get_server_matching_email(alias)

    username, password = onepassword.get_entry(server.onepassword_uuid)
    log("Retrieved credentials from 1Password", username, password)
    server.login(username, password)

    server.upsert_alias(alias, target)

    server.close()


if __name__ == '__main__':
    _, *script_args = sys.argv
    main(*script_args)
