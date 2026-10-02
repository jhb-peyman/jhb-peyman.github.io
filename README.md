# Peyman Jahanbin

Personal academic website: <https://jhb-peyman.github.io>

The website, the CV PDF, the link-preview card and the sitemap are all **built from one file, `content.toml`**.
To change anything, read [HOW_TO_UPDATE.md](HOW_TO_UPDATE.md): edit `content.toml`, double-click `Build.command` to
preview, then `Publish.command` to put it online.

## Files

- `content.toml` is the only file to edit.
- `build.py` and `builder/` (templates and fonts) turn it into the site. `Build.command` and `Publish.command` run it.
- `index.html`, `Peyman_Jahanbin_CV.pdf`, `og.jpg` and `sitemap.xml` are generated. Do not edit them by hand.
- `portrait.jpg` is the portrait.

## Notes

- The spectrogram in the hero and the chart in Research are simulations and are labelled as such on the page.
- Both animations stop when they are off screen or when the visitor prefers reduced motion.
- The site itself needs no build step to be served: GitHub Pages just serves the generated files.
