# scratch/a06-video.py
# Runs the operations from the DLAI lessons on your own corpus instead of on vectors he made up.
# Run from the repo root:  uv run python scratch/a06-video.py
# Needs search/search.py from Day 1 (Steps 2 and 3), for chunk() and CORPUS. No API call.
# Part 1 (lesson 2): the four distances from the video, on three chunks of your corpus.
# Part 2 (lesson 3): brute-force search in his shape, then the timing curve as N grows.
# Part 3 (word embeddings lesson): the shape your lookup table will have.
# Nothing in this file is yours to edit.
import re, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # add the repo root to Python's search path, so "from search.search" works
from search.search import chunk, CORPUS

# In: a vector, or a matrix of vectors (one per row). Out: the same, with every vector scaled to length 1.
def normalize(V):                 # the same line Step 5 puts in search.py
    return V / np.maximum(np.linalg.norm(V, axis=-1, keepdims=True), 1e-10)   # norm = each row's length; np.maximum guards a zero length

chunks = chunk(CORPUS.read_text(encoding="utf-8"))
n = len(chunks)

# ------------------------------------------------------------ Part 1: distances
# No API yet. The crudest vector a paragraph can have is a count of each word in it.
# These are real vectors about your corpus, and every distance below works on them
# exactly as it will on the 1,536-number vectors in Step 4.

# In: a string. Out: a list of its words, lowercased.
def tokens(s):
    return re.findall(r"[a-z0-9']+", s.lower())     # a "word" is a run of letters, digits or apostrophes; anything else splits words

A = chunks[n // 2]            # a chunk from the middle of the file (// is whole-number division)
B = chunks[n // 2 + 1]        # the chunk right after it
C = chunks[n // 4]            # a chunk a quarter of the way in, far from both
vocab = sorted(set(tokens(A)) | set(tokens(B)) | set(tokens(C)))   # every distinct word in the three chunks; | joins two sets
col = {}                                  # word -> which slot of the vector counts it
for i, w in enumerate(vocab):             # enumerate gives the position i and the word w together
    col[w] = i

# In: a string. Out: a vector with one slot per vocabulary word, holding how many times that word appears.
def count_vector(s):
    v = np.zeros(len(vocab))              # start with all zeros
    for w in tokens(s):
        v[col[w]] += 1                    # add one to the slot for this word
    return v
a = count_vector(A)
b = count_vector(B)
c = count_vector(C)
print("three chunks of your corpus:", n // 2, n // 2 + 1, n // 4, " vocabulary", len(vocab), " vector shape", a.shape)

# Each distance takes two vectors and returns one number. The first three grow with the length of the paragraph; cosine does not.
def euclidean(x, y): return float(np.sqrt(((x - y) ** 2).sum()))   # straight-line distance: square each difference, add them up, square root
def manhattan(x, y): return float(np.abs(x - y).sum())             # add up the absolute differences
def dot(x, y):       return float(x @ y)                           # @ multiplies matching slots and adds the products up
def cosine(x, y):    return float(x @ y / (np.linalg.norm(x) * np.linalg.norm(y)))   # the dot product divided by both lengths
def normalized_dot(x, y):
    return float(normalize(x) @ normalize(y))      # the line that is not in the video: scale both to length 1 first, then dot

print(f"{'pair':<10}{'euclidean':>12}{'manhattan':>12}{'dot':>10}{'cosine':>10}{'norm-dot':>10}")   # f-string: :<10 pads to 10 characters, left-aligned; :>12 right-aligned
pairs = [("A vs B", a, b), ("A vs C", a, c), ("B vs C", b, c), ("A vs A", a, a)]   # a label and the two vectors to compare
for name, x, y in pairs:
    print(f"{name:<10}{euclidean(x, y):>12.3f}{manhattan(x, y):>12.1f}{dot(x, y):>10.1f}{cosine(x, y):>10.4f}{normalized_dot(x, y):>10.4f}")   # .3f = three decimals
print("chunk lengths in words: A", len(tokens(A)), " B", len(tokens(B)), " C", len(tokens(C)))

# ------------------------------------------------------------ Part 2: brute force, and the timing curve
rng = np.random.default_rng(0)            # a random-number generator with a fixed seed, so every run prints the same numbers

# In: a query vector q and a matrix X of stored vectors, all length 1. Out: the k best (row index, score) pairs, best first.
def brute_force(q, X, k=3):
    sims = X @ q                          # one score per stored vector: each row of X dotted with q
    order = np.argsort(sims)              # the row indexes sorted from lowest score to highest
    top = order[::-1][:k]                 # [::-1] reverses, so the highest score comes first; [:k] keeps the first k
    result = []
    for i in top:
        result.append((int(i), round(float(sims[i]), 4)))   # (row index, score rounded to 4 decimals)
    return result

X = normalize(rng.standard_normal((1000, 1536), dtype=np.float32))   # 1,000 pretend chunks, same width as the real ones
q = X[7]                                                             # search with one of them
print("\nbrute force, query = row 7 of 1,000 random vectors:", brute_force(q, X))

print("\nN vectors     microseconds per search")
for N in (1_000, 2_000, 5_000, 10_000, 20_000, n):   # 1_000 is 1000 with a readable underscore; n is your chunk count
    X = normalize(rng.standard_normal((N, 1536), dtype=np.float32))
    q = X[0]
    t = time.perf_counter()               # a stopwatch: the time now, in seconds
    for _ in range(50):                   # search 50 times and average, because one search is too fast to time well
        X @ q
    us = (time.perf_counter() - t) / 50 * 1e6      # seconds per search, times a million = microseconds
    if N == n:
        tag = "   <- your chunk count"
    else:
        tag = ""
    print(f"{N:>9}     {us:>10.0f}{tag}")           # :>9 right-aligns in 9 spaces; .0f = no decimals

# ------------------------------------------------------------ Part 3: the lookup table
print("\nyour lookup table in Step 4 will be one row per chunk:", (n, 1536))
