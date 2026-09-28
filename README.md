# Foundations — Honors Software Engineering

**Section C-JD · Period C · Room U 108 · 2026–27**

One repository per project. This is the second of four, and it carries A05 through A11b:
embeddings, semantic search, the transformer, sampling, the failure catalogue and evals.
The tokenizer lives in its own repo and stays there; the GPT build and the capstone each
get their own later.

That means the setup you do here is setup you have done before. Git hooks live in
`.git/hooks/` and do not travel with a clone, so the secret guard you installed in the
tokenizer repo protects the tokenizer repo and nothing else. Every project template ships
its own `setup.sh` for exactly that reason.

---

## First run

```
./setup.sh
```

That installs Python 3.12, installs a git filter so notebook output never reaches a commit,
installs the secret guard, and runs the environment check. It ends by asking you to try
committing a fake key and watch it get refused. Do that. A guard that silently failed to
install is worse than no guard, because you find out when it is already too late.

If `./setup.sh` says `uv: command not found`, you skipped A01's first line:

```
brew install uv nvm
```

## NumPy is not installed yet, on purpose

```
uv add numpy
```

A05 has you run that yourself. `uv add` writes the dependency into `pyproject.toml`, so the
next person to clone this repo gets it too; `pip install` puts it in a directory and tells
nobody. That difference is the reason this repo ships without it.

Run your code with `uv run`, not plain `python`:

```
uv run python embed/probe.py
```

`uv run` uses the `.venv` this repo built, which is where `uv add` put NumPy. Plain `python`
uses whatever is first on your PATH and will not find it. The symptom is
`ModuleNotFoundError: No module named 'numpy'` on a package you just watched install.

## What is where

| Path | What |
|---|---|
| `embed/` | **A05.** `probe.py`, the saved vectors, `FINDINGS.md`. |
| `search/` | **A06.** `search.py` and `RESULTS.md`. |
| `transformer/` | **A07** `block.png` and **A08** `attention.md`. |
| `sampling/` | **A09.** `lab.py` and `RESULTS.md`. |
| `failures/` | **A10.** `CATALOG.md` and `traces/`. |
| `evals/` | **A11.** Labs, judge labels, `JUDGE_REPORT.md`. |
| `SELF_Q1.md` | **A11b.** You create this one at the top of the repo. |
| `data/` | **A05b.** Your corpus. Git-ignored on purpose, except `SOURCE.md` and `titles.txt`. |
| `Choosing a Corpus.md` | **A05b.** Sources by subject, each with the command that fetches it. Read it before you pick. |
| `scripts/check_corpus.py` | **A05b.** The corpus checker; `uv run pytest tests/` runs the same checks. |
| `logs/LOG_TEMPLATE.md` | The shape of a log entry. The entries themselves live in your log repo. |
| `scripts/check_env.py` | The environment check. Re-run it whenever something breaks. |
| `scripts/install_secret_guard.sh` | Pre-commit hook that refuses staged keys. |

Every directory above has a README saying what the deliverable is and what the common
mistake is. Read the one for the assignment you are on before you start it.

## Two files here are committed rather than ignored

`embed/vecs.npy` and `embed/words.npy`. Everything else matching `*.npy` is ignored, and
so is everything in `data/`.

The reason is A06: it builds on exactly the vectors A05 produced, and I re-run your numbers
against them. Re-embedding on every run burns your spend cap, and the cap does not warn you
before it stops you. Embed once, save, load from disk after that.

## This repo calls an API, which the tokenizer repo never did

A05 is the first assignment that spends money. Three rules:

**Never enter a personal credit card** for any service this course uses. If something asks
for one, stop and come to me. Class keys are provisioned with hard caps and you never touch
billing.

**Never commit a key.** The secret guard blocks the obvious shapes. It is not a substitute
for knowing where your key is. If you ever push one, tell me the same day: there is no
penalty for reporting it and rotating it, and concealing it is a different conversation.

**Batch your calls.** The embeddings endpoint takes a list. Three hundred separate requests
are slow, will trip rate limits, and cost the same as one.

## Rules that apply in every repo you open this year

**Branches.** `dev/<feature>` for work, and the log branch that has been open since A03
stays open until the track election. One pull request per assignment, and the PR body says
where the work is weakest.

**AI is allowed, and you say so.** Every log entry carries an `AI use:` line. Using it costs
you nothing. Not saying so is the only version that is a problem.
