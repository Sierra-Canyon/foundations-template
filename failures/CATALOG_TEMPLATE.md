# Failure Catalog: <your name>

Corpus: <data/SOURCE.md's one-line description>. API model: <MODEL from sampling/lab.py>. GPT-2: 124M, A09 sampler, T=0.7.
Questions: 20 (failures/questions.jsonl). Runs: 5 per question per model. Marks: failures/marks.md.

<!-- Ten entries. Keep the seven field names and their order. Delete every hint in angle brackets as you fill it.
     At least six entries come from your twenty questions; at least four show the same question on both models;
     at least three carry evidence from evidence.py; at least two are failures you caused; exactly one has Hypothesis: unknown, bounded. -->

## Entry 1: <four-word title>

- **Repro:** <the question verbatim, the model, every sampling setting, and the command that reruns it: `uv run python failures/ask.py` for a trace, or `uv run python failures/evidence.py q07 1` for one run>
- **Observed:** <the answer, pasted from the trace, not retyped; name the run: API run 3 of q07>
- **Expected:** <the quote, pasted, and where it is: `grep -n "..." data/corpus.txt` gives the line>
- **Rate:** <failures over runs, with N: 4/5 API runs said X; 5/5 GPT-2 runs wandered off>
- **Category:** <one of: tokenization artifact · context window or truncation · sampling nondeterminism · retrieval or grounding failure · instruction-following collapse · tool-schema mismatch · confident fabrication · loop or repetition, or one you name>
- **Hypothesis:** <one claim about machinery, tied to something from A03 to A09: the model never saw this text (A05b, A06), the name splits into pieces (A04), temperature 0.7 draws from a spread distribution (A09)>
- **Evidence:** <what evidence.py printed at the failure position, a tokenizer split, a diff across runs, or a token count; or "none yet", honestly>

## Entry 2: <title>

- **Repro:** <>
- **Observed:** <>
- **Expected:** <>
- **Rate:** <>
- **Category:** <>
- **Hypothesis:** <>
- **Evidence:** <>

## Entry 3: <title>

- **Repro:** <>
- **Observed:** <>
- **Expected:** <>
- **Rate:** <>
- **Category:** <>
- **Hypothesis:** <>
- **Evidence:** <>

## Entry 4: <title>

- **Repro:** <>
- **Observed:** <>
- **Expected:** <>
- **Rate:** <>
- **Category:** <>
- **Hypothesis:** <>
- **Evidence:** <>

## Entry 5: <title>

- **Repro:** <>
- **Observed:** <>
- **Expected:** <>
- **Rate:** <>
- **Category:** <>
- **Hypothesis:** <>
- **Evidence:** <>

## Entry 6: <title>

- **Repro:** <>
- **Observed:** <>
- **Expected:** <>
- **Rate:** <>
- **Category:** <>
- **Hypothesis:** <>
- **Evidence:** <>

## Entry 7: <title, a failure you caused>

- **Repro:** <>
- **Observed:** <>
- **Expected:** <>
- **Rate:** <>
- **Category:** <>
- **Hypothesis:** <name the line of ask.py or questions.jsonl that did it>
- **Evidence:** <>

## Entry 8: <title, a failure you caused>

- **Repro:** <>
- **Observed:** <>
- **Expected:** <>
- **Rate:** <>
- **Category:** <>
- **Hypothesis:** <name the line of ask.py or questions.jsonl that did it>
- **Evidence:** <>

## Entry 9: <title, from something else you ran this term: A06 search, the A09 table, a cl100k_base split>

- **Repro:** <>
- **Observed:** <>
- **Expected:** <>
- **Rate:** <>
- **Category:** <>
- **Hypothesis:** <>
- **Evidence:** <>

## Entry 10: <title, the one you cannot explain>

- **Repro:** <>
- **Observed:** <>
- **Expected:** <>
- **Rate:** <>
- **Category:** unknown
- **Hypothesis:** unknown. Ruled out: <category (the evidence that rules it out)>, <category (evidence)>
- **Evidence:** <the evidence named above, pasted>

## Deep dive: option <A/B/C/D>, <category>

Why this category: <one sentence>
Predicted number, written in the log before running: <n> (`grep -n -i predict logs/*.md` in the log repo finds it)

    <paste the NUMBER, BASELINE and COMPARISON lines deepdive.py printed, indented four spaces>

Where it got worse: <A: the questions still wrong with the answer on the page. B: whether a wrong chunk made the answer worse than no chunk. C: whether temperature 0 was the most right or only the most consistent. D: whether the setting that looped least also answered worst.>
Falsifier: <the result that would have come out the other way if my hypothesis for this category were wrong, and whether anything above came close>
