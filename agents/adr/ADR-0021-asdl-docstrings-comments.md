# ADR-0021: Comment-based docstrings for ASDL documentation

Status: Proposed

## Context
ASDL designs already embed design intent in YAML comments. We want low-friction
authoring and to render Markdown (and later Sphinx) documentation without
forcing explicit `doc` fields. Standard YAML parsers drop comments, so any
solution must define extraction rules and rely on a comment-preserving parser.

## Decision
- Use YAML comment blocks (consecutive `#` lines) immediately above a key at the
  same indentation as that key as the docstring for that key.
- Inline comments on `key: value # ...` attach to that key and append to any
  preceding block docstring.
- Section headers (comment blocks within a mapping) apply to the contiguous run
  of 2+ key/value pairs until a blank line, a new comment block at the same
  indent, or a dedent. Render these as grouped docs (e.g., net bundles).
- Extraction uses a comment-preserving parser (ruamel.yaml) against the raw
  ASDL source; comments are not part of the AST schema.
- Allow future structured doc metadata (`doc`/`metadata`) as an additive
  extension, not required for the MVP docstring flow.

## Consequences
- Documentation generation depends on comment preservation and indentation
  stability; tools must avoid stripping comments.
- Inline and section comments become part of the public docs; authors should
  keep them accurate and concise.
- Docs generation remains independent of core AST validation and lowering.

## Alternatives
- Add ubiquitous `doc` fields to the ASDL schema (more explicit but higher
  authoring overhead).
- Maintain separate Markdown docs detached from ASDL sources (risk drift).
