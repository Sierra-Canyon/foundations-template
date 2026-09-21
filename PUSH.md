# Two commands to put this on GitHub

Run these from inside this folder. Nothing here has touched GitHub yet.

**If you ran `./setup.sh` in here to test it, the guard is now watching this folder and
will block your own commit**, because `setup.sh` and `install_secret_guard.sh` both
contain example key strings. That is the guard working. Commit with `--no-verify` once,
or delete `.git/hooks/pre-commit` before you push the template.

```
gh repo create Sierra-Canyon/foundations-template --private --source=. --push
gh repo edit Sierra-Canyon/foundations-template --template
```

The second one is not optional. Classroom 50 silently produces empty student repos if the
template flag is not set, and it looks like a permissions problem when it is not.

Then make it **public**. Private templates fail at accept time and students get an error
rather than a repo:

```
gh repo edit Sierra-Canyon/foundations-template --visibility public --accept-visibility-change-consequences
./verify-templates.sh Sierra-Canyon foundations-template
```

`verify-templates.sh` lives in `classroom50-setup/` and checks the four things that break at
accept time: exists and not archived, public, template flag on, has a README, and ships no
`.github/workflows/autograde.yml` of its own.

## Then add the assignment

One command, rather than re-running `setup-hse.sh`. That script also creates the classroom
and imports the roster, and you do not want either of those again:

```
gh teacher assignment add Sierra-Canyon hse-2026-2027 foundations \
  --name "Foundations" \
  --description "A05 embeddings, A06 semantic search, A07-A08 the transformer, A09 sampling, A10 failures, A11 evals" \
  --template Sierra-Canyon/foundations-template \
  --due 2026-10-17T05:00:00 \
  --mode individual
```

That due date is A11b's, which is the last thing out of this repo.

Then add the same thing to `setup-hse.sh` so next year's run creates all three. A line in
the `ASSIGNMENTS` array:

```
"foundations|Foundations|$ORG/foundations-template|2026-10-17T05:00:00"
```

and a line in the `case` that sets the description:

```
foundations) a_desc="A05 embeddings, A06 semantic search, A07-A08 the transformer, A09 sampling, A10 failures, A11 evals" ;;
```

Finally, publish the assignment in Classroom 50 and check the accept link it gives you
matches the one A05 Step 1 already prints:

```
https://classroom50.org/Sierra-Canyon/hse-2026-2027/assignments/foundations/accept
```

Repos land as `<classroom>-<assignment>-<username>`, all lowercase, so each student gets
`hse-2026-2027-foundations-<their-handle>`. A05 Step 1 already links
`https://classroom50.org/Sierra-Canyon/hse-2026-2027/assignments/foundations/accept`, so
the slug has to be exactly `foundations`.

## What a student gets

Directory scaffolding for A05 through A11b, each directory carrying a README that states
the deliverable and the common mistake, plus `setup.sh`, the secret guard and the
environment check.

**No starter code.** Unlike `tokenizer-template` there is no skeleton with
`NotImplementedError` in it, because none of these assignments is test-driven: A05 and A06
are judged on numbers the student produces and explains, not on a suite going green. If you
later want a skeleton for `embed/probe.py`, that is a change to the assignment as well as to
the template, since A05 currently says "write `embed/probe.py`" with no file to open.

**NumPy is deliberately absent from `pyproject.toml`.** A05 Step 3 has students run
`uv add numpy` themselves, and shipping it would make that step a no-op. `jupyterlab` is
there because A11 has notebooks.

## Differences from tokenizer-template

| | tokenizer-template | this |
|---|---|---|
| Starter code | `bpe/tokenizer.py`, seven `NotImplementedError`s | none |
| Tests | 68, mutation-tested | none, nothing here is test-driven |
| Notebooks | two, from day one | none until A11 |
| `*.npy` | ignored | ignored except `embed/vecs.npy` and `embed/words.npy` |
| Python pin | `>=3.12,<3.13`, for tiktoken wheels | `>=3.12`, no tiktoken here |
| NumPy | shipped | added by the student in A05 |
