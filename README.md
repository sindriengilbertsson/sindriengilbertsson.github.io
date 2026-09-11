# Sindri Engilbertsson

Academic website built with Jekyll and AcademicPages, using Stanislav Avdeev’s version of the Minimal Mistakes theme. The theme’s MIT license is retained in LICENSE.

## Content

- `_config.yml`: identity, contact information, site URL.
- `_pages/about.md`: homepage.
- `_pages/publications.md`: research and original abstracts.
- `_pages/teaching.md`: teaching experience.
- `_data/navigation.yml`: navigation and CV download.
- `files/CV_SindriEngilbertsson.pdf`: public CV.
- `files/cartel-fines.pdf`: public cartel-fines paper.
- `images/SindriEngilbertsson.jpg`: portrait.

## Local development

Install Ruby and Bundler, then run `bundle install` and `bundle exec jekyll serve`.

The site uses `https://sindriengilbertsson.github.io` with an empty `baseurl`. In repository Settings → Pages, publish from `master` and `/ (root)`; leave Custom domain empty. The Check website workflow validates pushes to `master` and pull requests.

Only public documents belong in this repository. Research drafts and project notes should stay outside it unless explicitly cleared for publication.
