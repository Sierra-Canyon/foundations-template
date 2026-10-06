# failures/mark.py
# Run from the repo root:
#   uv run python failures/mark.py           prints every answer beside its quote with a blank mark, and fills the
#                                            table under ## Marks in evidence/A10.md with one row per question
#                                            for you to fill (if the rows are not there yet)
#   uv run python failures/mark.py counts    after you fill the marks: prints the counts table, the most-fabricated
#                                            question and the most split question
#
# What it does: reads the traces failures/ask.py saved. Without an argument it lays the 200 answers out for
# marking by hand. With "counts" it reads your letters back out of the ## Marks table in evidence/A10.md
# (r right, f fabricated, h hedged, o off) and counts them. The script only ever touches the lines under
# ## Marks; the rest of evidence/A10.md is yours. There is nothing to edit in this file.
import json, sys
from pathlib import Path

MARKS = {"r": "right", "f": "fabricated", "h": "hedged", "o": "off"}
EVIDENCE = Path("evidence/A10.md")                           # the file that holds the ## Marks table
traces = sorted(Path("failures/traces").glob("q*.json"))     # every trace file, q01 first
qs = []                                                      # one dict per question: id, question, answer, quote, api, gpt2
for p in traces:
    qs.append(json.loads(p.read_text(encoding="utf-8")))
assert qs, "no traces in failures/traces; run failures/ask.py first"   # stops here with that message if there are none

# In: nothing (reads evidence/A10.md).  Out: {id: {"api": "rrfrf", "gpt2": "ooofo", "notes": "..."}} from the rows under ## Marks.
def read_marks():
    """ the rows under '## Marks' in evidence/A10.md, one dict per question id """
    rows = {}
    inside = False                                           # True while we are under the ## Marks heading
    for line in EVIDENCE.read_text(encoding="utf-8").splitlines():
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

# In: the lines of evidence/A10.md, as a list.  Out: (first, last): the index of the "## Marks" heading and the
# index of the next "## " heading (or the end of the file), so lines[first + 1:last] is the Marks section.
def marks_section(lines):
    first = None                                             # where "## Marks" is, once found
    last = len(lines)                                        # where the next section starts; the end of the file if there is none
    for k, line in enumerate(lines):                         # k counts the lines from 0; line is the text
        if first is None:
            if line.strip() == "## Marks":
                first = k
        elif line.startswith("## "):                         # the first heading after ## Marks ends the section
            last = k
            break
    return first, last

# In: nothing (reads and writes evidence/A10.md).  Out: nothing; prints what it did.
# Puts one "| q01 | ..... | ..... |  |" row per question under ## Marks, in place of the slot line the
# template left there, unless rows are there already. Every other line of the file is written back unchanged.
def write_rows():
    if not EVIDENCE.exists():
        print(f"\n{EVIDENCE} not found; run this from the repo root, and merge main if evidence/ is missing")
        return
    lines = EVIDENCE.read_text(encoding="utf-8").split("\n")   # split on newlines, keeping a last empty item if the file ends with one
    first, last = marks_section(lines)
    if first is None:
        print(f"\nno ## Marks heading in {EVIDENCE}; put one back (the template has it) and run again")
        return
    for line in lines[first + 1:last]:
        if line.startswith("| q"):                           # a question row is already there
            print(f"\nrows already under ## Marks in {EVIDENCE}; left as they are")
            return
    rows = []
    for q in qs:
        rows.append(f"| {q['id']} | ..... | ..... |  |")     # five dots per model: one per run, to replace with letters
    slot = None                                              # the template's slot line under ## Marks, once found
    header = None                                            # the table's |---| line, in case the slot line is gone
    for k in range(first + 1, last):
        if "<paste:" in lines[k] and slot is None:
            slot = k
        if lines[k].startswith("|---"):
            header = k
    if slot is not None:
        lines[slot:slot + 1] = rows                          # slice assignment: the one line at slot comes out, all the rows go in
    elif header is not None:
        lines[header + 1:header + 1] = rows                  # no slot line: an empty slice, so the rows are inserted right after the table header
    else:
        lines[first + 1:first + 1] = ["", "| id | API runs 1-5 | GPT-2 runs 1-5 | notes |", "|---|---|---|---|"] + rows   # no table at all: header and rows
    EVIDENCE.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nwrote {len(qs)} rows to fill under ## Marks in {EVIDENCE}")

# ------------------------------------------------------------ no argument: lay the answers out, and write the marks rows
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
    write_rows()

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
