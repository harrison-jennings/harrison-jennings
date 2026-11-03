#!/usr/bin/env python3
"""Replace the latest writing section of README.md with the newest posts from the site's RSS feed."""

import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

FEED_URL = "https://www.harrisonjennings.au/rss.xml"
SITE_PREFIX = "https://www.harrisonjennings.au/"
POST_COUNT = 3
README = Path(__file__).resolve().parent.parent / "README.md"
SECTION = re.compile(r"(<!-- posts:start -->\n).*?(<!-- posts:end -->)", re.DOTALL)


def fetch_feed():
    request = urllib.request.Request(FEED_URL, headers={"User-Agent": "profile-readme-updater"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def latest_posts(feed):
    posts = []
    for item in ET.fromstring(feed).iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        published = item.findtext("pubDate")
        if title and link.startswith(SITE_PREFIX) and published:
            posts.append((parsedate_to_datetime(published), title, link))
    posts.sort(key=lambda post: post[0], reverse=True)
    return posts[:POST_COUNT]


def render(posts):
    lines = []
    for _, title, link in posts:
        escaped = title.replace("[", r"\[").replace("]", r"\]")
        lines.append(f"- [{escaped}]({link})\n")
    return "".join(lines)


def main():
    posts = latest_posts(fetch_feed())
    if not posts:
        sys.exit("No posts found in the feed; leaving README.md unchanged.")
    current = README.read_text(encoding="utf-8")
    if not SECTION.search(current):
        sys.exit("Posts markers not found in README.md.")
    section = render(posts)
    README.write_text(
        SECTION.sub(lambda match: match.group(1) + section + match.group(2), current),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
