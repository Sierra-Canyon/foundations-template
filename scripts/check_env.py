#!/usr/bin/env python3
"""
Honors Software Engineering — Week 1 environment check.

Run:  uv run check_env.py     (A01 gives you uv first; plain python3 also works)
It checks, it does not install. Every FAIL prints what to do about it.
Works on Mac, Linux and Windows (run it from Git Bash on Windows).
"""
import os, shutil, subprocess, sys, json

OK, WARN, FAIL = "PASS", "WARN", "FAIL"
results = []

def record(name, status, detail, fix=""):
    results.append((name, status, detail, fix))

def run(cmd):
    try:
        # Windows shims (nvm-windows, fnm, volta) are .cmd files, which only run through the shell.
        use_shell = sys.platform.startswith("win") and str(cmd[0]).lower().endswith((".cmd", ".bat"))
        p = subprocess.run(" ".join(f'"{c}"' for c in cmd) if use_shell else cmd,
                           capture_output=True, text=True, timeout=20, shell=use_shell)
        return (p.stdout + p.stderr).strip()
    except Exception as e:
        return f"__ERR__ {e}"

def version_tuple(s):
    nums, cur = [], ""
    for ch in s:
        if ch.isdigit():
            cur += ch
        elif cur:
            nums.append(int(cur)); cur = ""
            if len(nums) == 3: break
    if cur: nums.append(int(cur))
    return tuple(nums + [0, 0, 0])[:3]

# ---- Python
pv = sys.version_info
record("Python >= 3.12",
       OK if (pv.major, pv.minor) >= (3, 12) else FAIL,
       f"found {pv.major}.{pv.minor}.{pv.micro}",
       ("winget install astral-sh.uv, then `uv python install 3.12`" if sys.platform.startswith("win") else "brew install uv, then `uv python install 3.12`."))

# ---- Node
# Windows: node is node.exe, and nvm-windows / fnm / a plain installer each put it somewhere
# different. Look on PATH first, then in the places those installers use, so a student whose
# terminal has not picked up the new PATH yet gets "installed but not on PATH" instead of
# "not found", which is a different fix.
WIN = sys.platform.startswith("win")
NODE_FIX = ("Install Node 22 LTS: `winget install OpenJS.NodeJS.LTS` (or nvm-windows: `nvm install 22 && nvm use 22`), "
            "then close this terminal and open a new Git Bash. A terminal only learns about new commands when it starts."
            if WIN else
            "Install Node 22 LTS. `nvm install 22 && nvm use 22` if you have nvm, then open a new terminal.")

def find_node():
    """Returns (path, on_path). Searches PATH, then installer locations."""
    for name in ("node", "node.exe"):
        p = shutil.which(name)
        if p:
            return p, True
    import glob
    candidates = []
    if WIN:
        for base in (os.environ.get("NVM_SYMLINK"), os.environ.get("ProgramFiles"),
                     os.environ.get("ProgramFiles(x86)"), os.environ.get("LOCALAPPDATA")):
            if base:
                candidates += [os.path.join(base, "nodejs", "node.exe"), os.path.join(base, "node.exe"),
                               os.path.join(base, "Programs", "nodejs", "node.exe")]
        for base in (os.environ.get("NVM_HOME"), os.path.join(os.environ.get("APPDATA", ""), "nvm"),
                     os.path.join(os.environ.get("LOCALAPPDATA", ""), "fnm_multishells"),
                     os.path.join(os.environ.get("APPDATA", ""), "fnm", "node-versions")):
            if base:
                candidates += glob.glob(os.path.join(base, "*", "node.exe"))
                candidates += glob.glob(os.path.join(base, "*", "installation", "node.exe"))
    else:
        home = os.path.expanduser("~")
        candidates += glob.glob(os.path.join(os.environ.get("NVM_DIR") or os.path.join(home, ".nvm"),
                                             "versions", "node", "*", "bin", "node"))
        candidates += glob.glob(os.path.join(home, ".local", "share", "fnm", "node-versions", "*", "installation", "bin", "node"))
        candidates += ["/opt/homebrew/bin/node", "/usr/local/bin/node", os.path.join(home, ".volta", "bin", "node")]
    found = [c for c in candidates if c and os.path.isfile(c)]
    return (sorted(found)[-1], False) if found else (None, False)

node_path, node_on_path = find_node()
if node_path:
    out = run([node_path, "--version"])
    ok_ver = version_tuple(out) >= (22, 0, 0)
    if ok_ver and node_on_path:
        record("Node >= 22", OK, f"found {out}")
    elif ok_ver:
        record("Node >= 22", WARN, f"{out} at {node_path}, but `node` is not on PATH in this terminal",
               "Close this terminal and open a new one. If it is still missing, the installer did not update PATH: "
               + ("on Windows, System Properties -> Environment Variables -> Path -> add the folder above, then reopen Git Bash."
                  if WIN else "add the folder above to your PATH in ~/.bash_profile and reopen the terminal."))
    else:
        record("Node >= 22", FAIL, f"found {out} at {node_path}", NODE_FIX)
else:
    record("Node >= 22", FAIL, "node not found on PATH or in the usual install folders", NODE_FIX)

# ---- git
if shutil.which("git"):
    record("git", OK, run(["git", "--version"]))
    name = run(["git", "config", "--global", "user.name"])
    email = run(["git", "config", "--global", "user.email"])
    record("git identity configured",
           OK if name and email and "__ERR__" not in name else FAIL,
           f"name={name or '(unset)'} email={email or '(unset)'}",
           'git config --global user.name "Your Name" && git config --global user.email "you@example.com"')
else:
    record("git", FAIL, "git not found", "Install git.")

# ---- Go + Boot.dev CLI. Not needed until A13 (Mon 26 Oct), so these WARN in
# ---- September and only matter once Track A starts submitting lessons.
if shutil.which("go"):
    record("Go toolchain", OK, run(["go", "version"]))
else:
    record("Go toolchain", WARN, "not installed (not needed until A13)",
           "A13 tells you to: brew install go")

if shutil.which("bootdev"):
    record("Boot.dev CLI", OK, run(["bootdev", "--version"]))
else:
    record("Boot.dev CLI", WARN, "not installed (not needed until A13)",
           "A13 tells you to: go install github.com/bootdotdev/bootdev@latest, then bootdev login. "
           "If it is still not found, $(go env GOPATH)/bin is not on your PATH.")

# ---- uv (required: A01 launches this script with `uv run`, and A04/A05 use `uv add`)
record("uv (Python toolchain)",
       OK if shutil.which("uv") else FAIL,
       run(["uv", "--version"]) if shutil.which("uv") else "not found on PATH",
       "winget install astral-sh.uv, then open a new Git Bash" if sys.platform.startswith("win") else "brew install uv")

# ---- a Node version manager. On Mac it is nvm and it is required (it is how you keep Node 22
# ---- across terminals). On Windows nvm-windows, fnm or a plain installer all work, so a
# ---- missing manager is a WARN there as long as Node 22 itself was found.
nvm_dir = os.environ.get("NVM_DIR") or os.path.expanduser("~/.nvm")
win_managers = [d for d in (os.environ.get("NVM_HOME"),
                            os.path.join(os.environ.get("APPDATA", ""), "nvm"),
                            os.path.join(os.environ.get("APPDATA", ""), "fnm"),
                            os.path.join(os.environ.get("LOCALAPPDATA", ""), "fnm_multishells"))
                if d and os.path.isdir(d)]
if WIN:
    if win_managers:
        record("Node version manager", OK, f"found {win_managers[0]}")
    else:
        record("Node version manager", WARN if node_path else FAIL, "no nvm-windows or fnm found",
               "Optional on Windows if Node 22 is installed. nvm-windows (github.com/coreybutler/nvm-windows) "
               "lets you switch versions later; install it before you need a second version, not after.")
else:
    record("nvm (Node version manager)",
           OK if os.path.isdir(nvm_dir) else FAIL,
           nvm_dir if os.path.isdir(nvm_dir) else "not found",
           "brew install nvm, then add the two lines brew prints to your ~/.bash_profile and open a "
           "NEW terminal. nvm is a shell function, so `which nvm` finds nothing even when it works.")

# ---- API key
key = os.environ.get("CLASS_API_KEY") or os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
if key:
    masked = key[:6] + "..." + key[-4:] if len(key) > 12 else "(short)"
    record("Model API key in environment", OK, f"found, {masked}")
else:
    record("Model API key in environment", FAIL, "no CLASS_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY",
           "Add the class key your instructor gave you to your shell profile. Never paste a personal card into any of these services.")

# ---- key actually works (one cheap call)
if key:
    try:
        import urllib.request, urllib.error
        req = urllib.request.Request(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=15) as r:
            n = len(json.loads(r.read()).get("data", []))
        record("API key authenticates", OK, f"server returned {n} models")
    except urllib.error.HTTPError as e:
        record("API key authenticates", FAIL, f"HTTP {e.code}",
               "401 means the key is wrong or revoked. 429 means you are rate-limited or over your cap — talk to your instructor, do not add a personal card.")
    except Exception as e:
        record("API key authenticates", WARN, f"could not reach the API ({type(e).__name__})",
               "Check the school network. This may be a proxy issue rather than a key issue.")

# ---- your agent repo
here = os.getcwd()
has_git = os.path.isdir(os.path.join(here, ".git"))
record("Running inside a git repository", OK if has_git else WARN,
       here if has_git else f"{here} is not a git repo",
       "Run this from the top of the repository, not from inside scripts/.")

# ---- report
width = max(len(r[0]) for r in results) + 2
print("\n" + "=" * 68)
print("  HONORS SWE — WEEK 1 ENVIRONMENT CHECK")
print("=" * 68)
fails = 0
for name, status, detail, fix in results:
    mark = {OK: "  ok  ", WARN: " warn ", FAIL: " FAIL "}[status]
    print(f"[{mark}] {name.ljust(width)} {detail}")
    if status == FAIL:
        fails += 1
        if fix: print(f"{' ' * (width + 10)}-> {fix}")
    elif status == WARN and fix:
        print(f"{' ' * (width + 10)}-> {fix}")
print("=" * 68)
print(f"  {fails} blocking problem(s).", "You are set up." if fails == 0 else "Fix the FAILs, then re-run.")
print("=" * 68 + "\n")
sys.exit(1 if fails else 0)
