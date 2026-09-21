# search — A06

`search.py` is the file you write. Roughly sixty lines. If you are at two hundred you
have imported something the assignment bans.

**Banned:** Chroma, FAISS, Pinecone, pgvector, LangChain, LlamaIndex, `SentenceTransformer`,
any `VectorStore`, any `.similarity_search()`.
**Allowed:** `numpy`, the standard library, and a direct call to the embeddings endpoint.

The three operations that do the work are the same three you wrote in `embed/probe.py`
last week: normalise, matrix multiply, argsort. Keep that file open beside you.

`RESULTS.md` carries ten queries, top three results each, marked correct or incorrect by
you, plus the keyword-overlap comparison.
