# scratch/a09-mark.py
# Run from the repo root:  uv run python scratch/a09-mark.py
#
# What it does: reads sampling/table.txt (what "lab.py table" printed) and evidence/A09.md (the prediction
# table under "## Prediction"), and prints the nine rows of the X3 table with the "distinct of 5" and
# "predicted distinct" columns filled. You paste that table under "## Extension X3" in evidence/A09.md and
# fill "usable of 5" by reading sampling/table.txt. Run it again after the usable column is filled and it
# also prints, per prompt, the lowest temperature at which usable fell below 5.
#
# There is nothing to edit in this file.
from pathlib import Path

# ------------------------------------------------------------ read the nine headings out of table.txt
# Each heading looks like:  ## prompt 1  T=0.7  distinct 5 of 5  ends 'Hector hurried from '
lines = Path("sampling/table.txt").read_text(encoding="utf-8").splitlines()
blocks = []                                   # one dict per heading: prompt number, temperature, distinct count, the prompt's tail
for line in lines:
    if line.startswith("## prompt "):
        parts = line.split()                  # split on spaces: ['##', 'prompt', '1', 'T=0.7', 'distinct', '5', 'of', '5', 'ends', "'Hector", ...]
        blocks.append({
            "prompt": int(parts[2]),                        # '1' -> 1
            "T": float(parts[3][2:]),                       # 'T=0.7' -> the characters after 'T=' -> 0.7
            "distinct": int(parts[5]),                      # '5' -> 5
            "tail": line.split("ends ", 1)[1],              # everything after the first 'ends ': the quoted end of the prompt
        })
assert len(blocks) == 9, f"{len(blocks)} '## prompt' headings in sampling/table.txt; the table run prints 9 (3 prompts x 3 temperatures)"

# ------------------------------------------------------------ read evidence/A09.md, if it is there
evidence = Path("evidence/A09.md")
if evidence.exists():
    text = evidence.read_text(encoding="utf-8")
else:
    text = ""                                 # no file: every prediction reads ? and no usable cell is found

# In: the start of a heading, such as "## Prediction".  Out: a list of rows, each row a list of its cells as strings,
# from the table under the "## " heading that starts with those words (the rest of the heading can say anything).
def table_after(heading):
    """ the cells of every '| ... |' row under a '## heading', up to the next '## ' """
    rows = []
    inside = False                            # True while we are under the heading we want
    for line in text.splitlines():
        if line.startswith("## "):
            inside = line.strip().lower().startswith(heading.lower())   # a new heading: are we in the right section now?
            continue
        if inside and line.startswith("|") and not line.startswith("|---"):   # a table row, but not the |---|---| rule
            cells = []
            for c in line.strip().strip("|").split("|"):    # drop the outer | characters, split on the inner ones
                cells.append(c.strip())                     # and drop the spaces around each cell
            rows.append(cells)
    return rows

# the predictions: {(prompt number, T): what you predicted}, from the three rows of the Prediction table
predicted = {}
for cells in table_after("## Prediction"):
    if cells[0] in ("1", "2", "3") and len(cells) >= 5:
        last_three = cells[-3:]               # the T=0, T=0.7 and T=1.2 cells, in that order
        temps = (0, 0.7, 1.2)
        for j in range(3):
            cell = last_three[j]
            if cell.isdigit():                # a plain number
                predicted[(int(cells[0]), temps[j])] = cell
            else:                             # anything else (empty, the unfilled <   > cell, a word): shown as ?
                predicted[(int(cells[0]), temps[j])] = "?"

# the usable counts you filled in: {(prompt number, T): count}, from the rows under ## Extension X3
usable = {}
for cells in table_after("## Extension X3"):
    if len(cells) >= 4 and cells[0] in ("1", "2", "3") and cells[3].isdigit():
        usable[(int(cells[0]), float(cells[1]))] = int(cells[3])

# ------------------------------------------------------------ the X3 table
print("| prompt | T | distinct of 5 | usable of 5 | predicted distinct |")
print("|---|---|---|---|---|")
for b in blocks:
    key = (b["prompt"], b["T"])
    print(f"| {b['prompt']} | {b['T']:g} | {b['distinct']} | {usable.get(key, '')} | {predicted.get(key, '?')} |")   # :g prints 0.0 as 0; .get gives '' or ? when a cell is missing

missing = 0                                   # how many of the nine rows have no prediction
for b in blocks:
    if (b["prompt"], b["T"]) not in predicted:
        missing += 1
if missing:
    print(f"\n{missing} predicted cells read '?': the Prediction table in evidence/A09.md has no number there yet")

print("\nprompts, as the table run cut them:")
tails = {}                                    # {prompt number: its tail}; the same prompt appears in three blocks, so this keeps one
for b in blocks:
    tails[b["prompt"]] = b["tail"]
for k in sorted(tails):
    print(f"  prompt {k} ends {tails[k]}")

# ------------------------------------------------------------ the where-it-got-worse lines, once all nine usable cells are filled
if len(usable) == 9:
    print("\nwhere it got worse (first temperature at which usable fell below 5):")
    for k in (1, 2, 3):
        first_worse = None                    # the lowest temperature at which usable was under 5, if any
        for t in (0, 0.7, 1.2):
            if usable[(k, t)] < 5 and first_worse is None:
                first_worse = t
        if first_worse is None:
            print(f"  prompt {k}: never; usable 5 of 5 at every temperature")
        else:
            print(f"  prompt {k}: T={first_worse:g}, usable {usable[(k, first_worse)]} of 5")
    total_distinct = 0
    for b in blocks:
        total_distinct += b["distinct"]
    print(f"  usable in all: {sum(usable.values())} of 45; distinct in all: {total_distinct} of 45")
elif usable:
    print(f"\n{len(usable)} of 9 usable cells filled under ## Extension X3; fill the rest and run again for the where-it-got-worse lines")
else:
    print("\nnext: paste the table above into evidence/A09.md under ## Extension X3, fill usable of 5 by reading sampling/table.txt, run this again")
