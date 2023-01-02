#!/bin/bash
#
# This script will copy all the relevant files from your current development
# directory into the Alfred user workflow directory. This is only useful if
# you're doing active development in a local clone of the git repository
# and you want to push your local changes to the live workflow being used by
# Alfred on your computer.
#
# Run it from repo root, as in:  ./tools/deploy-local.sh
#
# Not very well tested, but it works great on my machine!  :)
#
set -euo pipefail

# Get location of workflows from Alfred preferences
syncfolder=$(defaults read com.runningwithcrayons.Alfred-Preferences syncfolder)
# Expansion/globbing does not work inside variables, force it here
syncfolder=$(eval echo $syncfolder)

if [ ! -d "$syncfolder" ]; then
	echo "Cannot locate Alfred sync folder ($syncfolder)"
	exit 1
fi

if [ ! -e "script_filter.py" ]; then
	echo "Run this script from the repo root as ./tools/$(basename "$0")" >/dev/stderr
	exit 1
fi

# Figure out what bundleID corresponds to this workflow
mybundleid=$(plutil -extract bundleid raw "info.plist")

# Walk through all info.plist files in the Alfred sync directory
find "$syncfolder" -name info.plist -print0 | while read -d $'\0' plist
do
	# If this info.plist file is for a workflow, see what bundleID it is
	bundleid=$(plutil -extract bundleid raw "$plist" 2>/dev/null || true)

	# Am I looking at the deployed version of this workflow?
	if [ "$bundleid" == "$mybundleid" ]; then
		# Yes -- let's overwrite the deployed workflow with these files
		dst=$(dirname $plist)
		manifest=("*.py")
		install -cpSv ${manifest[@]} $dst/
		osascript ./tools/reload_workflow.scpt
		exit 
	fi
done
