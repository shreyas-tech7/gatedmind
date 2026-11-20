# Proposals

Ideas that the brief does not ask for. Shreyas picks what gets built.

- Stretch from the brief: an optional OpenFGA backend for the access rules, so the same tuples drive the SQL filter.
- A per-access-set BM25 index, so pre-filtered search does not use word statistics from documents the asker cannot read.
- A real-model record run on a free provider, to see how often a real model paraphrases a forbidden fact in mode 3.
- Questions in looser words (written by people, not templates), to make accuracy a real test of retrieval.
- An n-gram redactor for mode 3, to measure how much fuzzy matching closes the paraphrase gap and how much it over-blocks.
