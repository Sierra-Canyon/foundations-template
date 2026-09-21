# failures — A10

`CATALOG.md` holds ten entries. Each one: repro steps, observed versus expected, failure
rate over N runs, category, a mechanistic hypothesis, and evidence where you have it.

The distinction that carries the assignment: a failure that happens once is a story, a
failure that happens 3 times in 20 is data. Every entry needs the denominator.

"The model hallucinated" is not a hypothesis. A claim about tokenization, retrieval,
context truncation or sampling that you could test is. You do not have to be right; you
have to be falsifiable.

Traces go in `traces/`.
