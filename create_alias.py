#!/usr/bin/env python3

"""Script creates/updates an alias on a Mail-in-a-Box server."""
import sys

import alfred
import miab
import onepassword
from macnugget import log


workflow = alfred.Config()


def main(*args):
    """Create/Update an alias on server."""
    alias = args[0] if args[0:] else ""
    _, alias_domain = alias.split("@")

    server_config = workflow.server_for_email_address(alias)
    log(server_config)
    target = workflow.match_best_target(alias_domain)

    server = miab.Server()
    workflow.server_for_email_address(alias)

    username, password = onepassword.get_entry(server_config["onepassword_uuid"])
    log("Retrieved credentials from 1Password", username, password)
    server.login(server_config["url"], username, password)

    server.upsert_alias(alias, target)

    server.close()


if __name__ == '__main__':
    _, *script_args = sys.argv
    main(*script_args)
