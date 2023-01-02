"""Methods and structures for interacting with 1Password 8."""

import subprocess
import re

from macnugget import log, fatal


def get_entry(uuid):
    """Obtain login credentials from 1Password agent using item UUID."""
    if uuid == "" or uuid is None:
        fatal("No onepassword_uuid")

    command_line = ["/usr/bin/env", "op", "item", "get", uuid]
    log("running 1Password CLI:", command_line)

    result = subprocess.run(command_line, capture_output=True, text=True)

    if result.stderr != "":
        fatal("1Password error\n", result.stdout, "\n", result.stderr)

    username, password = ("", "")

    match = re.search(r"^\s+username:\s+(\S+)$", result.stdout, re.MULTILINE)
    if match:
        username = match.group(1)
    else:
        fatal("Unable to retrieve username from 1Password for UUID", uuid)

    match = re.search(r"^\s+password:\s+(\S+)$", result.stdout, re.MULTILINE)
    if match:
        password = match.group(1)
    else:
        fatal("Unable to retrieve password from 1Password for UUID", uuid)

    return username, password
