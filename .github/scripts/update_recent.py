#!/usr/bin/env python3
"""Refresh the "Most-used languages" bar in the profile README.

Computes the language mix across the user's owned public, non-fork repos and
renders it as shields between the LANGS markers. Run weekly by
.github/workflows/update-profile.yml. Uses only the stdlib + GITHUB_TOKEN.
"""
import json
import os
import re
import urllib.request

USER = "BrutalCaeser"
README = "README.md"

LANG_COLORS = {
    "Python": "3776AB", "JavaScript": "F7DF1E", "TypeScript": "3178C6",
    "Shell": "89E051", "C++": "00599C", "SCSS": "CC6699", "HTML": "E34F26",
    "Jupyter Notebook": "DA5B0B", "Java": "ED8B00", "Rust": "DEA584",
}


def api(path):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "profile-updater",
        },
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def lang_bar(repos):
    """Most-used languages across owned public, non-fork repos, as shields."""
    counts = {}
    for r in repos:
        if r["fork"] or r["private"] or r.get("archived"):
            continue
        lang = r.get("language")
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
    total = sum(counts.values())
    if not total:
        return '<p align="center"><sub>—</sub></p>'
    top = sorted(counts.items(), key=lambda kv: -kv[1])[:8]
    badges = []
    for lang, n in top:
        pct = round(100 * n / total)
        color = LANG_COLORS.get(lang, "586069")
        label = lang.replace(" ", "%20").replace("+", "%2B").replace("-", "--")
        badges.append(
            f'<img src="https://img.shields.io/badge/{label}-{pct}%25-{color}'
            f'?style=flat-square&labelColor=0d1117"/>'
        )
    return '<p align="center">\n  ' + "\n  ".join(badges) + "\n</p>"


def replace_block(content, start, end, body):
    block = f"{start}\n{body}\n{end}"
    return re.sub(re.escape(start) + r".*?" + re.escape(end), block, content, flags=re.DOTALL)


def main():
    repos = api(f"/users/{USER}/repos?per_page=100&sort=pushed&type=owner")
    with open(README, encoding="utf-8") as f:
        content = f.read()
    new = replace_block(content, "<!--LANGS:START-->", "<!--LANGS:END-->", lang_bar(repos))
    if new != content:
        with open(README, "w", encoding="utf-8") as f:
            f.write(new)
        print("Updated language bar.")
    else:
        print("No change.")


if __name__ == "__main__":
    main()
