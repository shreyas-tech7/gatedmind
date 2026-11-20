# Demo

A real terminal transcript, recorded on 2026-11-20 on seed 1. Person p004 may read the open document d039 about the ember code freeze. The restricted draft twin d256 reads almost the same, with a different date. p004 may not read it.

What to notice: mode 4 shows both dates. Mode 3 removes the cited lines of d256, but its date 2027-07-10 survives in the summary line, and it also removes an allowed d039 line that matches d256 word for word. Modes 2 and 1 never show d256.

## Mode: none

```console
$ gatedmind ask --as p004 --mode none "What is the code freeze date for project ember?"
[d039] The code freeze date for project ember is 2027-01-28.
[d256] The code freeze date for project ember is 2027-07-10.
[d039] Earlier drafts of the code freeze date for project ember are archived.
[d256] Earlier drafts of the code freeze date for project ember are archived.
Summary: code freeze date for project ember: 2027-01-28; code freeze date for project ember: 2027-07-10
-- mode 4 (none), cited ['d039', 'd256'], denied chunks 0
```

## Mode: redact

```console
$ gatedmind ask --as p004 --mode redact "What is the code freeze date for project ember?"
[d039] The code freeze date for project ember is 2027-01-28.
Summary: code freeze date for project ember: 2027-01-28; code freeze date for project ember: 2027-07-10
-- mode 3 (redact), cited ['d039'], denied chunks 2
```

## Mode: postfilter

```console
$ gatedmind ask --as p004 --mode postfilter "What is the code freeze date for project ember?"
[d039] The code freeze date for project ember is 2027-01-28.
[d039] Earlier drafts of the code freeze date for project ember are archived.
Summary: code freeze date for project ember: 2027-01-28
-- mode 2 (postfilter), cited ['d039'], denied chunks 2
```

## Mode: prefilter

```console
$ gatedmind ask --as p004 --mode prefilter "What is the code freeze date for project ember?"
[d039] The code freeze date for project ember is 2027-01-28.
[d039] Earlier drafts of the code freeze date for project ember are archived.
[d174] This note covers the code freeze date for project fjord.
[d174] The code freeze date for project fjord is 2027-04-21.
Summary: code freeze date for project ember: 2027-01-28; code freeze date for project fjord: 2027-04-21
-- mode 1 (prefilter), cited ['d039', 'd174'], denied chunks 712
```

## The MCP server over stdio

The official MCP client starts `gatedmind serve`, lists the tools and calls each tool as an allowed and a forbidden identity.

```console
$ python scripts/mcp_smoke.py
tools: get_doc, search, who_knows

> search as p001 (allowed), error=False
[
 {
  "doc_id": "d012",
  "title": "Insurance renewal date for Q2 2027",
  "snippet": "Last reviewed in September 2026. The insurance renewal date for Q2 2027 is 2027-04-09."
 },
 {
  "doc_id": "d015",
  "title": "Insurance renewal date for Q3 2027",
  "snippet": "The insurance renewal date for Q3 2027 is 2027-11-15. Earlier drafts of the insurance renewal date for Q3 2027 are archived."
 }
]

> get_doc as p001 (allowed), error=False
{
 "doc_id": "d012",
 "title": "Insurance renewal date for Q2 2027",
 "text": "Changes need a second reviewer. Earlier drafts of the insurance renewal date for Q2 2027 are archived. Last reviewed in September 2026. The insurance renewal date for Q2 2027 is 2027-04-09."
}

> who_knows as p001 (allowed), error=False
[
 {
  "person_id": "p014",
  "name": "Abe Sato",
  "dept": "sales",
  "matching_docs": 3
 },
 {
  "person_id": "p021",
  "name": "Vic Ueda",
  "dept": "finance",
  "matching_docs": 2
 },
 {
  "person_id": "p023",
  "name": "Ben Price",
  "dept": "finance",
  "matching_docs": 1
 },
 {
  "person_id": "p017",
  "name": "Ezra Mendez",
  "dept": "sales",
  "matching_docs": 1
 },
 {
  "person_id": "p01 ...

> search as p002 (forbidden), error=False
[
 {
  "doc_id": "d015",
  "title": "Insurance renewal date for Q3 2027",
  "snippet": "The insurance renewal date for Q3 2027 is 2027-11-15. Earlier drafts of the insurance renewal date for Q3 2027 are archived."
 },
 {
  "doc_id": "d056",
  "title": "Renewal date for the Foxglove account",
  "snippet": "The renewal date for the Foxglove account is 2027-10-19. This note covers the renewal date fo ...

> get_doc as p002 (forbidden), error=True
document not found or not allowed

> who_knows as p002 (forbidden), error=False
[
 {
  "person_id": "p018",
  "name": "Sami Ferris",
  "dept": "sales",
  "matching_docs": 2
 },
 {
  "person_id": "p023",
  "name": "Ben Price",
  "dept": "finance",
  "matching_docs": 1
 },
 {
  "person_id": "p017",
  "name": "Ezra Mendez",
  "dept": "sales",
  "matching_docs": 1
 },
 {
  "person_id": "p021",
  "name": "Vic Ueda",
  "dept": "finance",
  "matching_docs": 1
 },
 {
  "person_id": " ...

smoke test: PASS
{"pass": true}
```

## The eval on seed 1 (BM25)

```console
$ gatedmind eval --seed 1 --out /tmp/seed1.json
bm25    prefilter  acc 200/200  leaks   0  overblock   0/122  p50 0.22 ms
bm25    postfilter acc 169/200  leaks   0  overblock  31/122  p50 0.32 ms
bm25    redact     acc  87/200  leaks 128  overblock  36/122  p50 0.26 ms
bm25    none       acc  91/200  leaks 167  overblock  31/122  p50 0.10 ms
wrote /tmp/seed1.json
```
