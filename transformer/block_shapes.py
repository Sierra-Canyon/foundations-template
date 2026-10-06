# transformer/block_shapes.py
# Run from the repo root:  uv run python transformer/block_shapes.py
#                     or:  uv run python transformer/block_shapes.py gpt2      (the Extension)
#                     or:  uv run python transformer/block_shapes.py tiny      (the Extension)
#
# What it does: builds Karpathy's decoder block (Head, MultiHeadAttention, FeedFoward, Block,
# as he writes them in the video) and pushes one sentence from your corpus through it once.
# Then it prints a SHAPE TABLE with one row per arrow, every parameter tensor with its size,
# and the total.
#
# The one line you edit is SENTENCE. Everything else stays as it is, except in Reflection
# Question 3, which asks you to change one number in CONFIGS and then put it back.
import sys                                  # for the config word on the command line, e.g. "gpt2"
import tiktoken, torch
import torch.nn as nn                       # nn has the building blocks: Linear, Embedding, LayerNorm
from torch.nn import functional as F        # F has the functions: softmax, relu

SENTENCE = "PASTE YOUR SENTENCE HERE"          # one sentence from data/corpus.txt; Step 3 says how to find it

# One config per name. Each is a dict of three named numbers:
#   n_embd      = d, how many numbers each token's vector has
#   n_head      = h, how many attention heads work side by side
#   block_size  = the context length, the most tokens the block can take at once
CONFIGS = {
    "walkthrough": {"n_embd": 64,  "n_head": 8,  "block_size": 32},
    "gpt2":        {"n_embd": 768, "n_head": 12, "block_size": 1024},   # GPT-2 small, from openai-community/gpt2 config.json
    "tiny":        {"n_embd": 32,  "n_head": 4,  "block_size": 32},     # Karpathy's width and head count in the segment; block_size raised so a sentence fits
}
if len(sys.argv) > 1:               # sys.argv is the command line split into words; [0] is the script, [1] is the first word after it
    CONFIG = sys.argv[1]
else:
    CONFIG = "walkthrough"
n_embd = CONFIGS[CONFIG]["n_embd"]
n_head = CONFIGS[CONFIG]["n_head"]
block_size = CONFIGS[CONFIG]["block_size"]
torch.manual_seed(1337)             # the random numbers come out the same every run, so your table is repeatable

# ------------------------------------------------------------ Karpathy's classes, 01:21:59 -> 01:37:49
# These four classes are his, exactly as he has them at 01:37:49. They read n_embd and
# block_size from the top of this file instead of being handed them; that is why CONFIGS
# sits above them.

class Head(nn.Module):
    """ one head of self-attention """
    # In: head_size, how many numbers this head works with per token (d_head).
    # Out: a module that turns (B, T, n_embd) into (B, T, head_size).
    def __init__(self, head_size):
        super().__init__()
        self.key = nn.Linear(n_embd, head_size, bias=False)      # what each token advertises
        self.query = nn.Linear(n_embd, head_size, bias=False)    # what each token is asking for
        self.value = nn.Linear(n_embd, head_size, bias=False)    # what each token hands over
        # tril is a block_size x block_size triangle of ones (ones on and below the diagonal, zeros above).
        # register_buffer keeps it with the model but marks it as not trainable.
        self.register_buffer("tril", torch.tril(torch.ones(block_size, block_size)))
        self.head_size = head_size

    # In: x of shape (B, T, n_embd). Out: (B, T, head_size), each token's mix of the values it can see.
    def forward(self, x):
        B, T, C = x.shape                                        # read the three sizes off the tensor
        q, k = self.query(x), self.key(x)
        # q @ k^T: every token's query against every token's key, one score per pair, shape (B, T, T).
        # Scaled by 1/sqrt(head_size), not C: his correction in the description.
        wei = q @ k.transpose(-2, -1) * self.head_size**-0.5
        # Where the triangle has a zero (a later token), put -inf so softmax gives it weight 0.
        wei = wei.masked_fill(self.tril[:T, :T] == 0, float("-inf"))
        wei = F.softmax(wei, dim=-1)                             # each row becomes weights that sum to one
        return wei @ self.value(x)                               # weighted mix of the values, (B, T, head_size)

class MultiHeadAttention(nn.Module):
    """ multiple heads of self-attention in parallel """
    # In: num_heads and head_size. Out: a module that runs num_heads Heads side by side and
    # joins their outputs back to width n_embd.
    def __init__(self, num_heads, head_size):
        super().__init__()
        # same as: make an empty list, then for each of num_heads times append a new Head(head_size)
        self.heads = nn.ModuleList([Head(head_size) for _ in range(num_heads)])
        self.proj = nn.Linear(n_embd, n_embd)                    # mixes the joined heads; this one has a bias

    # In: x of shape (B, T, n_embd). Out: (B, T, n_embd).
    def forward(self, x):
        # same as: run every head on x, then lay the results side by side along the last axis
        out = torch.cat([h(x) for h in self.heads], dim=-1)
        out = self.proj(out)
        return out

class FeedFoward(nn.Module):                   # his spelling, kept
    """ a simple linear layer followed by a non-linearity """
    # In: n_embd. Out: a module that widens each token to 4 * n_embd, applies ReLU, and narrows it back.
    def __init__(self, n_embd):
        super().__init__()
        self.net = nn.Sequential(              # Sequential runs its layers in order, one after the other
            nn.Linear(n_embd, 4 * n_embd),     # net[0]: the four-times-wider hidden layer
            nn.ReLU(),                         # net[1]: negative numbers become 0
            nn.Linear(4 * n_embd, n_embd),     # net[2]: back to width n_embd
        )

    # In: x of shape (B, T, n_embd). Out: (B, T, n_embd). Each token is handled on its own.
    def forward(self, x):
        return self.net(x)

class Block(nn.Module):
    """ Transformer block: communication followed by computation """
    # In: n_embd and n_head. Out: one decoder block, ready to run on (B, T, n_embd).
    def __init__(self, n_embd, n_head):
        super().__init__()
        head_size = n_embd // n_head           # d_head = d / h; // is whole-number division
        self.sa = MultiHeadAttention(n_head, head_size)
        self.ffwd = FeedFoward(n_embd)
        self.ln1 = nn.LayerNorm(n_embd)        # normalizes each token's vector before attention
        self.ln2 = nn.LayerNorm(n_embd)        # normalizes each token's vector before the feedforward

    # In: x of shape (B, T, n_embd). Out: the same shape. The two "x = x + ..." lines are the residual stream.
    def forward(self, x):
        x = x + self.sa(self.ln1(x))           # attention's output is added to x, never put in its place
        x = x + self.ffwd(self.ln2(x))         # the feedforward's output is added too
        return x

# ------------------------------------------------------------ your sentence becomes x
enc = tiktoken.get_encoding("cl100k_base")
ids = enc.encode(SENTENCE)                               # the sentence as a list of token ids
B, T, d, h = 1, len(ids), n_embd, n_head                 # one sentence, T tokens, d numbers each, h heads
d_head = d // h
tok_emb = nn.Embedding(enc.n_vocab, n_embd)              # a table with one random row of d numbers per token id, as in A08
x = tok_emb(torch.tensor([ids]))                         # (B, T, d): look up each id's row; the outer [ ] adds the batch dimension
blk = Block(n_embd, n_head)

print(f"config {CONFIG}: vocabulary {enc.n_vocab}   d {d}   context (block_size) {block_size}")
print(f"sentence: {T} tokens from {len(SENTENCE.split())} words  ->  B={B} T={T} d={d} h={h} d_head={d_head} 4d={4*d}")
if T > block_size:
    print(f"T={T} is longer than block_size={block_size}: the mask is {block_size} x {block_size} and cannot cover it. Watch what happens.")

# ------------------------------------------------------------ the arrows, in the order Block.forward runs them
rows = []                                                # one dict per arrow, filled in by row() below

# In: a name for the arrow, the tensor that flows along it, its shape written in symbols, and which sublayer it belongs to.
# Out: nothing returned; one row is added to the rows list, with the shape in numbers read off the tensor.
def row(name, t, symbols, sublayer):
    rows.append({"arrow": name, "symbols": symbols, "numbers": str(tuple(t.shape)), "sublayer": sublayer})

with torch.no_grad():                                    # no training here, so tell torch not to keep notes for gradients
    y = blk(x)                                           # the whole block once; the rows below retrace it one arrow at a time

    # Block.forward, line 1:  x = x + self.sa(self.ln1(x))
    row("x in", x, "(B, T, d)", "residual stream")
    a = blk.ln1(x)                                       # the ln1(x) inside the parentheses
    row("ln1(x)", a, "(B, T, d)", "attention")

    # Inside self.sa(...): MultiHeadAttention.forward runs each Head on a. Follow head 0 through Head.forward.
    h0 = blk.sa.heads[0]
    q, k, v = h0.query(a), h0.key(a), h0.value(a)        # Head.forward: q, k = self.query(x), self.key(x), and self.value(x)
    row("q, k, v (one head)", q, "(B, T, d_head)", "attention")
    scores = q @ k.transpose(-2, -1) * h0.head_size**-0.5    # Head.forward: wei = q @ k.transpose(-2, -1) * self.head_size**-0.5
    row("scores q @ k^T (one head)", scores, "(B, T, T)", "attention")
    mask = h0.tril[:T, :T]                               # Head.forward: self.tril[:T, :T], the top-left T x T corner of the triangle
    row("mask tril[:T, :T]", mask, "(T, T)", "attention")
    wei = F.softmax(scores.masked_fill(mask == 0, float("-inf")), dim=-1)   # Head.forward: the masked_fill line, then the softmax line
    row("softmax weights (one head)", wei, "(B, T, T)", "attention")
    row("wei @ v (one head out)", wei @ v, "(B, T, d_head)", "attention")   # Head.forward: return wei @ self.value(x)

    # The same scores for every head at once: one (B, T, T) grid per head, stacked along a new axis.
    # This shape never appears inside the block as one tensor; it is here so you can see it.
    scores_per_head = []
    for hd in blk.sa.heads:
        scores_per_head.append(hd.query(a) @ hd.key(a).transpose(-2, -1))   # this head's (B, T, T) score grid: every query dotted with every key
    all_scores = torch.stack(scores_per_head, dim=1)     # stack puts the h grids side by side as axis 1: (B, h, T, T)
    row("scores, all heads stacked", all_scores, "(B, h, T, T)", "attention")

    # MultiHeadAttention.forward: out = torch.cat([h(x) for h in self.heads], dim=-1), written as a loop
    head_outputs = []
    for hd in blk.sa.heads:
        head_outputs.append(hd(a))                       # each head's (B, T, d_head)
    cat = torch.cat(head_outputs, dim=-1)                # laid side by side along the last axis: (B, T, h * d_head)
    row("heads concat", cat, "(B, T, h*d_head)", "attention")
    sa_out = blk.sa.proj(cat)                            # MultiHeadAttention.forward: out = self.proj(out)
    row("proj", sa_out, "(B, T, d)", "attention")
    x1 = x + sa_out                                      # Block.forward, line 1, the addition: x = x + self.sa(...)
    row("+ residual 1:  x + sa(ln1(x))", x1, "(B, T, d)", "residual stream")

    # Block.forward, line 2:  x = x + self.ffwd(self.ln2(x))
    b = blk.ln2(x1)                                      # the ln2(x) inside the parentheses
    row("ln2(x)", b, "(B, T, d)", "feedforward")
    hid = blk.ffwd.net[0](b)                             # FeedFoward.forward, first layer of self.net: Linear(n_embd, 4 * n_embd)
    row("ffwd hidden (before ReLU)", hid, "(B, T, 4d)", "feedforward")
    ff_out = blk.ffwd.net[2](F.relu(hid))                # FeedFoward.forward, the ReLU and then the last layer: Linear(4 * n_embd, n_embd)
    row("ffwd out", ff_out, "(B, T, d)", "feedforward")
    x2 = x1 + ff_out                                     # Block.forward, line 2, the addition: x = x + self.ffwd(...)
    row("+ residual 2:  x + ffwd(ln2(x))  = x out", x2, "(B, T, d)", "residual stream")

    # allclose: True if every number in x2 is within a hair of the matching number in y.
    # If the retrace above missed a step, this line stops the script with the message.
    assert torch.allclose(x2, y, atol=1e-5), "the arrows above do not add up to Block.forward"

print("\nSHAPE TABLE")
# :<42 means: pad this text with spaces on the right until it is 42 characters wide, so the columns line up
print(f"{'arrow':<42} {'shape in symbols':<18} {'shape in numbers':<18} sublayer")
for r in rows:
    print(f"{r['arrow']:<42} {r['symbols']:<18} {r['numbers']:<18} {r['sublayer']}")

# ------------------------------------------------------------ parameters: every tensor that training would change
print("\nPARAMETERS")
total = 0
for name, p in blk.named_parameters():                   # named_parameters gives each trainable tensor with its dotted name
    print(f"{name:<24} {str(tuple(p.shape)):<14} {p.numel():>10,}")   # numel: how many numbers the tensor holds; :, adds thousands commas
    total += p.numel()
print(f"{'total':<24} {'':<14} {total:>10,}   ({len(list(blk.parameters()))} tensors)")
print(f"not parameters: {h} mask buffers tril, each {tuple(h0.tril.shape)}, never trained")
