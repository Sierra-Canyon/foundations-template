# scratch/a08-table.py
# Run from the repo root:  uv run python scratch/a08-table.py
#
# What it does: reads the five runs in transformer/head_runs.txt (written by X2's for loop)
# and prints the X2 table for the "## Extension X2" section of evidence/A08.md.
#
# Run it once with the two slots below empty: it prints every token with its position.
# Fill the slots from that list, run it again, and it prints the table, the summary line,
# and the pronoun's row from seed 1 with its labels.
#
# The two lines you edit are PRONOUN_POS and REFERENT_POSITIONS. Nothing else.
from pathlib import Path

PRONOUN_POS = None             # position of your pronoun token, counting from 0; e.g. 18
REFERENT_POSITIONS = []        # position(s) of the referent's token(s), e.g. [1] or [5, 6, 7]

# ------------------------------------------------------------ read the file back into numbers
# head_on_corpus.py prints, per run: a "T=... seed=..." line, a header line of column labels,
# then T grid rows (a 9-character label, a space, then T weights 7 characters wide each),
# then a "row sums:" line. This loop walks the file and pulls each run apart.
text = Path("transformer/head_runs.txt").read_text(encoding="utf-8").splitlines()
runs = []                                                   # one dict per run: its seed, its labels, its grid
i = 0
while i < len(text):
    if text[i].startswith("T="):                            # the first line of a run
        T = int(text[i].split()[0][2:])                     # "T=23" -> the characters after "T=" -> 23
        seed = int(text[i].split()[1][5:])                  # "seed=1" -> the characters after "seed=" -> 1
        header = text[i + 1]                                # the column labels, one per token, 7 characters each
        labels = []
        for c in range(T):
            start = 10 + 7 * c                              # the header has 10 leading spaces, then 7 characters per label
            labels.append(header[start:start + 7].strip())  # cut out that label and drop its padding spaces
        grid = []                                           # grid[r] is row r of the weights, as floats
        for r in range(T):
            line = text[i + 2 + r]                          # row r sits 2 lines below the "T=" line
            weights = []
            for w in line[10:].split():                     # skip the 9-character label and its space, then split on spaces
                weights.append(float(w))
            grid.append(weights)
        runs.append({"seed": seed, "labels": labels, "grid": grid})
        i += 2 + T                                          # jump past this run's header and grid
    i += 1
assert runs, "transformer/head_runs.txt is empty or not in head_on_corpus.py's format"   # stops here with that message if nothing was read
seed0 = runs[0]["seed"]
labels = runs[0]["labels"]
grid0 = runs[0]["grid"]

# ------------------------------------------------------------ first run: just list the positions
if PRONOUN_POS is None or REFERENT_POSITIONS == []:
    print(f"{len(runs)} runs of T={len(labels)} tokens. Positions, counting from 0:")
    for p in range(len(labels)):
        print(f"{p:>3}  {labels[p]}")                       # :>3 right-aligns the number in 3 columns
    print("\nPut the pronoun's position in PRONOUN_POS and the referent's position(s) in REFERENT_POSITIONS, then run again.")
    raise SystemExit                                        # stop the script here

# ------------------------------------------------------------ second run: the table
p = PRONOUN_POS
n = len(REFERENT_POSITIONS)                                 # how many tokens the referent is
for r in REFERENT_POSITIONS:
    assert r < p, "the referent has to come before the pronoun, or the mask hides it"
even_one = 1 / (p + 1)                 # a head that spreads its budget evenly gives each visible token this much
even = n * even_one                    # and the referent, over its n tokens, this much
referent_labels = []
for r in REFERENT_POSITIONS:
    referent_labels.append(labels[r])
print(f"pronoun '{labels[p]}' at {p}: {p + 1} tokens visible, even share {even_one:.4f} each, {even:.4f} on the referent ({n} token(s): {referent_labels})\n")

print("| seed | weight on referent | even share | ratio | biggest weight in the row, and which token |")
print("|---|---|---|---|---|")
weights = []                                                # the referent's weight in each run, for the summary line
for run in runs:
    row = run["grid"][p][: p + 1]                           # the pronoun's row, visible cells only (positions 0 to p)
    w = 0
    for r in REFERENT_POSITIONS:                            # add up the referent's columns
        w += row[r]
    big = 0                                                 # find the position with the biggest weight in the row
    for c in range(p + 1):
        if row[c] > row[big]:
            big = c
    weights.append(w)
    print(f"| {run['seed']} | {w:.2f} | {even:.4f} | {w / even:.2f} | {row[big]:.2f} on '{run['labels'][big]}' (position {big}) |")

below = 0                                                   # how many runs put less than the even share on the referent
for w in weights:
    if w < even:
        below += 1
print(f"\nmean {sum(weights) / len(weights):.3f}   range {min(weights):.2f} to {max(weights):.2f}   seeds below the even share: {below} of {len(weights)}")

# ------------------------------------------------------------ the pronoun's row from the first run, for Reflection 1
print(f"\nseed {seed0}, the pronoun's row with its column labels (visible tokens only):")
header = " " * 9                                            # 9 spaces, the width of the row label below
for l in labels[: p + 1]:                                   # the visible tokens' labels
    header += f"{l[:6]:>7}"                                 # the first 6 characters of the label, right-aligned in 7 columns
print(header)
line = f"{labels[p][:8]:>8} "                               # the pronoun's label, right-aligned in 8 columns, then a space
for w in grid0[p][: p + 1]:
    line += f"{w:7.2f}"                                     # each weight with 2 decimals in 7 columns
print(line)
