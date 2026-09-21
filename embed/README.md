# embed — A05

`probe.py` is the file you write. Everything for A05 goes in it; there is no notebook
this week, which means no kernel to select and no cell ordering to get wrong.

Two files here are committed rather than ignored, which is the opposite of the rule
everywhere else in this repo:

| File | Why it is committed |
|---|---|
| `vecs.npy` | A06 builds on exactly these vectors, and I re-run your numbers against them. |
| `words.npy` | Without the word list in the same order, the array is unreadable. |

Embed once, save, and load from disk on every run after that. Your key has a hard cap
and it does not warn you on the way to it.

`FINDINGS.md` carries all three probe results and your pre-registered anisotropy
prediction sitting next to the number you actually measured.
