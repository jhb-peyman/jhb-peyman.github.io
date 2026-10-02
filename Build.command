#!/bin/bash
# Double-click me: rebuilds the website and the CV PDF from content.toml, then opens both so you can look.
cd "$(dirname "$0")" || exit 1
echo "Building from content.toml ..."
echo
if python3 build.py; then
  echo
  echo "Opening the website and the CV so you can check them."
  open index.html
  open Peyman_Jahanbin_CV.pdf
  echo "When you are happy, double-click Publish.command to put it online."
else
  echo
  echo "Nothing was published. Fix the message above in content.toml, save, and double-click Build.command again."
fi
echo
read -n 1 -s -r -p "Press any key to close this window."
