#!/bin/bash
# Double-click me: rebuilds, then sends the changes to GitHub. The live site updates about a minute later.
cd "$(dirname "$0")" || exit 1
echo "Rebuilding first ..."
echo
if ! python3 build.py; then
  echo
  echo "The build failed, so nothing was published. Fix content.toml and try again."
  read -n 1 -s -r -p "Press any key to close this window."
  exit 1
fi
echo
echo "These files changed:"
git status --short
if [ -z "$(git status --porcelain)" ]; then
  echo "  (nothing: the site is already up to date)"
  read -n 1 -s -r -p "Press any key to close this window."
  exit 0
fi
echo
read -p "Press Return to publish these changes to the live site (or close this window to cancel). " _
git add -A
git commit -q -m "Update site content ($(date '+%Y-%m-%d'))"
if GIT_TERMINAL_PROMPT=0 git push origin main; then
  echo
  echo "Published. Give it about a minute, then reload https://jhb-peyman.github.io"
else
  echo
  echo "The push did not go through (see the message above). Your changes are saved on this Mac; run Publish.command again once the problem is fixed."
fi
echo
read -n 1 -s -r -p "Press any key to close this window."
