"""
Test cases for your corpus. Run:  uv run pytest tests/test_corpus.py -v

Each test is one thing the rest of the year assumes about data/corpus.txt.
A failing test names the assignment that would break. The last test is yours
to write (see A05b, Extension).
"""
import hashlib
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import check_corpus as cc  # noqa: E402

CORPUS = os.path.join(os.path.dirname(__file__), "..", "data", "corpus.txt")
SOURCE = os.path.join(os.path.dirname(__file__), "..", "data", "SOURCE.md")
FETCH = os.path.join(os.path.dirname(__file__), "..", "scripts", "fetch_corpus.sh")


@pytest.fixture(scope="module")
def raw():
    assert os.path.isfile(CORPUS), "data/corpus.txt is missing; run scripts/fetch_corpus.sh"
    return open(CORPUS, "rb").read()


@pytest.fixture(scope="module")
def text(raw):
    t, err = cc.decode(raw)
    assert t is not None, f"not UTF-8: {err}"
    return t


def test_is_text_not_binary(text):
    """A03's tokenizer and A06's chunker both read this as text."""
    assert "\x00" not in text
    printable = sum(1 for c in text if c.isprintable() or c in "\n\r\t") / len(text)
    assert printable >= cc.MIN_PRINTABLE, f"only {printable:.3%} printable"


def test_big_enough_for_the_fall(text):
    """A06 embeds it; A13–A19 search it."""
    assert len(text) >= cc.MIN_CHARS_FAIL, f"{len(text):,} chars; need {cc.MIN_CHARS_FAIL:,}"


@pytest.mark.xfail(strict=False, reason="Track B's spring GPT wants ≥ 1 MB; a warning in the fall, not a failure")
def test_big_enough_for_a_gpt(text):
    assert len(text) >= cc.MIN_CHARS_WARN


def test_not_empty(text):
    """A file with nothing in it passes every regex and fails every assignment."""
    assert len(text) > 0, "data/corpus.txt is empty; the fetch or the stripping rule produced nothing"


def test_no_license_boilerplate(text):
    """Otherwise every search for 'license' or 'Gutenberg' returns the header, and it embeds as a chunk."""
    n = len(text)
    head, tail = text[: max(3000, n // 50)].lower(), text[-max(3000, n // 50):].lower()
    for m in cc.GUTENBERG_MARKERS:          # the unmistakable ones; credit phrases are only a warning in the checker
        assert m.lower() not in head and m.lower() not in tail, f"found {m!r} at the top or bottom"


def test_enough_chunks_for_a06(text):
    """A06 requires 300 chunks after dropping anything under 200 characters."""
    cs = cc.chunks_of(text)
    assert len(cs) >= cc.MIN_CHUNKS, f"{len(cs)} chunks of ≥{cc.CHUNK_MIN_CHARS} chars; need {cc.MIN_CHUNKS}"


def test_has_paragraph_structure(text):
    """Chunking splits on blank lines; a file with none becomes one chunk."""
    assert re.search(r"\n\s*\n", text), "no blank lines anywhere: nothing to chunk on"
    longest = max(len(l) for l in text.split("\n"))
    assert longest <= cc.MAX_LINE_LEN_WARN * 5, f"a {longest:,}-character line; this is not paragraph text"


def test_not_mostly_repeats(text):
    """A search engine over a file that repeats itself returns the repeat for every query."""
    lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 30]
    import collections
    counts = collections.Counter(lines)
    dup = sum(c - 1 for c in counts.values()) / len(lines)
    assert dup <= cc.MAX_DUP_LINE_FAIL, f"{dup:.1%} of lines are repeats; top: {counts.most_common(1)[0]}"


def test_has_a_vocabulary(text):
    """Embeddings of one paragraph repeated 5,000 times are 5,000 copies of one point."""
    toks = cc.tokens_of(text)
    assert len(toks) > 10_000
    ttr = len(set(toks)) / len(toks)
    assert ttr >= cc.MIN_TTR, f"type-token ratio {ttr:.4f}"


def test_source_md_present_and_matches(raw):
    """I re-run your numbers. That needs the URL, the license, and the hash of the exact file you used."""
    assert os.path.isfile(SOURCE), "data/SOURCE.md missing"
    s = open(SOURCE, encoding="utf-8", errors="replace").read()
    assert "http" in s, "SOURCE.md has no URL"
    assert "icense" in s, "SOURCE.md has no license line"
    sha = hashlib.sha256(raw).hexdigest()
    assert sha[:16] in s, f"SOURCE.md sha256 does not match corpus.txt ({sha[:16]}…)"


def test_fetch_script_present():
    """A corpus that cannot be re-fetched is a corpus nobody can reproduce a result on."""
    assert os.path.isfile(FETCH), "scripts/fetch_corpus.sh missing"
    body = open(FETCH, encoding="utf-8", errors="replace").read()
    assert "corpus.txt" in body, "fetch_corpus.sh does not write data/corpus.txt"


# ---------------------------------------------------------------------------
# Yours. A05b's extension asks for ONE test that is true of YOUR corpus and
# would not be true of a random text: "every book heading 'BOOK ' appears
# exactly 24 times", "no line is longer than 80 characters", "the word
# 'Telemachus' occurs more than 100 times". Replace the body below.
# ---------------------------------------------------------------------------
def test_something_true_of_my_corpus(text):
    pytest.skip("write your own test here (A05b, Extension)")
