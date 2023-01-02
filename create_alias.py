#!/usr/bin/env python3

"""Script creates/updates an alias on a Mail-in-a-Box server."""
import sys

import miab
import onepassword
from macnugget import log

alias = sys.argv[1] if sys.argv[1:] else ""
alias_username, alias_domain = alias.split("@")
target = miab.match_best_target(alias_domain)

server = miab.Server()
server.get_server_matching_email(alias)

username, password = onepassword.get_entry(server.onepassword_uuid)
log("Retrieved credentials from 1Password", username, password)
server.login(username, password)

server.upsert_alias(alias, target)

server.close()
