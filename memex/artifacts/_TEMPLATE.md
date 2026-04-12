---
date: YYYY-MM-DD
depth: full | stub
tags: [relevant, keywords]
source-thread: relative/path/to/thread.md
source: (optional) path or URL to the original external material
summary: One to two sentences. Enough for the agent to decide whether to load the full file.
---

# Artifact Title

Content goes here. Artifacts at `depth: full` are self-contained. Artifacts at `depth: stub` contain a summary and a pointer to external material.

## Source conventions

The `source:` field points to external material that the artifact analyzes or references. Three types:

- **Vault file**: `memex/vault/mathematics/paper-name.pdf` — preferred for research materials, PDFs, notebooks. The vault is gitignored; files stay local.
- **Sibling repo**: `path/to/other-project/docs/something.md` — for living codebases. Use repo-relative paths.
- **URL**: `https://example.com/resource` — for web-accessible material.

When a new external file enters the Memex, copy or move it to the appropriate vault subdirectory. Current vault layout:

```
memex/vault/
  papers/         ← research papers, PDFs
  reference/      ← notebooks, brainstorms, misc reference material
```

Add subdirectories as needed. The vault is organizational infrastructure — keep it clean but don't overthink it. A file in the wrong subdirectory is better than a file in Downloads.
