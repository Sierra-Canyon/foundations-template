# Choosing a Corpus
### Honors Software Engineering · 2026–27 · sources by interest, with the command that fetches each one

One text file, `data/corpus.txt`, carries you from A05b to the symposium. This is the menu. Pick something you will not mind reading five hundred search results from, because you will.

## What makes a corpus good (the checker enforces all of this)

| Property | Why | Number |
|---|---|---|
| Big | A search has something to find; a spring GPT produces readable text | ≥ 1,000,000 characters (warns below; fails under 200,000). 1–5 MB is the sweet spot |
| Plain UTF-8 text | The chunker and tokenizer read text, not PDF | `file data/corpus.txt` says UTF-8 or ASCII |
| Paragraphs separated by blank lines | A06 chunks on `\n\n` | ≥ 300 chunks of ≥ 200 characters |
| No license wrapper | Otherwise "Gutenberg" is a top hit all year | the `awk` rule in `fetch_corpus.sh` |
| Not mostly repeats | Navigation, running heads and OCR echoes poison search | < 10% duplicate lines |
| Legal, and shareable in excerpts | You paste results into committed files all year | public domain, CC BY / CC BY-SA, or your own |
| Re-fetchable | I re-run your numbers | `scripts/fetch_corpus.sh` reproduces the same sha256 |

**Size guide.** A novel is 400,000–1,200,000 characters. The Odyssey (Butler) is about 700,000, which is why the examples say "add the Iliad if you go Track B." The complete Shakespeare is 5.5 MB, which is plenty and slow. Two or three related books glued together is usually the right answer.

**Rule on private text.** Your own notes, chats and journals are allowed and are the most interesting corpora in the room. `data/` is git-ignored, but your search results, your model's outputs and your golden set are not: excerpts land in committed files, PR bodies and reflection answers. Scrub names, or pick something else.

**Non-English and non-prose corpora** (code, chess, another language) are allowed. The checker warns rather than fails; write in `SOURCE.md` what you expect to be different (tokenization, stopwords, what "a sentence" means).

---

## Project Gutenberg — literature, history, science, food (public domain)

The plain-text URL pattern is `https://www.gutenberg.org/cache/epub/<ID>/pg<ID>.txt`. Find the ID by searching [gutenberg.org](https://www.gutenberg.org); it is the number in the book's URL. **Verify the ID by reading the first 40 lines of what you downloaded**, then let your own test in `tests/test_corpus.py` guard it forever.

Fetch and strip, the same way every time:

```bash
#!/bin/bash
set -e
mkdir -p data
ID=1727   # the Odyssey, Butler translation
curl -sSL "https://www.gutenberg.org/cache/epub/$ID/pg$ID.txt" -o data/raw.txt
awk '/\*\*\* START OF/{flag=1; next} /\*\*\* END OF/{flag=0} flag' data/raw.txt > data/corpus.txt
rm data/raw.txt
```

**The `awk` rule is for Gutenberg files only.** It keeps what sits between the two marker lines; run it on a file with no markers (Wikipedia, RFCs, docs) and it keeps nothing, and the checker will tell you the corpus is empty. To glue two books, fetch each to `data/raw1.txt`, `data/raw2.txt`, apply the `awk` to each, and `cat` them into `corpus.txt`. Older files carry a "Produced by …" credit *after* the START marker; if the checker flags it, add `sed '1,/^$/d'` to drop the first paragraph.

| Interest | Books (IDs to confirm on the site) | Rough size |
|---|---|---|
| **Epic / myth** | The Odyssey, Butler (1727) · The Iliad, Butler (6130) · Beowulf (16328) · Bulfinch's Mythology (4928) | 0.7 MB each; Odyssey + Iliad ≈ 1.6 MB |
| **Novels** | Moby Dick (2701, 1.2 MB) · War and Peace (2600, 3.2 MB) · Pride and Prejudice (1342, 0.7 MB) · Dracula (345, 0.9 MB) · Frankenstein (84, 0.4 MB) · The Adventures of Sherlock Holmes (1661, 0.6 MB) + The Memoirs (834) + The Return (108) | one novel is usually 0.5–1.2 MB |
| **Complete Shakespeare** | 100 | 5.5 MB; cut to the tragedies if it is slow |
| **History — ancient** | Herodotus, *The Histories* (2707 vol. 1, 2456 vol. 2) · Thucydides, *Peloponnesian War* (7142) · Plutarch's *Lives* (674) · Gibbon, *Decline and Fall* vol. 1 (25717) | 0.8–1.5 MB each |
| **History — American** | The Federalist Papers (1404, 1.2 MB) · Grant's *Personal Memoirs* (4367, 1.5 MB) · Frederick Douglass, *Narrative* (23) + *My Bondage and My Freedom* (202) · Lincoln's speeches and writings (search "Lincoln" — several volumes) | Federalist alone is enough |
| **Science** | Darwin, *On the Origin of Species* (1228, 0.9 MB) + *The Voyage of the Beagle* (944) · Newton's *Opticks* (search) · Faraday, *The Chemical History of a Candle* (14474) | Darwin pair ≈ 1.7 MB |
| **Philosophy** | Plato, *The Republic* (1497) · Marcus Aurelius, *Meditations* (2680) · Thoreau, *Walden* (205) | 0.4–1.2 MB |
| **Food** | Fannie Farmer, *The Boston Cooking-School Cook Book* (search) · Escoffier, *A Guide to Modern Cookery* (search) · any pre-1929 cookbook | recipes chunk beautifully; headings repeat, which is fine |
| **Sports (old)** | Christy Mathewson, *Pitching in a Pinch* (search) · Spalding's baseball guides · A. G. Spalding, *America's National Game* (search) | 0.3–0.8 MB; pair two |

---

## Wikipedia — sports, games, film, music, current technology (CC BY-SA 4.0; credit it in SOURCE.md)

Any set of related articles. Plain text comes from the API's `extracts` endpoint, one article per request. Put the titles in a file, one per line, and this script assembles the corpus with a blank line between paragraphs and the title as a heading:

```bash
#!/bin/bash
# scripts/fetch_corpus.sh — Wikipedia articles listed in data/titles.txt, one per line
set -e
mkdir -p data
: > data/corpus.txt
# Wikipedia's API policy wants a User-Agent that says who you are and how to reach you.
UA="hse-corpus/1.0 (Sierra Canyon HSE student project; contact: YOUR_EMAIL_HERE)"
n=0
while IFS= read -r title || [ -n "$title" ]; do
  title="${title%$'\r'}"                       # drop a Windows line ending if there is one
  [ -z "$title" ] && continue
  # -f: an HTTP error stops the script with the status code instead of feeding an error page to Python
  # --retry handles the occasional 429 (too many requests) by waiting and trying again
  if ! body=$(curl -fsS --max-time 30 --retry 4 --retry-delay 3 --retry-all-errors -G "https://en.wikipedia.org/w/api.php" \
        --data-urlencode "action=query" --data-urlencode "prop=extracts" \
        --data-urlencode "explaintext=1" --data-urlencode "format=json" \
        --data-urlencode "formatversion=2" --data-urlencode "redirects=1" \
        --data-urlencode "titles=$title" -H "User-Agent: $UA"); then
    echo "FAILED on '$title' (curl exit $?). Are you online, and did you set YOUR_EMAIL_HERE?" >&2
    exit 1
  fi
  printf '%s' "$body" | python3 -c '
import json, sys
raw = sys.stdin.read()
try:
    d = json.loads(raw)
except json.JSONDecodeError:
    sys.exit("Wikipedia did not return JSON. First 200 characters of what it sent:\n" + raw[:200])
page = d["query"]["pages"][0]
if page.get("missing"):
    sys.exit("No such article: " + page.get("title", "?"))
print("== " + page["title"] + " ==\n")
print(page.get("extract", ""))
' >> data/corpus.txt
  printf "\n\n" >> data/corpus.txt
  n=$((n + 1))
  sleep 1
done < data/titles.txt
echo "$n articles"
wc -c data/corpus.txt
```

Put your real email in `UA` (Wikipedia blocks anonymous scripts), and commit `data/titles.txt` (add `!data/titles.txt` to `.gitignore`). Section headings come out as `== Heading ==`; leave them, they are useful anchors for the golden set. If it stops with `FAILED on`, read the line above it: a `403` is the User-Agent, a `000` or a timeout is the network, and `No such article` is a title spelled differently from the page's real name (use the exact title from the article URL, with underscores or spaces, either works).

| Interest | `data/titles.txt` | Rough size |
|---|---|---|
| **NFL** | `Super Bowl I` … `Super Bowl LX` (60 lines) | ≈ 1.5–2 MB |
| **NBA** | `1980 NBA Finals` … `2026 NBA Finals`, plus `Michael Jordan`, `LeBron James`, `Stephen Curry` | ≈ 1.5 MB |
| **Soccer** | `1930 FIFA World Cup` … `2026 FIFA World Cup` (23 lines) + `UEFA Champions League` finals | ≈ 1.5 MB |
| **Baseball** | `1903 World Series` … `2025 World Series` | ≈ 2 MB |
| **Olympics** | every Summer Olympics article, 1896–2024 | ≈ 2 MB |
| **Formula 1** | every `<year> Formula One World Championship` since 1950 | ≈ 3 MB |
| **Video games** | every mainline entry of one franchise + its developers; or every game in a genre's "List of …" article, one per line | 1–3 MB |
| **Film** | a director's filmography (one article per film) | ≈ 1 MB per 25 films |
| **Music** | an artist's albums, one article each, plus the artist | 0.5–1.5 MB |
| **Space** | every Apollo mission + every Space Shuttle mission | ≈ 2 MB |
| **Technology history** | `History of the Internet`, `ARPANET`, `Unix`, `Linux`, `Python (programming language)`, `JavaScript`, `TCP/IP`, `World Wide Web`, `Git`, `Transformer (deep learning architecture)` … pick 40 | ≈ 1.5 MB |

The simplest way to make a titles list is the category script below; the fallback is to open the category or "List of …" page and copy the link text, one per line.
### Building `titles.txt` from a category or a "List of …" page

You do not have to type titles by hand. Wikipedia keeps sets of articles in two places, and either one can be turned into `data/titles.txt` by the script below.

**A category.** Every article ends with a **Categories:** box. Open one article you know belongs (say [Super Bowl I](https://en.wikipedia.org/wiki/Super_Bowl_I)), scroll to the bottom, and click the category that names the *set* rather than the topic: a category of games, seasons, albums or missions, not of the sport or the artist. Its URL is `https://en.wikipedia.org/wiki/Category:<Name>`; the members are under **Pages in category**, and if what you want is inside a subcategory, click through to that one. Category names have to be exact, so do not type one from memory: `bash scripts/make_titles.sh --categories-of "Super Bowl I"` prints every category that article is in, and you copy the one that names the set.

**A "List of …" page.** Search Wikipedia for *List of* plus your set: [List of Super Bowl champions](https://en.wikipedia.org/wiki/List_of_Super_Bowl_champions), *List of NBA champions*, *List of FIFA World Cup finals*, *List of Apollo missions*, *List of Nintendo Switch games*, *List of Studio Ghibli works*, *List of Marvel Cinematic Universe films*. The table on a list page links every member article, and a list page links to a lot else besides (teams, stadiums, players), so the script takes a second argument: words that every title you want contains. Look at the table first and find what the member titles share: `Super Bowl XLII`, `Super Bowl LIII` all contain `Super Bowl`; `2004 NBA Finals`, `2016 NBA Finals` all contain `NBA Finals`; `Apollo 11`, `Apollo 13` all contain `Apollo`. That shared piece is the filter. Leave it off to get every link on the page and delete the extras in your editor.

```bash
#!/bin/bash
# scripts/make_titles.sh — write data/titles.txt from a Wikipedia category or a "List of …" page
#   bash scripts/make_titles.sh --categories-of "Super Bowl I"      # prints the article's categories, to copy from
#   bash scripts/make_titles.sh "Category:Super Bowl"
#   bash scripts/make_titles.sh "List of Super Bowl champions" "Super Bowl"
#   bash scripts/make_titles.sh "List of NBA champions" "NBA Finals"
#   bash scripts/make_titles.sh "List of Apollo missions" "Apollo"
set -e
PAGE="$1"; KEEP="$2"    # KEEP: keep only titles containing these words (plain text, not a pattern); blank keeps all
[ -z "$PAGE" ] && { echo "usage: bash scripts/make_titles.sh 'Category:Name' | 'List of …' ['words the titles contain']" >&2; exit 1; }
UA="hse-corpus/1.0 (Sierra Canyon HSE student project; contact: YOUR_EMAIL_HERE)"
API="https://en.wikipedia.org/w/api.php"
CURL="curl -fsS --max-time 30 --retry 4 --retry-delay 3 --retry-all-errors -G $API -H User-Agent:$UA"
if [ "$PAGE" = "--categories-of" ]; then       # which categories does this article sit in?
  $CURL --data-urlencode "action=query" --data-urlencode "prop=categories" --data-urlencode "titles=$2" \
    --data-urlencode "clshow=!hidden" --data-urlencode "cllimit=50" --data-urlencode "format=json" --data-urlencode "formatversion=2" \
  | python3 -c 'import json,sys; [print(c["title"]) for c in json.load(sys.stdin)["query"]["pages"][0].get("categories",[])]'
  exit 0
fi
mkdir -p data; : > data/titles.txt

case "$PAGE" in
  Category:*)
    cont=""
    while :; do
      body=$($CURL --data-urlencode "action=query" --data-urlencode "list=categorymembers" \
        --data-urlencode "cmtitle=$PAGE" --data-urlencode "cmtype=page" --data-urlencode "cmnamespace=0" \
        --data-urlencode "cmlimit=500" --data-urlencode "format=json" --data-urlencode "formatversion=2" \
        ${cont:+--data-urlencode "cmcontinue=$cont"})
      printf '%s' "$body" | python3 -c 'import json,sys; [print(m["title"]) for m in json.load(sys.stdin)["query"]["categorymembers"]]' >> data/titles.txt
      cont=$(printf '%s' "$body" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("continue",{}).get("cmcontinue",""))')
      [ -z "$cont" ] && break
    done ;;
  *)
    # every article the list page links to, in page order, keeping only titles that contain $KEEP
    $CURL --data-urlencode "action=parse" --data-urlencode "page=$PAGE" --data-urlencode "prop=links" \
      --data-urlencode "format=json" --data-urlencode "formatversion=2" \
    | python3 -c 'import json,sys
keep = sys.argv[1].lower()
seen = set()
for l in json.load(sys.stdin)["parse"]["links"]:
    t = l["title"]
    if l["ns"] == 0 and l.get("exists") and keep in t.lower() and t not in seen:
        seen.add(t); print(t)' "$KEEP" >> data/titles.txt ;;
esac
wc -l data/titles.txt
if [ ! -s data/titles.txt ]; then
  echo "Nothing came back. Check the exact name: for a category, run  bash scripts/make_titles.sh --categories-of \"<an article in it>\"  and copy one; for a list page, copy the title from the article URL." >&2
  exit 1
fi
```

For a category, `cmtype=page` and `cmnamespace=0` mean only articles come out, no subcategories, files or talk pages. For a list page, red links are dropped and the filter words do the rest; run it with no second argument once to see everything the page links to, then run it again with the words that the titles you want share. Capitalization does not matter. Either way, open `data/titles.txt` afterwards and delete what does not belong: a category often holds an overview article beside its members, and a list page's table can link the same article twice under different names. If the count is under about 40, run the script again for a second category or list and paste the two files together. A count of `0` means the name is not the real one: use `--categories-of` for a category, or copy a list page's title from its URL. Expect a few extras from a list page even with the filter (`Super Bowl Sunday`, `Super Bowl curse`); that is what the delete-in-your-editor pass is for.

---

## Technology — documentation and standards (open licenses)

These are prose about code, which is a good corpus and an honest one: keyword search beats semantic search on exact identifiers, and you get to see that.

**RFCs (public domain-ish; IETF Trust license permits this use).** HTTP, TLS and the classic Internet protocols, as plain text with paragraph structure already in place:

```bash
#!/bin/bash
set -e
mkdir -p data; : > data/corpus.txt
for n in 791 793 1034 1035 2616 5321 6455 7540 8446 9110 9111 9112 9113 9114; do
  curl -sSL "https://www.rfc-editor.org/rfc/rfc$n.txt" >> data/corpus.txt
  printf "\n\n" >> data/corpus.txt
done
# drop the page-break running heads that repeat on every page
sed -i.bak -E '/^RFC [0-9]+ .* [A-Z][a-z]+ [0-9]{4}$/d; /^[A-Za-z].*\[Page [0-9]+\]$/d' data/corpus.txt && rm data/corpus.txt.bak
wc -c data/corpus.txt
```

The `sed` line matters: without it the checker's duplicate-line test fails on the page headers. About 2.5 MB.

**Node.js API docs (MIT).** One Markdown file per module; the rest of this course's agent is written in TypeScript, so this is a corpus you will actually query for real. A sparse clone fetches only the docs folder, a few seconds instead of the whole repository:

```bash
git clone --quiet --depth 1 --filter=blob:none --sparse https://github.com/nodejs/node.git /tmp/node
git -C /tmp/node sparse-checkout set doc/api 2>/dev/null
cat /tmp/node/doc/api/*.md > data/corpus.txt
rm -rf /tmp/node
```

About 4.7 MB. Expect the checker to warn about duplicate lines: every code example starts with the same `import` lines, which puts repeats near 25%. That is real and harmless for search; if you go Track B, know that a character model will learn to write `import { Buffer } from 'node:buffer';` very well.

**The Rust Book (MIT/Apache).** About 1.2 MB of unusually well-written prose:

```bash
git clone --quiet --depth 1 --filter=blob:none --sparse https://github.com/rust-lang/book.git /tmp/book
git -C /tmp/book sparse-checkout set src 2>/dev/null
cat /tmp/book/src/*.md > data/corpus.txt
rm -rf /tmp/book
```

**Python docs (PSF license).** The tutorial on its own is 270 K, too small; the tutorial plus the HOWTO guides is 1.1 MB and reads as one voice:

```bash
git clone --quiet --depth 1 --filter=blob:none --sparse https://github.com/python/cpython.git /tmp/cpython
git -C /tmp/cpython sparse-checkout set Doc/tutorial Doc/howto 2>/dev/null
cat /tmp/cpython/Doc/tutorial/*.rst /tmp/cpython/Doc/howto/*.rst > data/corpus.txt
rm -rf /tmp/cpython
```

`Doc/library/*.rst` is another 7 MB if you want the module reference too; it is drier and more repetitive.

**Git's own docs (GPL-2).** Every man page you have ever half-read, about 1.5 MB. The pages are AsciiDoc (`.adoc`), not `.txt`:

```bash
git clone --quiet --depth 1 --filter=blob:none --sparse https://github.com/git/git.git /tmp/git
git -C /tmp/git sparse-checkout set Documentation 2>/dev/null
cat /tmp/git/Documentation/git-*.adoc > data/corpus.txt
rm -rf /tmp/git
```

**Your own code.** Docstrings and READMEs from repositories you wrote. Allowed if they are yours, and the most personal corpus available; usually too small on its own.

---

## Science — arXiv abstracts (arXiv license permits abstract redistribution with attribution)

Two thousand abstracts from one category, one paragraph each, is a corpus with a very different shape from a novel: short chunks, dense vocabulary, lots of near-duplicates. Good for retrieval, poor for the spring GPT unless you take more.

```bash
#!/bin/bash
# scripts/fetch_corpus.sh — 2,000 arXiv abstracts from one category, 200 per request
set -e
CAT="cs.LG"                      # astro-ph, q-bio, physics.pop-ph, math.HO, cs.CL …
mkdir -p data; : > data/corpus.txt
for start in 0 200 400 600 800 1000 1200 1400 1600 1800; do
  for attempt in 1 2 3; do
    curl -fsS --max-time 60 "https://export.arxiv.org/api/query?search_query=cat:$CAT&start=$start&max_results=200&sortBy=submittedDate&sortOrder=descending" -o data/raw.xml
    grep -q "<entry>" data/raw.xml && break        # arXiv sometimes returns an empty feed; ask again
    sleep 5
  done
  START=$start python3 - <<'PY'
import re, html, os
x = open("data/raw.xml", encoding="utf-8").read()
entries = re.findall(r"<entry>(.*?)</entry>", x, re.S)
with open("data/corpus.txt", "a", encoding="utf-8") as f:
    for e in entries:
        t = re.search(r"<title>(.*?)</title>", e, re.S).group(1)
        a = re.search(r"<summary>(.*?)</summary>", e, re.S).group(1)
        f.write(" ".join(html.unescape(t).split()) + "\n\n" + " ".join(html.unescape(a).split()) + "\n\n")
print(len(entries), "abstracts from offset", os.environ["START"])
PY
  sleep 3                                          # arXiv asks for a pause between requests
done
rm -f data/raw.xml
wc -c data/corpus.txt
```

Change `CAT` for another field. Ten requests of 200 with a pause between them, because one request of 2,000 comes back empty more often than not. About 2 MB.

---

## Games — chess (CC0)

The Lichess open database is CC0. A month of games is gigabytes, so take the first N games of one month. PGN is text: moves, results, and a header per game. A character-level model trained on it learns to write legal-looking chess, which is a memorable spring milestone.

```bash
#!/bin/bash
set -e
mkdir -p data
# a rated-standard month; pick one from https://database.lichess.org/ and paste its URL
URL="https://database.lichess.org/standard/lichess_db_standard_rated_2013-01.pgn.zst"
# head stops reading at 3 MB and the two tools upstream complain about the closed pipe; that is fine
(curl -sSL "$URL" 2>/dev/null | zstd -d 2>/dev/null | head -c 3000000 > data/corpus.txt) || true   # brew install zstd
# PGN games are separated by blank lines already; strip the per-game headers if you only want moves:
# sed -i.bak '/^\[/d' data/corpus.txt
wc -c data/corpus.txt
```

The checker will warn "not English prose" and "high type-token ratio." Both are correct and both are fine; say so in `SOURCE.md`.

---

## Law and government (public domain)

**Supreme Court opinions** via CourtListener's API, or the plain-text opinions at `https://www.courtlistener.com/api/rest/v4/opinions/` (free key). Simpler: Gutenberg carries the Constitution (5), the Declaration (1), and Lincoln; Wikisource carries every State of the Union address (`https://en.wikisource.org/wiki/Portal:State_of_the_Union_Speeches_by_United_States_Presidents`, fetch each page's `?action=raw` URL the same way as the Wikipedia script). The full set of State of the Union addresses is about 4 MB and chunks cleanly by paragraph.

---

## What not to pick

Song lyrics, subtitles, news sites, anything behind a login, anything from a Discord or group chat that is not only yours, textbooks still in copyright, and PDFs. Not because the checker will catch all of them (it will not) but because you will be pasting excerpts into a public-facing repository for eight months, and I will not merge a PR whose evidence file quotes something you had no right to copy.

## Writing `data/SOURCE.md`

```markdown
# Corpus
Title: Super Bowl articles I–LX
URL: https://en.wikipedia.org/ (titles in data/titles.txt)
License: CC BY-SA 4.0, Wikipedia contributors
Fetched: 2026-09-28 by scripts/fetch_corpus.sh
sha256: <the full hash from shasum -a 256 data/corpus.txt>

What I expect to be different: team names and player names repeat across articles, so
keyword search will do well on names and badly on "who won in a blowout"; the == Heading ==
lines will show up as short chunks and I drop them at 200 chars.
```

The checker reads `SOURCE.md` and fails if the URL, the word "license," or a matching sha256 is missing.
