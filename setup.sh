#!/bin/bash
# Honors Software Engineering — one-time setup for this repository.
# Run it once, from the top of the repo:  ./setup.sh
set -e
cd "$(dirname "$0")"

echo "==> Python 3.12 and dependencies"
uv python install 3.12
uv sync

echo
echo "==> git filter: strip notebook output before it reaches a commit"
# Without this, one re-run of a notebook shows up as 4,000 changed lines and your
# reviewer cannot see the twelve you actually wrote. The filter rewrites the blob
# on the way into the index; your local file keeps its output. Nothing in this repo
# is a notebook until A11, and the filter has to be in place before the first one is.
git config filter.nbstrip.clean \
  "uv run python -c \"import sys,json; d=json.load(sys.stdin); [c.update(outputs=[],execution_count=None) for c in d['cells'] if c['cell_type']=='code']; json.dump(d,sys.stdout,indent=1); sys.stdout.write('\n')\""
git config filter.nbstrip.smudge cat
git config filter.nbstrip.required true

echo
echo "==> secret guard"
chmod +x scripts/install_secret_guard.sh
./scripts/install_secret_guard.sh

echo
echo "==> environment check"
uv run scripts/check_env.py || true

cat <<'MSG'

Setup done. One thing to verify yourself, because a guard that silently did not
install is worse than no guard:

  Try to commit a fake key and watch it get rejected:

      echo 'sk-test1234567890abcdefghijklmnopqrstuvwxyz' > leak.md
      git add leak.md && git commit -m "should fail"

  Then clean up:  git reset && rm leak.md

  The extension matters. `.gitignore` here ignores `*.txt`, so a `leak.txt` is
  refused by gitignore before the hook ever runs, and you get "paths are ignored"
  instead of "COMMIT BLOCKED" — which tests nothing.

  This is the second repo you have done this in, and the reason is the same one:
  hooks live in .git/hooks/ and do not travel with a clone. The guard you installed
  in the tokenizer repo protects the tokenizer repo and nothing else.

  The notebook filter above has nothing to check yet. A11 is the first assignment
  here with a notebook in it; verify the filter then, with `git diff --stat` after
  running one cell and saving.

MSG
