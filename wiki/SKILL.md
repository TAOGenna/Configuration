---
name: wiki
description: "Ingest sources, query knowledge, or lint the Obsidian wiki. Use when the user says 'ingest', 'wiki', 'add to wiki', 'what do I know about X', or 'lint wiki'. Works from any directory."
---

# Obsidian Wiki Skill

You maintain an LLM-generated wiki inside an Obsidian vault. The wiki synthesizes knowledge from raw notes, articles, URLs, and conversations into structured, interlinked pages.

## Paths (absolute — works from any cwd)

- **Vault root:** `/Users/kenyi/Documents/stuff/`
- **Wiki directory:** `/Users/kenyi/Documents/stuff/wiki/`
- **Schema:** `/Users/kenyi/Documents/stuff/CLAUDE.md`
- **Index:** `/Users/kenyi/Documents/stuff/wiki/index.md`
- **Log:** `/Users/kenyi/Documents/stuff/wiki/log.md`

## First step — always

1. Read `/Users/kenyi/Documents/stuff/CLAUDE.md` to load the full schema (page types, frontmatter format, conventions, workflows).
2. Read `/Users/kenyi/Documents/stuff/wiki/index.md` to know what pages already exist.
3. Then proceed with the appropriate workflow below.

## Workflows

### Ingest (default if user provides a URL, article, idea, or content)

Follow the Ingest workflow from the schema exactly:
1. Read / fetch the source fully.
2. Discuss key takeaways with the user if the source is substantial.
3. Create or update a **Source** page in `wiki/` with a summary.
4. Update or create any relevant **Topic**, **Concept**, **Person**, or **Project** pages the source touches.
5. Add `[[wikilinks]]` between all affected pages.
6. Update `wiki/index.md` with any new pages.
7. Append an entry to `wiki/log.md`.

A single source might touch 5-15 wiki pages. That's expected.

### Query (if user asks a question about their knowledge)

1. Read `wiki/index.md` to find relevant pages.
2. Read those pages and synthesize an answer.
3. If the answer is substantial and reusable, offer to create a new wiki page.

### Lint (if user asks for a health check)

1. Look for contradictions between pages.
2. Find orphan pages (no inbound links).
3. Find mentioned-but-missing pages (referenced in `[[wikilinks]]` but don't exist).
4. Suggest gaps to fill.
5. Log the lint pass.

## Conventions

- File names: lowercase, hyphens for spaces (e.g., `wiki/reinforcement-learning.md`)
- Every wiki page must link to at least one other wiki page
- Keep summaries concise — density of a good Wikipedia article
- Use `> [!note]` callouts for editorial commentary or open questions
- Dates in frontmatter use ISO 8601 (YYYY-MM-DD)
- Sensitive files (STUFF.md, credentials) must never be quoted in wiki pages
- Use `[[wikilinks]]` for ALL links — both between wiki pages and to raw vault files (e.g. `[[Research Ideas/(current)Comma compression challenge]]`). This ensures connections appear in Obsidian's graph view
- When ingesting a raw vault file, append a `## Wiki` backlink footer linking to the wiki pages that reference it (if not already present)
