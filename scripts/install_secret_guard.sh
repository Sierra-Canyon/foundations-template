#!/usr/bin/env bash
# Students run this ONCE, inside their repo, in Week 1 Meeting 2.
# It makes committing a key hard instead of easy.
#
# git remembers everything. A key pushed and then "deleted" in a later commit is
# still in the history, still scrapeable, and still live. Bots scan public GitHub
# for key patterns within seconds of a push. Prevention is the only cure.
set -euo pipefail
git rev-parse --git-dir >/dev/null 2>&1 || { echo "Run this inside your repo."; exit 1; }
ROOT=$(git rev-parse --show-toplevel)
cd "$ROOT"

# 1. ignore the usual suspects
for pat in ".env" ".env.*" "!.env.example" "*.key" "secrets.json" "students_keys.csv" "openrouter_keys.csv"; do
  grep -qxF "$pat" .gitignore 2>/dev/null || echo "$pat" >> .gitignore
done
echo "  .gitignore updated"

# 2. pre-commit hook that refuses staged secrets
mkdir -p .git/hooks
cat > .git/hooks/pre-commit <<'HOOK'
#!/usr/bin/env bash
# Blocks a commit containing anything shaped like an API key.
PATTERNS='sk-or-v1-[A-Za-z0-9]{20,}|sk-svcacct-[A-Za-z0-9_-]{20,}|sk-proj-[A-Za-z0-9_-]{20,}|sk-admin-[A-Za-z0-9_-]{20,}|sk-ant-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{35}|sk-[A-Za-z0-9]{32,}'
hits=$(git diff --cached --no-color -U0 | grep -E '^\+' | grep -Ein "$PATTERNS" || true)
if [ -n "$hits" ]; then
  echo
  echo "  COMMIT BLOCKED — this looks like an API key:"
  echo "$hits" | head -5 | sed 's/^/    /'
  echo
  echo "  Move it to .env and read it with an environment variable."
  echo "  If this is genuinely a false positive:  git commit --no-verify"
  echo "  If you already PUSHED a real key: revoke it now, then tell your instructor."
  echo "  Rotating a leaked key takes 30 seconds. Not rotating it can cost real money."
  echo
  exit 1
fi
HOOK
chmod +x .git/hooks/pre-commit
echo "  pre-commit hook installed"

# 3. tell them if it is already too late
echo "  scanning existing history ..."
if git grep -InE 'sk-or-v1-[A-Za-z0-9]{20,}|sk-svcacct-|sk-proj-[A-Za-z0-9_-]{20,}|sk-ant-|AIza[0-9A-Za-z_-]{35}' \
     $(git rev-list --all 2>/dev/null | head -200) -- 2>/dev/null | head -5; then
  echo
  echo "  ^ If anything printed above, a key is IN YOUR HISTORY."
  echo "    Revoke that key immediately, then tell your instructor. Do not try to"
  echo "    rewrite history first — revoke first, clean up second."
else
  echo "  history looks clean"
fi
echo
echo "  Done. Test it:  echo 'sk-or-v1-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' > leak.md"
echo "                  git add leak.md && git commit -m test"
echo "  It should refuse. Then: git reset && rm leak.md"
echo "  Use .md, not .txt: .gitignore ignores *.txt, so a leak.txt never reaches the hook."
echo
