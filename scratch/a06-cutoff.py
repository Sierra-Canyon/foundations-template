# scratch/a06-cutoff.py
# Tests your predicted cutoff against the twelve top scores of your run, then finds the cutoff
# that would have made the fewest mistakes.
# Run from the repo root:  uv run python scratch/a06-cutoff.py
# Reads the top semantic score of every query from search/run1.txt, lines them up with your
# marks, draws your predicted cutoff on the line, counts the wrong side, then tries every
# distinct score as the cutoff and reports the one with the fewest mistakes.
# Edit the two lines marked EDIT below, MARKS and PREDICTED, and nothing else.
from pathlib import Path

MARKS = "got got got got got got got got got got none none"   # EDIT: one word per query, in the order of queries.txt:
                                                                # got / miss for the ten answerable, none for the two off-corpus
PREDICTED = 0.000                                               # EDIT: the cutoff you committed in E1

marks = MARKS.split()                                                     # the string becomes a list of twelve words
lines = Path("search/run1.txt").read_text(encoding="utf-8").splitlines()  # the run, as a list of lines
queries = []
scores = []
for k, line in enumerate(lines):                 # enumerate gives the line number k and the line together
    if line.startswith("## "):                   # a query heading
        queries.append(line[3:])                 # the text after "## "
        score_line = lines[k + 1]                # the next line is "  sem 0.512 [i] '...'"
        scores.append(float(score_line.split()[1]))   # split on spaces gives ["sem", "0.512", ...]; take the number
assert len(scores) == len(marks) == 12, f"{len(scores)} queries in run1.txt, {len(marks)} marks; both must be 12"   # stops with this message if the counts differ

# In: a cutoff score. Out: the list of queries that sit on the wrong side of it.
def wrong_side(cutoff):
    # A score at or above the cutoff claims "this has an answer". That claim is wrong when the
    # mark is miss or none. A score below the cutoff claims "no good answer", wrong when the mark is got.
    wrong = []
    for q, s, m in zip(queries, scores, marks):  # zip walks the three lists together: a query, its score, its mark
        if s >= cutoff and m != "got":
            wrong.append(q)
        elif s < cutoff and m == "got":
            wrong.append(q)
    return wrong

rows = sorted(zip(scores, marks, queries), reverse=True)   # (score, mark, query) triples, highest score first
above = []                                       # the scores at or above your predicted cutoff, as text like "0.512g"
below = []                                       # the scores under it
for s, m, q in rows:
    label = f"{s:.3f}{m[0]}"                     # the score to 3 decimals, then the first letter of its mark: g, m or n
    if s >= PREDICTED:
        above.append(label)
    else:
        below.append(label)
print("twelve top scores, highest first (g = got, m = miss, n = none), | = your predicted cutoff:")
print(" ", " ".join(above), "|", " ".join(below))   # " ".join puts one space between the items
w = wrong_side(PREDICTED)
print(f"  wrong side of {PREDICTED:.3f}: {len(w)}")
for q in w:
    print("    " + q)

print("\ncutoff      mistakes")
best_cutoff = None
best_count = None
for c in sorted(set(scores)):                    # set() drops duplicate scores; sorted() puts them lowest first
    n = len(wrong_side(c))
    print(f"{c:.3f}   {n:>8}")
    if best_count is None or n < best_count:     # a strict < keeps the first, lowest cutoff when two tie
        best_cutoff = c
        best_count = n
print(f"\nfewest mistakes: cutoff {best_cutoff:.3f} makes {best_count} (set the cutoff at the lowest score that should count as an answer)")
