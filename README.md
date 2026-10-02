# Peyman Jahanbin

Personal academic website: <https://jhb-peyman.github.io>

A static site with no build step. `index.html` holds all of the content and styling.

## Files

- `index.html` is the whole site.
- `Peyman_Jahanbin_CV.pdf` is the downloadable CV.
- `portrait.jpg` is the portrait. `og.jpg` is the card shown when the link is shared.

## Updating the site

Every change goes live about a minute after it is saved to the `main` branch.
Each place you add to has a comment in `index.html` that starts with `ADD`, with a template to copy.

**Add a paper.** Search for `ADD A NEW PAPER`. It takes two steps: paste the paper block at the top of the
list, then add a matching record to the `CITATIONS` block at the bottom of the file. The record powers the
"Copy APA" and "BibTeX" buttons. The publication counts and the topic filter update by themselves.

**Add news.** Search for `ADD NEWS`. Paste a new row at the top and keep the list to about five.

**Add a document to the Dossier** (research statement, teaching statement, and so on). Upload the PDF next to
`index.html`, then search for `ADD A DOCUMENT` and copy a row.

**Add a presentation or a course.** Search for `ADD A PRESENTATION` or `ADD A COURSE`.

**Edit directly on GitHub.** Open `index.html` in the repository, click the pencil icon, make the change,
then choose "Commit changes".

**Replace the CV.** Upload the new PDF with exactly the same file name, `Peyman_Jahanbin_CV.pdf`.

**After advancing to candidacy.** Change "Ph.D. Student" to "Ph.D. Candidate" in three places in
`index.html` (the line above the name, the page description near the top, and `jobTitle` in the
structured data), and rebuild `og.jpg`.

## Notes

- The spectrogram in the hero and the chart in Research are simulations and are labelled as such on the page.
- Both animations stop when they are off screen or when the visitor prefers reduced motion.
