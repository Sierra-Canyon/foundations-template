# failures/deepdive.py
# Run from the repo root:  uv run python failures/deepdive.py --option A        (A, B, C or D)
#
# What it does: one option, one category. Each option is one function below, with a header comment that
# says in words what its NUMBER, BASELINE and COMPARISON are. Each prints those three lines for evidence/A10.md,
# then the detail behind them, and saves every new answer in failures/deepdive_<option>.json so you can
# quote it. "right" is decided by a rule here: an answer is right when the `answer` field of questions.jsonl
# appears in it, ignoring case. Read the detail, overrule the rule by hand in evidence/A10.md where it is wrong,
# and say that you did. There is nothing to edit in this file.
import json, math, os, sys, urllib.request
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # the repo root, so "from sampling.lab" and "from search.search" work
from sampling.lab import MODEL, generate                           # A09's GPT-2 sampler, unchanged; option D uses it

N = 5                                        # runs per question, the same as ask.py
SUFFIX = " Answer in one sentence."          # the same suffix ask.py adds, so the only change is the one the option makes

QS = {}                                      # {id: the question dict}, from questions.jsonl
for line in Path("failures/questions.jsonl").read_text(encoding="utf-8").splitlines():
    if line.strip():
        q = json.loads(line)
        QS[q["id"]] = q
TRACES = {}                                  # {id: the trace ask.py saved}, with the closed-book API answers
for i in QS:
    TRACES[i] = json.loads(Path(f"failures/traces/{i}.json").read_text(encoding="utf-8"))

# In: the whole user message, a temperature, a token limit.  Out: {"text", "tokens"}, the same shape ask.py saves.
def ask_api(content, temperature=0.7, max_tokens=60):
    """ ask.py's call, with the whole user message passed in """
    body = json.dumps({"model": MODEL, "temperature": temperature, "max_tokens": max_tokens,
                       "logprobs": True, "top_logprobs": 5,
                       "messages": [{"role": "user", "content": content}]}).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions", data=body,
        headers={"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"],
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        c = json.load(r)["choices"][0]
    tokens = []                              # one entry per token: [the token, [[alternative, probability] x 5]]
    for t in c["logprobs"]["content"]:
        alternatives = []
        for a in t["top_logprobs"]:
            alternatives.append([a["token"], round(math.exp(a["logprob"]), 3)])
        tokens.append([t["token"], alternatives])
    return {"text": c["message"]["content"], "tokens": tokens}

# In: an answer text and a question dict.  Out: True when the answer field appears in the text (the rule).
def right(text, q):
    """ the rule: the answer field appears in the text, ignoring case and extra spaces """
    return " ".join(q["answer"].lower().split()) in " ".join(text.lower().split())

# In: a list of runs ({"text": ...} dicts) and a question dict.  Out: how many of the runs are right by the rule.
def count_right(runs, q):
    n = 0
    for r in runs:
        if right(r["text"], q):
            n += 1
    return n

# In: nothing (reads evidence/A10.md).  Out: {id: "rfhfo"}, your five API letters per question, from the rows under ## Marks.
def api_marks():
    """ your API marks from the ## Marks table in evidence/A10.md """
    rows = {}
    inside = False                           # True while we are under the ## Marks heading
    for line in Path("evidence/A10.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            inside = line.strip() == "## Marks"
            continue
        if inside and line.startswith("| q"):
            cells = []
            for c in line.strip().strip("|").split("|"):     # drop the outer | characters, split on the inner ones
                cells.append(c.strip())
            rows[cells[0]] = cells[1]        # the id and the API letters
    assert rows, "no rows under ## Marks in evidence/A10.md; run failures/mark.py first (Step 4)"
    for m in rows.values():
        assert len(m) == 5 and not set(m) - set("rfho"), "fill the marks in evidence/A10.md first (Step 4)"   # five letters, each one of r f h o
    return rows

# In: a chunk's text and a quote.  Out: True when the quote is in the chunk, word for word.
def holds(chunk_text, quote):
    return " ".join(quote.split()) in chunk_text

# In: a passage and a question.  Out: the open-book prompt: the passage, then the question with the suffix.
def with_passage(passage, question):
    return "Here is a passage:\n\n" + passage + "\n\n" + question + SUFFIX

# ============================================================ option A: confident fabrication
# NUMBER      how many of 25 open-book answers are right: your five most-fabricated questions, five runs each,
#             with the chunk of your corpus that holds the quote pasted above the question.
# BASELINE    how many of 25 closed-book answers to the same five questions were right: by your marks, and by the rule.
# COMPARISON  open-book minus closed-book, by the rule. Then every open-book run still wrong: the questions wrong
#             with the answer on the page.
def option_a(out_file):
    from search.search import chunk, CORPUS
    chunks = chunk(CORPUS.read_text(encoding="utf-8"))
    marks = api_marks()

    def fabricated_count(i):
        """ how many of question i's five API runs you marked f """
        return marks[i].count("f")
    ids = sorted(sorted(QS), key=fabricated_count, reverse=True)[:5]   # most f first; sorted keeps ties in id order; [:5] is the first five
    summary = []
    for i in ids:
        summary.append((i, marks[i].count("f")))
    print("five most-fabricated questions, API fabricated/5 by your marks:", summary)

    saved = {}
    for i in ids:
        held = []                            # every chunk that holds this question's quote (usually exactly one)
        for c in chunks:
            if holds(c, QS[i]["quote"]):
                held.append(c)
        assert held, f"{i}: no chunk holds the quote; check_questions.py should have caught this"
        runs = []
        for _ in range(N):
            runs.append(ask_api(with_passage(held[0], QS[i]["question"])))
        saved[i] = {"chunk": held[0], "runs": runs}
        print(" ", i, "asked", N, "times with its chunk pasted in,", len(held[0]), "characters of passage")
    out_file.write_text(json.dumps(saved, indent=1), encoding="utf-8")

    open_right = 0                           # right by the rule, open-book, over the 25 new runs
    closed_hand = 0                          # right by your marks, closed-book, over the 25 runs in the traces
    closed_rule = 0                          # right by the rule, closed-book, over the same 25 runs
    for i in ids:
        open_right += count_right(saved[i]["runs"], QS[i])
        closed_hand += marks[i].count("r")
        closed_rule += count_right(TRACES[i]["api"], QS[i])
    print(f"\nNUMBER      API right, open-book (the chunk holding the quote pasted above the question): {open_right}/25")
    print(f"BASELINE    API right, closed-book, the same five questions: {closed_hand}/25 by your marks, {closed_rule}/25 by the rule")
    print(f"COMPARISON  open-book minus closed-book (by the rule): {open_right - closed_rule:+d} of 25")   # :+d prints the sign too, +12 or -3
    print("\n| id | closed-book right/5 (marks) | closed-book right/5 (rule) | open-book right/5 (rule) |\n|---|---|---|---|")
    for i in ids:
        print(f"| {i} | {marks[i].count('r')} | {count_right(TRACES[i]['api'], QS[i])} | {count_right(saved[i]['runs'], QS[i])} |")
    print("\nstill wrong by the rule with the answer on the page (where it got worse):")
    for i in ids:
        for k, r in enumerate(saved[i]["runs"], 1):          # k counts the runs 1 to 5
            if not right(r["text"], QS[i]):
                print(f"  {i} run {k}: {' '.join(r['text'].split())[:140]}")

# ============================================================ option B: retrieval or grounding
# NUMBER      how often the API is right with the top-1 chunk from your A06 search pasted in, split by whether that
#             chunk actually held the quote: right/runs when it did, right/runs when it did not.
# BASELINE    the top-3 hit rate of keyword search and of semantic search on the same twenty questions (a hit is a
#             chunk among the top three that holds the quote), and how often the semantic top-1 held it.
# COMPARISON  closed-book right (by the rule) on the same two groups of questions. A wrong chunk made it worse
#             than no chunk when right-with-a-wrong-chunk is below closed-book right on those questions.
def option_b(out_file):
    from search.search import chunk, CORPUS, VECS, normalize, search, keyword_search
    chunks = chunk(CORPUS.read_text(encoding="utf-8"))
    V = np.load(VECS)                        # the A06 vectors, one row per chunk
    assert len(V) == len(chunks), "chunking changed since you embedded: delete search/chunks.npy and run search/search.py"
    Vn = normalize(V)

    def any_holds(results, quote):
        """ True when any chunk in a list of (chunk index, score) pairs holds the quote """
        for j, score in results:
            if holds(chunks[j], quote):
                return True
        return False

    saved = {}
    sem_hits = 0                             # questions whose quote is in one of semantic search's top three
    kw_hits = 0                              # the same for keyword search
    top1_held = {}                           # {id: True or False}, did the semantic top-1 chunk hold the quote
    for i in QS:
        q = QS[i]
        sem = search(q["question"], Vn, k=3)                 # three (chunk index, score) pairs, best first; one embedding call
        kw = keyword_search(q["question"], chunks, k=3)      # the same shape, scored by shared words
        if any_holds(sem, q["quote"]):
            sem_hits += 1
        if any_holds(kw, q["quote"]):
            kw_hits += 1
        top1 = sem[0][0]                                     # the best chunk's index
        top1_held[i] = holds(chunks[top1], q["quote"])
        runs = []
        for _ in range(N):
            runs.append(ask_api(with_passage(chunks[top1], q["question"])))
        saved[i] = {"top1": top1, "score": sem[0][1], "held": top1_held[i], "runs": runs}
        if top1_held[i]:
            verdict = "holds"
        else:
            verdict = "does not hold"
        print(f"  {i} top-1 chunk [{top1}] score {sem[0][1]:.3f} {verdict} the quote")
    out_file.write_text(json.dumps(saved, indent=1), encoding="utf-8")

    held_ids = []                            # questions whose top-1 chunk held the quote
    miss_ids = []                            # questions whose top-1 chunk did not
    for i in QS:
        if top1_held[i]:
            held_ids.append(i)
        else:
            miss_ids.append(i)
    r_held, r_miss, c_held, c_miss = 0, 0, 0, 0   # right counts: with the chunk (r_) and closed-book (c_), for each group
    for i in held_ids:
        r_held += count_right(saved[i]["runs"], QS[i])
        c_held += count_right(TRACES[i]["api"], QS[i])
    for i in miss_ids:
        r_miss += count_right(saved[i]["runs"], QS[i])
        c_miss += count_right(TRACES[i]["api"], QS[i])
    print(f"\nNUMBER      API right with the top-1 chunk pasted in: {r_held}/{N * len(held_ids)} when it held the quote ({len(held_ids)} questions), "
          f"{r_miss}/{N * len(miss_ids)} when it did not ({len(miss_ids)} questions)")
    print(f"BASELINE    top-3 hit rate on the same twenty: keyword {kw_hits}/20, semantic {sem_hits}/20, semantic top-1 {len(held_ids)}/20")
    print(f"COMPARISON  closed-book right (rule) on the same split: {c_held}/{N * len(held_ids)} where top-1 held, {c_miss}/{N * len(miss_ids)} where it did not. "
          f"A wrong chunk made it worse than no chunk if {r_miss} < {c_miss}.")
    print("\n| id | top-1 held the quote | closed-book right/5 (rule) | with top-1 pasted right/5 (rule) |\n|---|---|---|---|")
    for i in QS:
        if top1_held[i]:
            held_word = "yes"
        else:
            held_word = "no"
        print(f"| {i} | {held_word} | {count_right(TRACES[i]['api'], QS[i])} | {count_right(saved[i]['runs'], QS[i])} |")

# ============================================================ option C: sampling nondeterminism
# NUMBER      for the question whose five API marks were most split: right/20 and distinct texts/20 at temperature
#             0, 0.7 and 1.2 (twenty runs each).
# BASELINE    the temperature 0 row: right/20 and distinct/20.
# COMPARISON  which temperature was most right and which was most consistent (fewest distinct texts), and whether
#             temperature 0 was both, one, or neither. Then every distinct text at each temperature with how often it came up.
def option_c(out_file):
    marks = api_marks()

    def split_score(i):
        """ (how many different letters, minus the size of the biggest group) for question i's API marks: bigger is more split """
        a = marks[i]
        biggest = 0
        for m in a:
            if a.count(m) > biggest:
                biggest = a.count(m)
        return (len(set(a)), -biggest)
    most_split = None
    for i in sorted(QS):                                     # sorted, so on a tie the lowest id wins
        if most_split is None or split_score(i) > split_score(most_split):
            most_split = i
    i = most_split
    print(f"most split question (API): {i}, marks {marks[i]}: {QS[i]['question']}\n  quote: {QS[i]['quote']}")

    saved = {}                               # {"0": twenty runs, "0.7": twenty runs, "1.2": twenty runs}
    for T in (0, 0.7, 1.2):
        runs = []
        for _ in range(20):
            runs.append(ask_api(QS[i]["question"] + SUFFIX, temperature=T))
        saved[str(T)] = runs
        print(f"  T={T}: 20 runs done")
    out_file.write_text(json.dumps({"id": i, "runs": saved}, indent=1), encoding="utf-8")

    rows = {}                                # {T: {"right": right/20 by the rule, "distinct": distinct texts/20}}
    for T in (0, 0.7, 1.2):
        texts = set()
        for r in saved[str(T)]:
            texts.add(r["text"])
        rows[T] = {"right": count_right(saved[str(T)], QS[i]), "distinct": len(texts)}
    right_parts, distinct_parts = [], []
    for T in rows:
        right_parts.append(f"T={T} {rows[T]['right']}/20")
        distinct_parts.append(f"T={T} {rows[T]['distinct']}")
    print("\nNUMBER      right/20 (rule): " + ", ".join(right_parts) + "   distinct texts/20: " + ", ".join(distinct_parts))
    print(f"BASELINE    T=0: right {rows[0]['right']}/20, distinct {rows[0]['distinct']}/20")
    most_right = 0                           # the temperature with the most right answers; on a tie, the lower one
    most_consistent = 0                      # the temperature with the fewest distinct texts; on a tie, the lower one
    for T in (0.7, 1.2):
        if rows[T]["right"] > rows[most_right]["right"]:
            most_right = T
        if rows[T]["distinct"] < rows[most_consistent]["distinct"]:
            most_consistent = T
    if most_right == 0:
        right_word = "the most right"
    else:
        right_word = "not the most right"
    if most_consistent == 0:
        consistent_word = "the most consistent"
    else:
        consistent_word = "not the most consistent"
    print(f"COMPARISON  most right: T={most_right}; most consistent: T={most_consistent}. "
          f"Temperature 0 was {right_word} and {consistent_word}.")
    for T in (0, 0.7, 1.2):
        print(f"\nT={T}, distinct texts with how often each came up:")
        counts = {}                          # {text: how many of the twenty runs said it}, in the order first seen
        for r in saved[str(T)]:
            text = " ".join(r["text"].split())
            counts[text] = counts.get(text, 0) + 1          # .get(text, 0) is the count so far, or 0 the first time
        def times(text):
            return counts[text]
        for text in sorted(counts, key=times, reverse=True):   # most frequent first; ties stay in the order first seen
            if right(text, QS[i]):
                verdict = "right"
            else:
                verdict = "wrong"
            print(f"  {counts[text]:>2}x {verdict}  {text[:120]}")

# ============================================================ option D: loop or repetition
# NUMBER      how many of GPT-2's twenty answers (60 new tokens each, on the Q: ... A: prompts) loop, at temperature 0,
#             at 0.7, and at 0.7 with top_p=0.9. An output loops when any three-word sequence appears three or more times.
# BASELINE    the temperature 0 row: looping/20 and right/20 by the rule.
# COMPARISON  right/20 at each setting, and whether the setting that looped least is also the one that answered worst.
#             Then a yes/no table per question and the first looping output at each setting.
def option_d(out_file):
    SETTINGS = [{"name": "T=0", "temperature": 0, "top_p": None},
                {"name": "T=0.7", "temperature": 0.7, "top_p": None},
                {"name": "T=0.7 top_p=0.9", "temperature": 0.7, "top_p": 0.9}]

    def loops(text):
        """ True when any three-word sequence appears three or more times """
        w = text.split()
        counts = {}                          # {"three word sequence": how many times it appears}
        for k in range(len(w) - 2):          # every position where three words in a row start
            seq = w[k] + " " + w[k + 1] + " " + w[k + 2]
            counts[seq] = counts.get(seq, 0) + 1
        for seq in counts:
            if counts[seq] >= 3:
                return True
        return False

    saved = {}                               # {setting name: {id: GPT-2's text}}
    for s in SETTINGS:
        saved[s["name"]] = {}
        for i in QS:
            saved[s["name"]][i] = generate(f"Q: {QS[i]['question']}\nA:", n_new=60, seed=0, temperature=s["temperature"], top_p=s["top_p"])
        print(f"  {s['name']}: 20 generations of 60 tokens done")
    out_file.write_text(json.dumps(saved, indent=1), encoding="utf-8")

    rows = {}                                # {setting name: {"loops": looping outputs/20, "right": right/20 by the rule}}
    for s in SETTINGS:
        n_loops, n_right = 0, 0
        for i in QS:
            if loops(saved[s["name"]][i]):
                n_loops += 1
            if right(saved[s["name"]][i], QS[i]):
                n_right += 1
        rows[s["name"]] = {"loops": n_loops, "right": n_right}
    loop_parts, right_parts = [], []
    for name in rows:
        loop_parts.append(f"{name} {rows[name]['loops']}/20")
        right_parts.append(f"{name} {rows[name]['right']}/20")
    print("\nNUMBER      looping outputs/20: " + ", ".join(loop_parts))
    print(f"BASELINE    T=0: {rows['T=0']['loops']}/20 looping, {rows['T=0']['right']}/20 right (rule)")
    least = "T=0"                            # the setting that looped least; on a tie, the earlier one
    worst = "T=0"                            # the setting with the fewest right; on a tie, the earlier one
    for name in rows:
        if rows[name]["loops"] < rows[least]["loops"]:
            least = name
        if rows[name]["right"] < rows[worst]["right"]:
            worst = name
    if least == worst:
        same_word = "the same setting"
    else:
        same_word = "different settings"
    print(f"COMPARISON  right/20 (rule): " + ", ".join(right_parts) + f". Looped least: {least}; answered worst: {worst}; {same_word}.")
    header_parts = []
    for s in SETTINGS:
        header_parts.append(f"{s['name']} loops")
    print("\n| id | " + " | ".join(header_parts) + " |\n|---|---|---|---|")
    for i in QS:
        cells = []
        for s in SETTINGS:
            if loops(saved[s["name"]][i]):
                cells.append("yes")
            else:
                cells.append("no")
        print(f"| {i} | " + " | ".join(cells) + " |")
    for s in SETTINGS:
        first = None                         # the first question whose output loops at this setting
        for i in QS:
            if first is None and loops(saved[s["name"]][i]):
                first = i
        if first is not None:
            print(f"\nfirst looping output at {s['name']}, {first}: {saved[s['name']][first][:200]!r}")

# ============================================================ which option to run
if __name__ == "__main__":
    OPTION = ""
    if len(sys.argv) == 3 and sys.argv[1] == "--option":   # exactly "--option" and a letter after the script name
        OPTION = sys.argv[2].upper()
    assert OPTION in ("A", "B", "C", "D"), "usage: uv run python failures/deepdive.py --option A|B|C|D"
    out_file = Path(f"failures/deepdive_{OPTION}.json")    # where this option's new answers are saved
    if OPTION == "A":
        option_a(out_file)
    elif OPTION == "B":
        option_b(out_file)
    elif OPTION == "C":
        option_c(out_file)
    else:
        option_d(out_file)
