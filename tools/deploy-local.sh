#!/bin/bash
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

mybundleid=$(plutil -extract bundleid raw "info.plist")

find "$syncfolder" -name info.plist -print0 | while read -d $'\0' plist
do
	bundleid=$(plutil -extract bundleid raw "$plist" 2>/dev/null || true)

	if [ "$bundleid" == "$mybundleid" ]; then
		dst=$(dirname $plist)
		manifest=("*.py")
		install -cpSv ${manifest[@]} $dst/
		osascript ./tools/reload_workflow.scpt
		exit 
	fi
done

