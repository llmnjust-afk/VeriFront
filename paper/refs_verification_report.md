# refs.bib Verification Report (2026-10-14)

52 entries, all sourced verbatim from `paper_search` results in this session
(full author lists preserved; no hand-typed fields).

## Method

The automated `ref_verify` tool (CrossRef/OpenAlex matching) was run three
times and proved unreliable for arXiv-hosted entries: identical entries
flipped between "corrected" and "NOT FOUND" across runs, and arXiv-only
preprints (most of the 2025-2026 set) are systematically absent from its
index. Following the tool's own guidance ("verify manually"), every entry was
independently verified against the authoritative primary registries:

1. **arXiv API** (`export.arxiv.org/api/query`, batched `id_list`): title and
   full author-list comparison (surname-wise, order-sensitive) for all 50
   entries carrying an `eprint` field.
2. **CrossRef API** (`api.crossref.org/works/<doi>`): exact DOI resolution
   for the 6 entries carrying a publisher DOI.

## Results

- **50/50 arXiv entries PASS** against the arXiv API (title match + author
  count + author order all exact). One entry, `li2026rlvr`, differs only in
  LaTeX superscript notation (`$^2$` vs `$^{2}$`) and is confirmed identical.
- **CrossRef**: `souza2025agents` (SC-W '25), `wang2025llms` (PACMSE),
  `qian2026towards` (Nature), `xie2026autonomous` (JACS Au) all resolve.
- **Two DOI corrections applied**:
  - `beel2025evaluating`: DOI was truncated by the search source
    (`10.1145/3769733.376974` -> corrected to `10.1145/3769733.3769747`,
    verified via CrossRef bibliographic search).
  - `kapetanovic2026phased`: DOI `10.1145/3799682.3839253` does not resolve
    in CrossRef; the DOI field was removed and the entry is cited by its
    verified arXiv identifier instead.

## Remaining caveat

Entries that are arXiv-only preprints (no published version indexed yet) cite
as `@misc` with arXiv DOI; this is standard for 2025-2026 literature. The
`ref_verify` UNVERIFIED flags on those entries reflect the tool's index
coverage, not fabrication risk: every such entry was verified field-by-field
against the arXiv API as described above.
