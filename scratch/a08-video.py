# scratch/a08-video.py
# Run from the repo root:  uv run python scratch/a08-video.py
#
# What it does, in three parts:
#   Part 1 is Karpathy's self-attention v4 on his toy tensor, as he types it from 01:02:00.
#   Part 2 is the same head, same three matrices, on one sentence from your corpus.
#   Part 3 is one block of output for each of his six notes, starting at 01:11:38.
#
# The one line you edit is SENTENCE. Nothing else in this file is yours to edit.
import tiktoken, torch
import torch.nn as nn                       # nn has the building blocks: Linear, Embedding
from torch.nn import functional as F        # F has the functions: softmax

SENTENCE = "PASTE YOUR SENTENCE HERE"      # the sentence you chose in Step 2

torch.manual_seed(1337)                                            # same random numbers every run
torch.set_printoptions(precision=2, sci_mode=False, linewidth=140)  # print tensors with 2 decimals, on wide lines

# ------------------------------------------------------------ Part 1: his toy tensor, 01:02:00 -> 01:11:38
B, T, C = 4, 8, 32           # batch, time, channels: four sequences of eight positions, 32 numbers each
x = torch.randn(B, T, C)     # random numbers standing in for token vectors

head_size = 16
key = nn.Linear(C, head_size, bias=False)        # turns 32 numbers into 16: what a position advertises
query = nn.Linear(C, head_size, bias=False)      # turns 32 numbers into 16: what a position is asking for
value = nn.Linear(C, head_size, bias=False)      # turns 32 numbers into 16: what a position hands over
k = key(x)                                   # (B, T, 16)
q = query(x)                                 # (B, T, 16)
# q @ k^T: every position's query against every position's key, one score per pair, shape (B, T, T).
# transpose(-2, -1) swaps the last two axes of k so the @ lines up. Scaled by 1/sqrt(head_size),
# not C: his correction in the description.
wei = q @ k.transpose(-2, -1) * head_size**-0.5

tril = torch.tril(torch.ones(T, T))                # a T x T triangle: ones on and below the diagonal, zeros above
wei = wei.masked_fill(tril == 0, float("-inf"))    # where the triangle is 0 (a later position), put -inf: it cannot be seen
wei = F.softmax(wei, dim=-1)                       # every row becomes a budget that sums to one; -inf becomes 0
v = value(x)                                       # (B, T, 16)
out = wei @ v                                      # (B, T, 16): each position's weighted mix of the values it can see

print("PART 1: his toy tensor")
print("x", tuple(x.shape), " k, q, v", tuple(k.shape), " wei", tuple(wei.shape), " out", tuple(out.shape))
print("wei[0], the grid for the first of his four sequences:")
print(wei[0].detach())                             # detach: just the numbers, without torch's notes for gradients

# ------------------------------------------------------------ Part 2: the same head on your sentence
enc = tiktoken.get_encoding("cl100k_base")
ids = enc.encode(SENTENCE)                         # your sentence as a list of token ids
labels = []                                        # one short text label per token, for the grid's rows and columns
for i in ids:
    piece = enc.decode([i]).strip()                # the token's text, without its leading space
    if piece == "":                                # a token that is only a space would print as nothing
        piece = "_"
    labels.append(piece)
Ts = len(ids)                                      # T for your sentence
tok_emb = nn.Embedding(enc.n_vocab, C)             # a table with one random row of 32 numbers per token id
xs = tok_emb(torch.tensor([ids]))                  # (1, Ts, C): your sentence in his shape, B = 1

# In: xq, the tensor the queries come from, and xkv, the tensor the keys and values come from
#     (the same tensor for self-attention), and whether to apply the mask.
# Out: the grid of weights wei, shape (B, T_of_xq, T_of_xkv), with every row summing to one.
def attend(xq, xkv, masked=True):
    q = query(xq)
    k = key(xkv)
    wei = q @ k.transpose(-2, -1) * head_size**-0.5   # every query dotted with every key: a (T, T) grid of scores, scaled down by sqrt(head_size)
    if masked:                                     # the mask only makes sense when xq and xkv are the same text
        Tq = xq.shape[1]                           # how many positions xq has
        wei = wei.masked_fill(torch.tril(torch.ones(Tq, Tq)) == 0, float("-inf"))
    wei = F.softmax(wei, dim=-1)
    return wei.detach()

# In: a one-row tensor of numbers. Out: the same numbers as a plain Python list, each rounded to 2 decimals.
def rounded(t):
    result = []
    for w in t.tolist():
        result.append(round(w, 2))
    return result

wei_s = attend(xs, xs)
out_s = wei_s @ value(xs).detach()                 # (1, Ts, 16), as out was in Part 1
print(f"\nPART 2: the same head on your sentence, {Ts} tokens")
print("xs", tuple(xs.shape), " wei", tuple(wei_s.shape), " out", tuple(out_s.shape))
print("the first four rows, with your tokens on them:")
header = " " * 9                                   # 9 spaces, the width of the row labels below
for l in labels[:4]:                               # the first four tokens
    header += f"{l[:6]:>7}"                        # the first 6 characters of the token, right-aligned in 7 columns
print(header)
for r in range(4):                                 # the first four rows of the grid
    line = f"{labels[r][:8]:>8} "                  # the row's token, right-aligned in 8 columns, then a space
    for w in wei_s[0, r, :4].tolist():             # the first four weights in row r
        line += f"{w:7.2f}"                        # each weight with 2 decimals in 7 columns
    print(line)

# ------------------------------------------------------------ Part 3: his six notes, 01:11:38 -> 01:19:11
print("\nPART 3: the six notes")

# ---------- note 1: attention is communication.
# Every token is a node in a graph; the nonzero weights in its row are the arrows pointing into it.
edges = (wei_s[0] > 0).sum(dim=-1).tolist()        # for each row, count the cells that are not zero
print(f"1. nodes that send into each position, row by row: {edges}")
print(f"   the first token hears from {edges[0]} node (itself); the last, '{labels[-1]}', hears from all {edges[-1]}")

# ---------- note 2: no notion of space.
# x is built from the token ids alone, so the same token gets the same vector wherever it sits.
ids_reversed = ids[::-1]                           # [::-1] reverses the list: last token first
xs_rev = tok_emb(torch.tensor([ids_reversed]))     # the reversed sentence, through the same table
# xs.flip(1) reverses xs along its token axis; torch.equal is True if the two tensors match number for number
print(f"2. your sentence reversed gives the same vectors in reverse order: {torch.equal(xs.flip(1), xs_rev)}  (nothing in x says where a token is; positions are added later)")

# ---------- note 3: the B sequences never talk.
# Wipe out sequence 1 of his toy tensor and sequence 0's grid does not move.
x_wiped = x.clone()                                # a copy, so x itself is untouched
x_wiped[1] = 0                                     # every number in sequence 1 becomes 0
wei_wiped = attend(x_wiped, x_wiped)
# allclose: True if every number in one grid is within a hair of the matching number in the other
print(f"3. after zeroing sequence 1 of his toy tensor, sequence 0's grid is unchanged: {torch.allclose(wei[0].detach(), wei_wiped[0])}")

# ---------- note 4: encoder = delete the masking line.
# Every token then sees the whole sentence, including what comes after it.
wei_enc = attend(xs, xs, masked=False)
row0 = wei_enc[0, 0]                               # row 0: the first token's weights over every token
print(f"4. with the mask line deleted, row 0 of your sentence becomes: {rounded(row0)}")
print(f"   it still sums to {row0.sum().item():.2f}, and the first token now hears from all {int((row0 > 0).sum())} tokens")

# ---------- note 5: self-attention means k and v come from the same x as q.
# Take them from a different text and the grid stops being square.
words = open("data/corpus.txt", encoding="utf-8").read().split()   # every word of your corpus
OTHER = " ".join(words[:12])                       # the first twelve words, joined back into one string
xo = tok_emb(torch.tensor([enc.encode(OTHER)]))    # that text, through the same table
wei_cross = attend(xs, xo, masked=False)           # queries from your sentence, keys and values from OTHER
print(f"5. queries from your sentence, keys and values from another text ({xo.shape[1]} tokens): wei is {tuple(wei_cross.shape)}, not square. That is cross-attention.")

# ---------- note 6: scale by 1/sqrt(head_size).
# His demonstration first: random k and q with variance about 1 give q @ k^T a variance about head_size.
kk = torch.randn(B, T, head_size)
qq = torch.randn(B, T, head_size)
raw = qq @ kk.transpose(-2, -1)                    # the scores without the scale
# .var() is the variance: how spread out the numbers are
print(f"6. variance of k {kk.var():.2f}, of q {qq.var():.2f}, of q @ k^T without the scale {raw.var():.2f}, with the scale {(raw * head_size**-0.5).var():.2f}")
# Then his second demonstration: softmax of small numbers is spread out; softmax of the same numbers times 8 piles up on the biggest.
small = torch.tensor([0.1, -0.2, 0.3, -0.2, 0.5])
print(f"   softmax of a small vector      {rounded(F.softmax(small, dim=-1))}")
print(f"   softmax of the same vector * 8 {rounded(F.softmax(small * 8, dim=-1))}")
# Then the same thing on your sentence: the last row's biggest weight, with the scale (wei_s) and without it.
q_s = query(xs)
k_s = key(xs)
scores_unscaled = q_s @ k_s.transpose(-2, -1)      # no * head_size**-0.5 this time
scores_unscaled = scores_unscaled.masked_fill(torch.tril(torch.ones(Ts, Ts)) == 0, float("-inf"))
unscaled = F.softmax(scores_unscaled, dim=-1).detach()
print(f"   biggest weight in your last row, '{labels[-1]}': with the scale {wei_s[0, -1].max():.2f}, without it {unscaled[0, -1].max():.2f}")
