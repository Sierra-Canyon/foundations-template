# scripts/check_evidence.py
# Lists the slots in an evidence file that you have not filled yet.
# Run from the repo root:  uv run python scripts/check_evidence.py A06
# Reads evidence/A06.md (or whichever assignment you name), prints every line that still holds a
# slot, with its line number, and ends with "N slots still empty" or "all slots filled".
# A slot is "<paste:" or "<answer:" (the text inside the angle brackets says what goes there) or an
# empty table cell "<   >" (angle brackets with nothing but spaces between them).
# Nothing to edit in this file. The exit code is 0 either way; the last line is the verdict.
import sys
from pathlib import Path

# In: one line of the file. Out: how many empty table cells like "<   >" it holds.
def count_blank_cells(line):
    count = 0
    start = line.find("<")                       # position of the first "<", or -1 if there is none
    while start != -1:
        end = line.find(">", start + 1)          # the next ">" after that "<"
        if end == -1:                            # no closing bracket: nothing more to count on this line
            break
        inside = line[start + 1:end]             # the text between the brackets
        if inside != "" and inside.strip() == "":   # at least one character, and all of them spaces
            count += 1
        start = line.find("<", end + 1)          # look for the next "<" after this cell
    return count

# In: one line of the file. Out: how many unfilled slots of any kind it holds.
def count_slots(line):
    pastes = line.count("<paste:") - line.count("<paste: ...>")        # "<paste: ...>" is the example in the file's header, not a slot
    answers = line.count("<answer:") - line.count("<answer: ...>")     # same for "<answer: ...>"
    return pastes + answers + count_blank_cells(line)

# In: the assignment name from the command line, like A06, A06.md or evidence/A06.md.
# Out: the path of the evidence file, evidence/A06.md.
def evidence_path(name):
    name = name.replace("\\", "/")               # Windows paths use backslashes; make them forward slashes
    if "/" in name:
        name = name.split("/")[-1]               # keep only the part after the last slash
    if name.endswith(".md"):
        name = name[:-3]                         # drop the ".md" so it is not added twice below
    return Path("evidence") / (name + ".md")

if len(sys.argv) != 2:                           # sys.argv is the command line: [script, assignment]
    print("usage: uv run python scripts/check_evidence.py A06")
    sys.exit(0)

path = evidence_path(sys.argv[1])
if not path.exists():
    print(f"{path} not found; run this from the repo root, and check the assignment name")
    sys.exit(0)

empty = 0                                        # slots found so far
lines = path.read_text(encoding="utf-8").splitlines()
for number, line in enumerate(lines, start=1):   # enumerate gives the line number and the line together; start=1 counts from 1 like an editor
    n = count_slots(line)
    if n > 0:
        print(f"{path}:{number}: {line.strip()}")   # strip() drops the spaces at both ends of the line
        empty += n

if empty == 0:
    print("all slots filled")
else:
    print(f"{empty} slots still empty")
sys.exit(0)
