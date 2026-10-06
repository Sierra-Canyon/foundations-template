# failures/mark.py
# Run from the repo root:
#   uv run python failures/mark.py           prints every answer beside its quote with a blank mark, and writes
#                                            failures/marks.md with one row per question to fill (if it is not there yet)
#   uv run python failures/mark.py counts    after you fill the marks: prints the counts table, the most-fabricated
#                                            question and the most split question
#
# What it does: reads the traces failures/ask.py saved. Without an argument it lays the 200 answers out for
# marking by hand. With "counts" it reads your letters back out of failures/marks.md (r right, f fabricated,
# h hedged, o off) and counts them. There is nothing to edit in this file.
import json, sys
from pathlib import Path

MARKS = {"r": "right", "f": "fabricated", "h": "hedged", "o": "off"}
traces = sorted(Path("failures/traces").glob("q*.json"))     # every trace file, q01 first
qs = []                                                      # one dict per question: id, question, answer, quote, api, gpt2
for p in traces:
    qs.append(json.loads(p.read_text(encoding="utf-8")))
assert qs, "no traces in failures/traces; run failures/ask.py first"   # stops here with that message if there are none

# In: nothing (reads failures/marks.md).  Out: {id: {"api": "rrfrf", "gpt2": "ooofo", "notes": "..."}} from the rows under ## Marks.
def read_marks():
    """ the rows under '## Marks' in failures/marks.md, one dict per question id """
    rows = {}
    inside = False                                           # True while we are under the ## Marks heading
    for line in Path("failures/marks.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            inside = line.strip() == "## Marks"              # a new heading: is it the one we want?
            continue
        if inside and line.startswith("| q"):                # a question row
            cells = []
            for c in line.strip().strip("|").split("|"):     # drop the outer | characters, split on the inner ones
                cells.append(c.strip())                      # and drop the spaces around each cell
            notes = ""
            if len(cells) > 3:
                notes = cells[3]
            rows[cells[0]] = {"api": cells[1], "gpt2": cells[2], "notes": notes}
    return rows

# ------------------------------------------------------------ no argument: lay the answers out, and write the marks file
if sys.argv[1:] == []:
    for q in qs:
        print(f"\n{'=' * 110}\n{q['id']}  {q['question']}\n      answer: {q['answer']}\n      quote:  {q['quote']}")   # '=' * 110 is a rule of 110 = signs
        for model in ("api", "gpt2"):
            for k, run in enumerate(q[model], 1):            # k counts the runs 1 to 5; run is the answer
                if model == "api":
                    text = run["text"]                       # an API run is a dict with the text and the tokens
                else:
                    text = run                               # a GPT-2 run is just the text
                text = " ".join(text.split())                # newlines and double spaces become single spaces
                print(f"  {model:<5} {k}  [ ]  {text[:120]}")   # :<5 pads the model name to 5 characters; [:120] cuts long answers
    out = Path("failures/marks.md")
    if out.exists():
        print("\nfailures/marks.md already exists; left as it is")
    else:
        lines = ["# Marks: <your name>", "",
                 "One letter per run, in run order, r right, f fabricated, h hedged, o off. Replace every dot.", "",
                 "## Marks", "", "| id | API runs 1-5 | GPT-2 runs 1-5 | notes |", "|---|---|---|---|"]
        for q in qs:
            lines.append(f"| {q['id']} | ..... | ..... |  |")   # five dots per model: one per run, to replace with letters
        lines += ["", "## Counts", "", "<paste what `uv run python failures/mark.py counts` prints>", ""]
        out.write_text("\n".join(lines), encoding="utf-8")
        print(f"\nwrote failures/marks.md with {len(qs)} rows to fill")

# ------------------------------------------------------------ "counts": read the letters back and count them
elif sys.argv[1] == "counts":
    rows = read_marks()
    bad = []                                                 # ids whose row is not five letters from r f h o, twice
    for i in rows:
        a, g = rows[i]["api"], rows[i]["gpt2"]
        if len(a) != 5 or len(g) != 5 or set(a + g) - set("rfho"):   # set(...) - set("rfho") is whatever is not one of the four letters
            bad.append(i)
    assert not bad, f"these rows are not five letters from r f h o, twice: {bad}"
    missing = []                                             # questions with no row under ## Marks
    for q in qs:
        if q["id"] not in rows:
            missing.append(q["id"])
    assert not missing, f"no row under ## Marks for {missing}"
    byid = {}                                                # {id: the question dict}, to print questions by id below
    for q in qs:
        byid[q["id"]] = q

    print("| id | API right/5 | API fabricated/5 | API hedged/5 | GPT-2 right/5 | GPT-2 fabricated/5 | notes |")
    print("|---|---|---|---|---|---|---|")
    tot = [0, 0, 0, 0, 0]                                    # running totals of the five count columns
    for i in rows:
        a, g = rows[i]["api"], rows[i]["gpt2"]
        counts = [a.count("r"), a.count("f"), a.count("h"), g.count("r"), g.count("f")]   # .count("r") is how many r letters
        for j in range(5):
            tot[j] += counts[j]
        cells = []
        for c in counts:
            cells.append(str(c))
        print(f"| {i} | " + " | ".join(cells) + f" | {rows[i]['notes']} |")
    n = 5 * len(rows)                                        # runs per model in all: 5 x 20 = 100
    cells = []
    for c in tot:
        cells.append(f"{c}/{n}")
    print(f"| all | " + " | ".join(cells) + " |  |")

    # the most-fabricated question: the most f letters in the API column; on a tie, the lowest id
    most_f = None
    for i in sorted(rows):                                   # sorted, so on a tie the lowest id wins
        if most_f is None or rows[i]["api"].count("f") > rows[most_f]["api"].count("f"):
            most_f = i
    # the most split question: the most different letters across the five API runs; on a tie, the smallest
    # majority (the letter that came up most, came up least often); on a tie again, the lowest id
    def split_score(i):
        """ (how many different letters, minus the size of the biggest group) for question i's API marks: bigger is more split """
        a = rows[i]["api"]
        biggest = 0
        for m in a:
            if a.count(m) > biggest:
                biggest = a.count(m)
        return (len(set(a)), -biggest)
    most_split = None
    for i in sorted(rows):
        if most_split is None or split_score(i) > split_score(most_split):
            most_split = i
    print(f"\nmost-fabricated question (API): {most_f}, fabricated {rows[most_f]['api'].count('f')}/5, marks {rows[most_f]['api']}")
    print(f"   {byid[most_f]['question']}\n   quote: {byid[most_f]['quote']}")
    print(f"most split question (API): {most_split}, marks {rows[most_split]['api']}, {len(set(rows[most_split]['api']))} different marks across 5 runs")
    print(f"   {byid[most_split]['question']}")
    both = []                                                # questions the API got 5/5 and GPT-2 got 0/5
    for i in rows:
        if rows[i]["api"].count("r") == 5 and rows[i]["gpt2"].count("r") == 0:
            both.append(i)
    print(f"API right 5/5 and GPT-2 right 0/5: {len(both)} of {len(rows)} questions {both}")
else:
    print("usage: uv run python failures/mark.py [counts]")
