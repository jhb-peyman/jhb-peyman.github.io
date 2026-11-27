# How to update your website and CV

You only ever edit **one file**: `content.toml`. Your website, your CV PDF and your CV **Word file** are all built from it, so they can never disagree.

## The three steps

1. **Edit** `content.toml` in a plain-text editor and save it. In TextEdit, first choose Format, then Make Plain Text, and turn off smart quotes (Edit, Substitutions, untick Smart Quotes), because curly quotes break the file. Typing a curly apostrophe or quote *inside* your text, such as in “Students’ English”, is fine; only the quotes that wrap the text must be straight. Don't use Word or Pages for this file.
2. **Double-click `Build.command`.** It rebuilds the site and the CV, then opens both so you can look. If you made a typing mistake, it tells you the line or the entry to fix, and nothing is touched.
3. **Double-click `Publish.command`.** It shows what changed, waits for you to press Return, and puts it online. The live site updates about a minute later.

The first time you double-click a `.command` file, macOS may refuse. Right-click it, choose Open, then Open again. You only do this once per file.

You never edit the website pages (`index.html`, `research.html`, `publications.html`, `teaching.html`, `service.html`, `404.html`), `sitemap.xml`, `og.jpg`, `Peyman_Jahanbin_CV.pdf` or `Peyman_Jahanbin_CV.docx` by hand. They are rebuilt every time and your edits to them would be overwritten.

## Rules of the file

- Text goes in double quotes: `title = "My new paper"`
- `*stars*` make italics: `text = "Published in *TESOL Quarterly*."`
- A line that starts with `#` is a note to yourself and is ignored.
- A line like `[[publications]]` starts a **new entry** in a list. To **add** something, copy a whole block (from its `[[...]]` line to the blank line after it), paste it, and change the words. To **remove** something, delete its whole block. Newest entries go first.
- Leave a field out, or set it to `""`, when it does not apply.
- If the text itself needs double quotes, wrap it in single quotes instead: `cite_title = '"The accent hides the knowledge"'`

## Recipes

### Add a new paper
Copy any `[[publications]]` block to the top of the publications list and edit it.

| Field | What to put |
| --- | --- |
| `id` | a short unique word, such as `"newpaper"` |
| `status` | `"published"`, `"review"` (under review) or `"preprint"` |
| `year`, `title` | the year and the title in title case |
| `cite_title` | the same title in sentence case; the Copy APA and BibTeX buttons use it |
| `authors` | `"Given Family"` for each author, in order (your own name turns bold by itself; see the note below for names written family-name-first) |
| `venue`, `volume`, `issue`, `pages`, `doi` | journal details. Leave out what you do not have |
| `topics` | one or more of the topic keys (assessment, speech, ai, policy, classroom, corpus) |

A name written family-name-first (as on some co-authors' papers) takes two forms separated by a vertical bar: how it is shown, then how it is cited. For example `"Fan Qihang | Fan, Qihang"`.

The counts on the filter buttons and the topic filter update by themselves. In the CV, the paper lands in the right group (published, in review, preprints) by itself.

A paper under review also takes `label` (the small text on the site, such as `"Submitted Jan 2027"`) and `cv_status` (the line in the CV).

### A paper gets its volume and issue
Online first means the paper has no issue yet (`online = true`, cited as "Advance online publication."). When the issue arrives, add `volume`, `issue` and `pages`, and delete the `online = true` line.

### A paper moves from "in review" to published
Change `status` to `"published"`, add the venue details and DOI, and delete `label` and `cv_status`.

### Add news
Add a `[[news]]` block at the top. The home page shows the newest six; older ones stay in the file but drop off the page, so delete them now and then.

### Add a presentation
Add a `[[presentations]]` block at the top. If it has a DOI and you want cite buttons, also give it `id`, `doi`, `coauthors` and the `cite_*` fields (the AERA entry is a complete example).

### Add or change a course
Each course is a `[[teaching.courses]]` block under its group (`[[teaching]]` with `group = "Graduate"` and so on). Copy a block and edit it.

| Field | What it does |
| --- | --- |
| `code`, `title` | the course code and title (site and CV) |
| `terms`, `cv_terms` | the terms as the CV shows them |
| `taught` | **the website's teaching table**: one entry per section, such as `["Fall 2023", "Fall 2023", "Spring 2024"]` for two sections in Fall 2023 and one in Spring 2024. Write terms as `"Spring 2027"`, `"Summer 2026"`, `"Fall 2026"`. |
| `short` | a few words for the table, such as `"Assessment in TESOL"` |
| `summary` | one sentence for the course list |
| `note` | optional: one more sentence under the course |

**Each new semester:** add the new term to `taught` (and to `terms`/`cv_terms` for the CV). Terms after the current one show as already assigned; when the term starts they count as taught by themselves. The section counts, the "most taught first" order, the opening paragraph of the Teaching page all update by themselves.

### Earlier teaching (Iran)
An appointment with a `site_text` line appears under "Teaching in Iran" on the Teaching page. The University of Isfahan entry also lists its `courses`. A teaching award shows as a highlighted box under that entry when its `note` under `[[honors]]` names the same institution and a year (for example `"University of Isfahan · 2019"`).

### Peer review journals
Each journal under `[peer_review]` has a `count` and an `about` line (publisher and scope) shown under it on the Service page. The total updates by itself.

### Add a research statement, teaching statement or any document
Put the PDF in the same folder as `content.toml`, then add a block like this and rebuild:

```
[[documents]]
title = "Research statement"
file  = "Peyman_Jahanbin_Research_Statement.pdf"
```

(Examples are already in the file, commented out. Remove the `#` signs to use them.)

### When your status changes (for example when you graduate)
Change `status` under `[person]`. That updates the line under your name and the share card. Then also update, by hand, the description under `[seo]`, `job_title`, the Education entry text, and any research text that mentions it.

### Rebuild at the start of every term
The pages are fixed files, so sentences about time ("next term", the shaded current term on the Teaching page) only update when you build. Double-click `Build.command` and publish once at the start of each term, even if nothing else changed. Also reword news items about upcoming talks once they have happened.

### Add a research project
Copy a `[[projects]]` block and give it a new `id` (a short word, never reused) and a `strand`: `"scoring"`, `"policy"` or `"ai"` puts it in that section of the Research page; anything else puts it under Other Work. `site_title` and `site_text` are the heading and paragraph on the Research page; without them the `title` and `text` are used. The order inside a section follows the file.

### Talks
Each `[[presentations]]` block has an `id`. The Research page places talks by that id, so you can rename a talk freely; a new talk shows on the Publications page right away, and on the Research page once its id is added there (ask for help).

### Choosing a CV section for an entry
- A paper with `cv_section = "other"` goes under "Other Publications" in the CV instead of its usual group (used for the special-issue paper in an outside-field journal). The website lists it as usual.
- An appointment with `cv_section = "teaching_iran"` goes under "Teaching Experience (Iran)" in the CV instead of "Academic Appointments".
- The two headings can be renamed with `other_publications_heading` and `iran_teaching_heading` under `[cv]`.

### Different wording on the CV than on the website
Many fields have a CV-only twin that starts with `cv_`: `cv_title`, `cv_text`, `cv_dates`, `cv_terms`, `cv_note`, and so on. When it is present, the CV uses it and the website uses the normal field. Details that appear only in the CV (Research Interests sentence, Methodological Training, header line) live under `[cv]`.

### Add a whole new section (Grants, Workshops, Media, Invited Talks...)
Near the bottom of `content.toml` there is a commented example called `[[extra_sections]]`. Remove the `#` signs, rename it, and fill in its items. It appears in the CV before Languages. The website has five fixed pages, so a new section does not appear there by itself; it needs a small change in `builder/web/`.

### What is on the website and what is only in the CV
The website shows: home (photo, research themes, news), Research, Publications (papers and talks), Teaching and Service. Education, methodological training, honors and languages are in the CV only (linked from every page). Removing all blocks of a list removes it from the CV and from the website page that uses it.

### Words that live in the design files, not in content.toml
A few hand-written passages are part of the page design in `builder/web/`: the Research page's prose, its methods-and-data lists and the code examples (`research_page.py`), the three research themes on the home page and the spectrogram caption (`pages.py`), and the short page descriptions for search engines (`PAGE_DESC` in `build.py`). Change them there, or ask for help.

### Change the photo
Replace `portrait.jpg` with a new file of the same name.

### Change your link or email
Under `[person]`. It changes everywhere.

## What you can break, and what happens

- A mistake in the file: the build stops and tells you what to fix. The live site is not touched.
- Publishing something you did not mean to: edit the file and publish again. It goes live a minute later.
- You can always see exactly what changed before it goes online: `Publish.command` lists the changed files and waits for your Return.

## Good to know

- **The Word file (`Peyman_Jahanbin_CV.docx`)** uses Cambria, like your original CV, and has the same sections and wording as the PDF. Word can open and tweak it freely (for one-off versions for a specific job, for example), but a hand-edited copy is not connected to `content.toml`: the next build writes a fresh one over it, so save one-off edits under a different file name.
- **The CV PDF is built with a free font (Caladea), not Cambria.** Caladea is designed to match Cambria's measurements, so the layout is the same, but the letter shapes are slightly different from your Word original. Keep your Word file if you want the exact original look.
- The footer date ("Updated October 2026") and the sitemap date update by themselves every time you build.
- The PDF is only rebuilt when something in it changed, so publishing twice in a row does not create noise.
- Building the CV and the share card needs Google Chrome installed. The website itself builds without it (`python3 build.py --no-pdf`).
- Everything in this folder is public once published (including `content.toml`), so keep private notes elsewhere.

## Folder map

| File | What it is |
| --- | --- |
| `content.toml` | **the only file you edit** |
| `Build.command`, `Publish.command` | double-click to preview and to publish |
| `build.py` | the program that builds everything |
| `builder/web/` | the website's page code (one file per page) |
| `assets/` | the website's stylesheet, scripts and images |
| `builder/cv.html`, `og.html`, `fonts/` | the CV and share-card templates and the fonts for the offline build |
| `builder/site.html` | the old one-page design, no longer used |
| `index.html`, `research.html`, `publications.html`, `teaching.html`, `service.html`, `404.html`, `Peyman_Jahanbin_CV.pdf`, `Peyman_Jahanbin_CV.docx`, `og.jpg`, `sitemap.xml` | built for you, do not edit |
