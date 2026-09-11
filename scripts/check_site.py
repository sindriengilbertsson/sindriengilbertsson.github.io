#!/usr/bin/env python3
"""Check the built website without contacting external services.

Usage: python scripts/check_site.py [build-directory]
"""

import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urljoin, urlsplit


IDENTITY = "Sindri Engilbertsson"
SITE_HOSTS = {"sindriengilbertsson.github.io"}
REQUIRED_PAGES = ("index.html", "research/index.html", "teaching/index.html")
APPROVED_PDFS = {"files/CV_SindriEngilbertsson.pdf", "files/cartel-fines.pdf"}
PORTRAIT = "images/SindriEngilbertsson.jpg"
FORBIDDEN = re.compile(
    r"avdeev|sindrieng\.github\.io|G-T5NRPXKWYG|googletagmanager\.com|google-analytics\.com",
    re.IGNORECASE,
)


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.text = []
        self.abstracts = []
        self._details = []
        self._summary_depth = 0
        self._hidden_depth = 0

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in {"href", "src"} and value:
                self.links.append(value)
        if tag in {"script", "style"}:
            self._hidden_depth += 1
        if tag == "details":
            self._details.append({"summary": [], "body": []})
        elif tag == "summary":
            self._summary_depth += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self._hidden_depth = max(0, self._hidden_depth - 1)
        if tag == "summary":
            self._summary_depth = max(0, self._summary_depth - 1)
        elif tag == "details" and self._details:
            detail = self._details.pop()
            summary = " ".join(detail["summary"]).strip().casefold()
            body = " ".join(detail["body"]).strip()
            if "abstract" in summary and body:
                self.abstracts.append(detail)

    def handle_data(self, data):
        if self._hidden_depth:
            return
        self.text.append(data)
        if self._details:
            field = "summary" if self._summary_depth else "body"
            self._details[-1][field].append(data)


def local_target(build_dir, page_path, link):
    """Resolve relative links and links to this site's public domains."""
    current_url = "https://sindriengilbertsson.github.io/" + page_path.as_posix()
    url = urlsplit(urljoin(current_url, link))
    if url.scheme not in {"http", "https"} or url.hostname not in SITE_HOSTS:
        return None
    target = (build_dir / unquote(url.path).lstrip("/")).resolve()
    if not target.is_relative_to(build_dir):
        raise ValueError("path leaves the website directory")
    if target.is_dir():
        target /= "index.html"
    return target


def check_site(build_dir):
    build_dir = build_dir.resolve()
    problems = []
    parsed = {}
    for html_file in sorted(build_dir.rglob("*.html")):
        relative = html_file.relative_to(build_dir)
        content = html_file.read_text(encoding="utf-8")
        if FORBIDDEN.search(content):
            problems.append(f"{relative}: inherited identity, domain or analytics remains")
        page = Page()
        page.feed(content)
        page.close()
        parsed[relative.as_posix()] = page
        for link in sorted(set(page.links)):
            try:
                target = local_target(build_dir, relative, link)
            except ValueError as error:
                problems.append(f"{relative}: invalid link {link!r}: {error}")
                continue
            if target is not None and not target.is_file():
                problems.append(f"{relative}: missing local target for {link!r}")

    for relative in REQUIRED_PAGES:
        page = parsed.get(relative)
        if page is None:
            problems.append(f"Missing page: {relative}")
        elif IDENTITY.casefold() not in " ".join(" ".join(page.text).split()).casefold():
            problems.append(f"{relative}: expected author identity is absent")

    research = parsed.get("research/index.html")
    if research is not None and len(research.abstracts) < 3:
        problems.append("Research needs at least three nonempty expandable abstracts")

    for relative in sorted(APPROVED_PDFS | {PORTRAIT}):
        asset = build_dir / relative
        if not asset.is_file() or asset.stat().st_size == 0:
            problems.append(f"Missing or empty required asset: {relative}")

    published_pdfs = {
        path.relative_to(build_dir).as_posix()
        for path in build_dir.rglob("*")
        if path.is_file() and path.suffix.casefold() == ".pdf"
    }
    for relative in sorted(published_pdfs - APPROVED_PDFS):
        problems.append(f"Unapproved PDF in published output: {relative}")

    return problems, len(parsed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build_directory", nargs="?", default="_site", type=Path)
    args = parser.parse_args()
    if not args.build_directory.is_dir():
        parser.error(f"Build directory does not exist: {args.build_directory}")
    problems, page_count = check_site(args.build_directory)
    if problems:
        for problem in problems:
            print(f"ERROR: {problem}", file=sys.stderr)
        return 1
    print(f"Checked {page_count} HTML pages, local links, abstracts and approved assets.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
