#!/usr/bin/env bash
# Commit the generated files and push to main. If main moved (the offers bot pushed meanwhile) and the rebase
# conflicts, throw the local generated result away, take the newest main and generate again: generated files
# are always rebuildable, so the bot's data wins and nothing is merged by hand.
# usage: tools/push_generated.sh "<commit message>" <paths...>
set -uo pipefail
msg="$1"; shift
git config user.name "Wafferna Rebuild"
git config user.email "actions@users.noreply.github.com"
git add "$@"
if git diff --cached --quiet; then echo "nothing to commit"; exit 0; fi
git commit -q -m "$msg"
for i in 1 2 3 4; do
  if git pull --rebase origin main && git push origin HEAD:main; then exit 0; fi
  echo "push attempt $i failed, regenerating on top of the latest main"
  git rebase --abort 2>/dev/null || true
  git reset -q --hard origin/main
  git fetch -q origin main && git reset -q --hard origin/main
  bash tools/rebuild_all.sh
  git add "$@"
  if git diff --cached --quiet; then echo "nothing left to commit"; exit 0; fi
  git commit -q -m "$msg"
  sleep $((i * 5))
done
echo "could not push after 4 attempts"; exit 1
