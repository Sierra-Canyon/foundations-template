# scratch/a09-video.py
# Run from the repo root:  uv run python scratch/a09-video.py
#
# What it does: Karpathy's sampling loop from 00:33:31 -> 00:45:50, with two things swapped:
# the Hugging Face GPT-2 in place of the GPT class he wrote earlier in the video, and the first
# prompt from your corpus in place of "Hello, I'm a language model,". It prints five continuations
# of that prompt, thirty new tokens each, sampled with top-k = 50 and nothing else.
#
# Needs sampling/lab.py from Step 3 (it borrows the model, the tokenizer and PROMPTS from there).
# There is nothing to edit in this file.
import sys
from pathlib import Path
import torch
from torch.nn import functional as F          # F has the functions: softmax

# Path(__file__) is this file; .parent.parent is two folders up, the repo root. Adding the root to
# sys.path is what lets the next line say "from sampling.lab" from inside the scratch folder.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sampling.lab import model, enc, PROMPTS, pick_prompts   # the same GPT-2 and tokenizer lab.py uses

num_return_sequences = 5      # his first two lines. His max_length counts the prompt; his prompt is 8 tokens
max_length = 50               # and yours is 20, so 50 here gives thirty new tokens, the same as lab.py's n_new=30

# his device detection, from the end of the segment: a GPU if there is one, Apple's "mps" on a Mac, else the CPU
device = "cpu"
if torch.cuda.is_available():
    device = "cuda"
elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
    device = "mps"
print("using device:", device)
model.to(device)                              # move the weights to that device

# the prompt: the first string in PROMPTS, or, if PROMPTS is still empty, the first string "pick" would print
if PROMPTS:
    prompt = PROMPTS[0]
else:
    prompt = pick_prompts()[0]
print("prompt:", repr(prompt))

tokens = enc.encode(prompt)                                  # his "prefix tokens": the prompt as GPT-2 token ids
tokens = torch.tensor(tokens, dtype=torch.long)              # the same ids as a tensor of shape (T,)
tokens = tokens.unsqueeze(0).repeat(num_return_sequences, 1) # (5, T): the same prompt five times, one row each
x = tokens.to(device)
print("x", tuple(x.shape))

torch.manual_seed(42)                         # his seed, so the random draws below repeat run to run
if device == "cuda":
    torch.cuda.manual_seed(42)

while x.size(1) < max_length:                 # x.size(1) is T, the length of each row; stop at 50
    with torch.no_grad():                     # no gradients: we are only reading the model, not training it
        logits = model(x).logits                   # his line is  logits = model(x). Hugging Face returns an object; .logits is the tensor
        logits = logits[:, -1, :]                  # (5, 50257): only the last position predicts the next token
        probs = F.softmax(logits, dim=-1)          # scores -> probabilities, one row per sequence, each row sums to one
        topk_probs, topk_indices = torch.topk(probs, 50, dim=-1)   # (5, 50) each: the 50 most likely, and which tokens they are
        ix = torch.multinomial(topk_probs, 1)      # (5, 1): one draw among the 50, weighted by probability. This is top-k.
        xcol = torch.gather(topk_indices, -1, ix)  # (5, 1): the token id each draw stands for
        x = torch.cat((x, xcol), dim=1)            # append it to every row; T grows by one

print(f"x after the loop {tuple(x.shape)}: {max_length - tokens.shape[1]} new tokens per row\n")
for i in range(num_return_sequences):         # one line per row
    out = x[i, :max_length].tolist()          # row i as a plain list of ids
    print(">", repr(enc.decode(out)))         # ids back to text; repr shows newlines as \n
