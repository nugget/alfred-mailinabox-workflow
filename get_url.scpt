set myURL to ""
set nameOfActiveApp to (path to frontmost application as text)
if "Safari" is in nameOfActiveApp then
	tell application "Safari"
		set myURL to the URL of the current tab of the front window
	end tell
else if "Chrome" is in nameOfActiveApp then
	tell application "Google Chrome"
		set myURL to the URL of the active tab of the front window
	end tell
end if

return myURL
