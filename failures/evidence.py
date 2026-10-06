# failures/evidence.py
# Run from the repo root:  uv run python failures/evidence.py q07 1        (question id, API run number 1 to 5)
#
# What it does: prints one API answer token by token with the model's top-5 alternatives at every
# position, flags the first token that is in neither the quote nor the question, and says whether the
# right answer was in the top five there. The flag is a pointer, not a verdict: a right answer also has
# words the quote does not. There is nothing to edit in this file.
import json, sys
from pathlib import Path

# words too common to say anything about where a token came from
STOP = {"the", "a", "an", "of", "and", "to", "in", "is", "was", "what", "who", "how", "why", "does", "did",
        "which", "whose", "where", "when", "do", "he", "she", "it", "they", "his", "her", "its", "their", "them",
        "him", "that", "this", "for", "from", "by", "with", "on", "at", "as", "be", "are", "were", "had", "has", "have"}

assert len(sys.argv) == 3, "usage: uv run python failures/evidence.py <id> <run 1-5>"   # stops with that message unless there are exactly two words after the script name
qid, run_no = sys.argv[1], int(sys.argv[2])
q = json.loads(Path(f"failures/traces/{qid}.json").read_text(encoding="utf-8"))
run = q["api"][run_no - 1]                     # runs are numbered 1 to 5 for you; the list counts from 0
quote = " ".join(q["quote"].lower().split())      # lowercased, single spaces, so tokens can be looked up in them
question = " ".join(q["question"].lower().split())
answer = " ".join(q["answer"].lower().split())

# In: one token, as the API wrote it.  Out: its letters, digits and apostrophes, lowercased, minus a possessive.
def core(tok):
    """ ' Noman' -> 'noman', ' prophet's' -> 'prophet', ',' -> '' """
    c = ""
    for ch in tok.lower():
        if ch.isalnum() or ch == "'":           # keep letters, digits and apostrophes; drop spaces and punctuation
            c += ch
    if c.endswith("'s"):
        c = c[:-2]
    return c

# In: one token.  Out: where its text can be found: "in quote", "in question", "NOT IN QUOTE OR QUESTION", or "" when it is too short or a stop word to say.
def where(tok):
    c = core(tok)
    if len(c) < 3 or c in STOP:
        return ""
    if c in quote:
        return "in quote"
    if c in question:
        return "in question"
    return "NOT IN QUOTE OR QUESTION"

print(f"{qid} run {run_no}: {q['question']}")
print(f"  answer: {q['answer']}\n  quote:  {q['quote']}\n  text:   {run['text']}")
if answer in " ".join(run["text"].lower().split()):
    print("  contains the answer field: yes, so the flag below points at filler, not a fabrication\n")
else:
    print("  contains the answer field: no\n")

print(f"{'pos':>3} {'token':<16} {'top-5 alternatives [token, probability]':<84} where")   # :>3 right-aligns in 3 columns; :<16 left-aligns in 16
first = None                                   # the position of the first token not in the quote or question, once found
for pos, (tok, top5) in enumerate(run["tokens"]):   # enumerate numbers the tokens from 0; each entry is [token, top-5 list]
    w = where(tok)
    flag = ""
    if w.startswith("NOT") and first is None:
        first = pos
        flag = "   <-- first token not in the quote"
    print(f"{pos:>3} {tok!r:<16} {str(top5)[:84]:<84} {w}{flag}")   # !r shows the token in quotes, spaces included; [:84] cuts the list to fit

if first is None:
    print("\nevery token of three or more letters is in the quote or the question: this run is not a fabrication by text")
else:
    tok, top5 = run["tokens"][first]
    own = None                                 # the probability the model put on the token it chose, if it is among the five
    for t, p in top5:
        if t == tok and own is None:
            own = p
    print(f"\nfirst token not in the quote: position {first}, {tok!r}")
    if own is None:
        print(f"  probability on it: below the fifth alternative ({top5[-1][1]} or less)")   # top5[-1] is the last of the five, the least likely
    else:
        print(f"  probability on it: {own}")
    right = []                                 # the alternatives there whose text is in the answer or the quote
    for t, p in top5:
        c = core(t)
        if len(c) >= 3 and c not in STOP and (c in answer or c in quote):
            right.append((t, p))
    if right:
        print(f"  right answer in the top five there: yes, {right}")
    else:
        print("  right answer in the top five there: no")
    parts = []
    for t, p in top5:
        parts.append(f"{t!r} {p}")
    print("  the five: " + ", ".join(parts))
