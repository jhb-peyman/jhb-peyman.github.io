# How to update your website and CV

You only ever edit **one file**: `content.toml`. Your website, your CV PDF and your CV **Word file** are all built from it, so they can never disagree.

## The three steps

1. **Edit** `content.toml` in any text editor (TextEdit works: choose Format, then Make Plain Text) and save it.
2. **Double-click `Build.command`.** It rebuilds the site and the CV, then opens both so you can look. If you made a typing mistake, it tells you the line or the entry to fix, and nothing is touched.
3. **Double-click `Publish.command`.** It shows what changed, waits for you to press Return, and puts it online. The live site updates about a minute later.

The first time you double-click a `.command` file, macOS may refuse. Right-click it, choose Open, then Open again. You only do this once per file.

You never edit `index.html`, `sitemap.xml`, `og.jpg`, `Peyman_Jahanbin_CV.pdf` or `Peyman_Jahanbin_CV.docx` by hand. They are rebuilt every time and your edits to them would be overwritten.

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
Add a `[[news]]` block at the top. Keep about five. Delete the oldest when you add one.

### Add a presentation
Add a `[[presentations]]` block at the top. If it has a DOI and you want cite buttons, also give it `id`, `doi`, `coauthors` and the `cite_*` fields (the AERA entry is a complete example).

### Add or change a course
Courses sit inside the groups under `[[teaching]]`. Copy a course line, edit it, and keep the commas and braces. The CV line `teaching_summary` (under `[cv]`) is typed by hand, so update the number of courses and assignments yourself.

### Add a research statement, teaching statement or any document
Put the PDF in the same folder as `content.toml`, then add a block like this and rebuild:

```
[[documents]]
title = "Research statement"
file  = "Peyman_Jahanbin_Research_Statement.pdf"
```

(Examples are already in the file, commented out. Remove the `#` signs to use them.)

### When you advance to candidacy
Change `status` under `[person]` to `"Ph.D. Candidate"`. That updates the hero line and the share card. Then also update, by hand, the description under `[seo]`, `job_title`, the Education entry text, and the research text if you mention it. Search the file for "student" and "candidacy".

### Different wording on the CV than on the website
Many fields have a CV-only twin that starts with `cv_`: `cv_title`, `cv_text`, `cv_dates`, `cv_terms`, `cv_note`, and so on. When it is present, the CV uses it and the website uses the normal field. Details that appear only in the CV (Research Interests sentence, Methodological Training, header line) live under `[cv]`.

### Add a whole new section (Grants, Workshops, Media, Invited Talks...)
Near the bottom of `content.toml` there is a commented example called `[[extra_sections]]`. Remove the `#` signs, rename it, and fill in its items. It appears on the website after Honors, in the CV before Languages, and in the menu automatically. Add `site = false` or `cv = false` to show it in only one place.

### Remove a section
Delete all of its blocks (or the whole section). It disappears from the website, the menu and the CV, and the section numbers close up by themselves. You can bring it back later by pasting the blocks again. The order of the sections is fixed.

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
| `builder/site.html`, `cv.html`, `og.html`, `fonts/` | the page templates and the fonts for the offline build |
| `index.html`, `Peyman_Jahanbin_CV.pdf`, `Peyman_Jahanbin_CV.docx`, `og.jpg`, `sitemap.xml` | built for you, do not edit |
