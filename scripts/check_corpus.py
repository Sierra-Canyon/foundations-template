#!/usr/bin/env python3
"""
Honors Software Engineering — is this a good corpus for the semester?

Run from the top of the repo:   uv run python scripts/check_corpus.py
Or point it at another file:    uv run python scripts/check_corpus.py path/to/file.txt

It checks; it does not fix. Every FAIL says what to do about it. A WARN is
something to decide about, not something wrong. Exit code 1 on any FAIL.

The same checks run as tests:  uv run pytest tests/test_corpus.py -v
"""
import collections
import hashlib
import os
import re
import sys

PASS, WARN, FAIL = "PASS", "WARN", "FAIL"

# ---- the thresholds, in one place, so a student can read them and argue with them
MIN_CHARS = 1_000_000         # Track B trains a GPT on this file; 1 MB is the floor that produces readable text.
                              # Required from A05b on: one book is usually 0.4-0.8 MB, so most corpora are two.
MAX_CHARS_WARN = 20_000_000   # above this every embedding run costs real money and every loop is slow
CHUNK_MIN_CHARS = 200         # A06's minimum chunk length
MIN_CHUNKS = 300              # A06 needs at least this many chunks of at least CHUNK_MIN_CHARS
MAX_DUP_LINE_WARN = 0.10      # fraction of repeated non-trivial lines (boilerplate, nav, OCR echoes)
MAX_DUP_LINE_FAIL = 0.30
MIN_PRINTABLE = 0.985         # anything lower is a PDF, a binary, or an encoding accident
MAX_NON_ASCII_WARN = 0.05     # smart quotes and ligatures from a PDF copy-paste show up here
MAX_DISTINCT_CHARS_WARN = 200 # a character-level model has one output per distinct character
MAX_LINE_LEN_WARN = 20_000    # one giant line means no paragraph structure to chunk on
MIN_TTR = 0.010               # type-token ratio; below this the file repeats itself
MAX_TTR_WARN = 0.30           # above this on a 1 MB file: OCR garbage, random strings, or a word list
MIN_STOPWORD_RATE_WARN = 0.03 # "the of and to a in" share of tokens; English prose sits around 0.15–0.25

STOPWORDS = {"the", "of", "and", "to", "a", "in"}
GUTENBERG_MARKERS = ("*** START OF", "*** END OF", "PROJECT GUTENBERG", "GUTENBERG EBOOK",
                     "www.gutenberg.org")                      # unmistakable: a FAIL
CREDIT_MARKERS = ("Produced by", "Online Distributed Proofreading", "Transcriber's Note")  # a WARN: appears in real text too
EMAIL_RE = re.compile(r"[\w.+-]+@(?!example\.)[\w-]+\.[\w.-]+")   # example.com addresses are documentation, not people
PHONE_RE = re.compile(r"\(?\b\d{3}\)?[-. ]\d{3}[-. ]\d{4}\b")


def load(path):
    with open(path, "rb") as f:
        raw = f.read()
    return raw


def decode(raw):
    """Returns (text, error). Refuses anything that is not UTF-8: fix the file, do not hide the bytes."""
    try:
        return raw.decode("utf-8"), None
    except UnicodeDecodeError as e:
        return None, f"byte {e.start}: {e.reason}"


def chunks_of(text, min_chars=CHUNK_MIN_CHARS):
    """A06's rule: split on blank lines, drop anything shorter than min_chars."""
    parts = re.split(r"\n\s*\n", text)
    return [p.strip() for p in parts if len(p.strip()) >= min_chars]


def tokens_of(text):
    return re.findall(r"[a-z']+", text.lower())


def check(path):
    """Runs every check and returns a list of (name, status, detail, fix)."""
    results = []

    def rec(name, status, detail, fix=""):
        results.append((name, status, detail, fix))

    # 1. exists
    if not os.path.isfile(path):
        rec("file exists", FAIL, f"{path} not found",
            "Your corpus goes at data/corpus.txt. scripts/fetch_corpus.sh should create it.")
        return results
    raw = load(path)

    # 2. UTF-8, no NUL
    text, err = decode(raw)
    if text is None:
        rec("UTF-8 text", FAIL, err,
            "Re-save as UTF-8, or re-download the .txt version rather than the .pdf/.epub. "
            "iconv -f latin1 -t utf-8 in.txt > out.txt converts a Latin-1 file.")
        return results
    if "\x00" in text:
        rec("UTF-8 text", FAIL, "contains NUL bytes: this is a binary file, not text",
            "You downloaded a PDF, a zip, or an HTML page renamed .txt. Get the plain-text version.")
        return results
    rec("UTF-8 text", PASS, f"{len(raw):,} bytes, {len(text):,} characters")

    # 3. size
    n = len(text)
    if n == 0:
        rec("size", FAIL, "0 characters: the file is empty",
            "Whatever wrote it produced nothing. The usual cause is a Gutenberg-style awk rule "
            "('*** START OF' … '*** END OF') run on a file that has no such markers, such as a Wikipedia "
            "corpus, which then keeps nothing. Re-run scripts/fetch_corpus.sh, and only strip what your source actually has.")
        return results
    if n < MIN_CHARS:
        rec("size", FAIL, f"{n:,} characters",
            f"Under {MIN_CHARS:,}; you are {MIN_CHARS - n:,} short. Add more of the same source in the fetch "
            f"script (the sequel, the next volume, another season or category) and run it again. One book "
            f"is usually not enough; two related ones usually are.")
    elif n > MAX_CHARS_WARN:
        rec("size", WARN, f"{n:,} characters",
            "Big. Every embedding pass costs money and every loop takes a while. Cut to the part you care about.")
    else:
        rec("size", PASS, f"{n:,} characters")

    # 4. Gutenberg (or any) boilerplate still attached
    head, tail = text[: max(3000, n // 50)], text[-max(3000, n // 50):]
    hits = [m for m in GUTENBERG_MARKERS if m.lower() in head.lower() or m.lower() in tail.lower()]
    soft = [m for m in CREDIT_MARKERS if m in head or m in tail]          # case-sensitive: "produced by" in prose is not a credit
    if hits:
        rec("boilerplate stripped", FAIL, f"found {hits[:3]} in the first or last 2% of the file",
            "This is a Project Gutenberg download with its license wrapper still on. In fetch_corpus.sh, keep only "
            "the text between the '*** START OF' and '*** END OF' lines (the awk rule in the corpus guide). "
            "Only use that rule on a Gutenberg file: on anything else it keeps nothing.")
    elif soft:
        where = head if any(m in head for m in soft) else tail
        line = next((l.strip() for l in where.split("\n") if any(m in l for m in soft)), "")
        rec("boilerplate stripped", WARN, f"found {soft[:2]} near the {'start' if where is head else 'end'}: {line[:90]!r}",
            "Usually a Gutenberg credits paragraph, but the same words occur in ordinary text (film credits, "
            "acknowledgements). Look at the first and last 40 lines; if it is a credit block, drop it in fetch_corpus.sh, "
            "otherwise leave it.")
    else:
        rec("boilerplate stripped", PASS, "no license header or footer found")

    # 5. printable ratio
    printable = sum(1 for c in text if c.isprintable() or c in "\n\r\t")
    ratio = printable / n
    if ratio < MIN_PRINTABLE:
        rec("printable characters", FAIL, f"{ratio:.3%} printable",
            "Control characters or garbage bytes. Usually a PDF-to-text conversion; find the plain-text source.")
    else:
        rec("printable characters", PASS, f"{ratio:.3%} printable")

    # 6. non-ASCII share
    non_ascii = sum(1 for c in text if ord(c) > 127)
    na = non_ascii / n
    if na > MAX_NON_ASCII_WARN:
        rec("non-ASCII share", WARN, f"{na:.2%} of characters",
            "Fine for a non-English corpus. If the corpus is English, this is smart quotes, ligatures (ﬁ) "
            "or accented OCR. A05 and A06 still work; A03's byte-level tokenizer will spend vocabulary on them.")
    else:
        rec("non-ASCII share", PASS, f"{na:.2%} of characters")

    # 7. distinct characters
    distinct = len(set(text))
    if distinct > MAX_DISTINCT_CHARS_WARN:
        rec("distinct characters", WARN, f"{distinct}",
            "A character-level model has one output per distinct character. Over 200 is usually stray Unicode; "
            "print collections.Counter(text).most_common()[-50:] and decide what to normalize.")
    else:
        rec("distinct characters", PASS, f"{distinct}")

    # 8. structure: chunks
    cs = chunks_of(text)
    lens = sorted(len(c) for c in cs)
    med = lens[len(lens) // 2] if lens else 0
    if len(cs) < MIN_CHUNKS:
        rec("chunks (blank-line split, ≥200 chars)", FAIL, f"{len(cs)} chunks, median {med} chars",
            "A06 needs 300. Either the file has no blank lines between paragraphs (one giant block: see the "
            "next check) or it is too short. If paragraphs are separated by single newlines, run "
            "sed 's/^$/\\n/' or re-wrap in fetch_corpus.sh.")
    else:
        rec("chunks (blank-line split, ≥200 chars)", PASS, f"{len(cs)} chunks, median {med} chars, longest {lens[-1]}")

    # 9. giant lines
    longest_line = max((len(l) for l in text.split("\n")), default=0)
    if longest_line > MAX_LINE_LEN_WARN:
        rec("longest line", WARN, f"{longest_line:,} characters",
            "One paragraph per line with no blank lines, or the whole file on one line. Chunking on blank lines "
            "will produce a few enormous chunks. Insert a blank line between paragraphs in fetch_corpus.sh.")
    else:
        rec("longest line", PASS, f"{longest_line:,} characters")

    # 10. duplicate lines
    lines = [l.strip() for l in text.split("\n")]
    lines = [l for l in lines if len(l) > 30]
    if lines:
        counts = collections.Counter(lines)
        dup = sum(c - 1 for c in counts.values()) / len(lines)
        top = counts.most_common(1)[0]
        detail = f"{dup:.1%} of non-trivial lines are repeats; most repeated ({top[1]}x): {top[0][:60]!r}"
        if dup > MAX_DUP_LINE_FAIL:
            rec("duplicate lines", FAIL, detail,
                "Navigation menus, page headers, or the same article pasted many times. Remove them in "
                "fetch_corpus.sh; a search engine over this file returns the repeat for every query.")
        elif dup > MAX_DUP_LINE_WARN:
            rec("duplicate lines", WARN, detail,
                "Some boilerplate survived (running heads, 'CHAPTER' lines are fine). Look at the top repeats.")
        else:
            rec("duplicate lines", PASS, detail)

    # 11. vocabulary
    toks = tokens_of(text)
    if toks:
        ttr = len(set(toks)) / len(toks)
        if ttr < MIN_TTR:
            rec("vocabulary (type-token ratio)", FAIL, f"{ttr:.4f} over {len(toks):,} tokens",
                "The file repeats itself: a log, a table, or one paragraph copied. Pick prose.")
        elif ttr > MAX_TTR_WARN and len(toks) > 50_000:
            rec("vocabulary (type-token ratio)", WARN, f"{ttr:.4f} over {len(toks):,} tokens",
                "Very high for this size: OCR errors, random identifiers, or a list rather than text. "
                "Fine if that is what you meant (code, chess games). Not fine if it is supposed to be a book.")
        else:
            rec("vocabulary (type-token ratio)", PASS, f"{ttr:.4f} over {len(toks):,} tokens, {len(set(toks)):,} distinct")

        # 12. English-prose signal (WARN only: non-English and non-prose corpora are allowed)
        sw = sum(1 for t in toks if t in STOPWORDS) / len(toks)
        if sw < MIN_STOPWORD_RATE_WARN:
            rec("reads like English prose", WARN, f"stopword share {sw:.1%}",
                "Not English prose (code, notation, another language, a table). Allowed. Know that A03–A09 "
                "examples assume English; write in data/SOURCE.md what you expect to be different.")
        else:
            rec("reads like English prose", PASS, f"stopword share {sw:.1%}")

    # 13. personal data
    emails, phones = len(EMAIL_RE.findall(text)), len(PHONE_RE.findall(text))
    if emails or phones:
        rec("personal data", WARN, f"{emails} email-like, {phones} phone-like strings",
            "data/ is git-ignored, but you will paste search results and model outputs into committed files "
            "all year. If this is your own chat log or notes, scrub it now, not in November.")
    else:
        rec("personal data", PASS, "no email or phone patterns")

    # 14. provenance
    root = os.path.dirname(os.path.dirname(os.path.abspath(path)))
    src = os.path.join(root, "data", "SOURCE.md")
    fetch = os.path.join(root, "scripts", "fetch_corpus.sh")
    sha = hashlib.sha256(raw).hexdigest()
    if not os.path.isfile(src):
        rec("data/SOURCE.md", FAIL, "missing",
            "Title, URL, license, the date you fetched it, and the sha256 below. Committed; the corpus itself is not.")
    else:
        s = open(src, encoding="utf-8", errors="replace").read()
        missing = [k for k in ("http", "icense", "sha256") if k not in s]
        if missing:
            rec("data/SOURCE.md", FAIL, f"present but missing {missing}",
                "SOURCE.md needs a URL, a license line, and the sha256 of corpus.txt.")
        elif sha[:16] not in s:
            rec("data/SOURCE.md", FAIL, f"sha256 in SOURCE.md does not match the file ({sha[:16]}…)",
                "Re-run fetch_corpus.sh, then paste the new hash. If they differ every run, the fetch is not repeatable.")
        else:
            rec("data/SOURCE.md", PASS, "URL, license and matching sha256 present")
    if not os.path.isfile(fetch):
        rec("scripts/fetch_corpus.sh", FAIL, "missing",
            "A script that re-creates data/corpus.txt from the URL. A corpus nobody can re-fetch is a corpus "
            "I cannot re-run your numbers on.")
    else:
        rec("scripts/fetch_corpus.sh", PASS, "present")

    rec("sha256", PASS, sha)
    return results


def report(results):
    width = max(len(r[0]) for r in results) + 2
    print("\n" + "=" * 72)
    print("  HONORS SWE — CORPUS CHECK")
    print("=" * 72)
    fails = warns = 0
    for name, status, detail, fix in results:
        mark = {PASS: "  ok  ", WARN: " warn ", FAIL: " FAIL "}[status]
        print(f"[{mark}] {name.ljust(width)} {detail}")
        if status != PASS and fix:
            print(f"{' ' * (width + 10)}-> {fix}")
        fails += status == FAIL
        warns += status == WARN
    print("=" * 72)
    verdict = "This corpus will carry you through the year." if fails == 0 else "Fix the FAILs, then re-run."
    print(f"  {fails} FAIL, {warns} WARN.  {verdict}")
    print("=" * 72 + "\n")
    return fails


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "data/corpus.txt"
    sys.exit(1 if report(check(target)) else 0)
