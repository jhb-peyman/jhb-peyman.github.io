# Peyman Jahanbin

Personal academic website: <https://jhb-peyman.github.io>

The website, the CV (PDF and Word), the link-preview card and the sitemap are all **built from one file, `content.toml`**.
To change anything, read [HOW_TO_UPDATE.md](HOW_TO_UPDATE.md): edit `content.toml`, double-click `Build.command` to
preview, then `Publish.command` to put it online.

## Files

- `content.toml` is the only file to edit.
- `build.py`, `builder/` (page code, CV template, fonts) and `assets/` (stylesheet, scripts, images) turn it into the site. `Build.command` and `Publish.command` run it.
- The pages (`index.html`, `research.html`, `publications.html`, `teaching.html`, `service.html`, `404.html`), `Peyman_Jahanbin_CV.pdf`, `Peyman_Jahanbin_CV.docx`, `og.jpg` and `sitemap.xml` are generated. Do not edit them by hand.
- `portrait.jpg` is the portrait.

## Notes

- The home spectrogram shows a synthetic voice (labelled as such) and, if the visitor allows it, their own microphone; the recording stays in the page. The scorer chart on Research is a labelled illustration.
- The paper figures on Publications and the console on Research use numbers reported in the papers.
- Animations stop when they are off screen or when the visitor prefers reduced motion.
- The site itself needs no build step to be served: GitHub Pages just serves the generated files.
