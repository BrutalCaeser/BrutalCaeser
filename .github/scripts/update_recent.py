#!/usr/bin/env python3
"""Regenerate the 'things I've built' section of the profile README.

Pulls the user's most recently pushed public, non-fork repositories and renders
them as a 2-column table between the RECENT_PROJECTS markers. Run weekly by
.github/workflows/update-profile.yml. Uses only the stdlib + GITHUB_TOKEN.
"""
import json
import os
import re
import urllib.request

USER = "BrutalCaeser"
START = "<!--RECENT_PROJECTS:START-->"
END = "<!--RECENT_PROJECTS:END-->"
COUNT = 6
README = "README.md"

# Repos surfaced elsewhere on the profile; skip so the list stays fresh.
SKIP = {"BrutalCaeser", "BrutalCaeser.github.io", "reinforcing_dLLMs",
        "block-diffusion-pareto", "phantom-gradients", "Flow-Language-Model",
        "physical_ai"}

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


def card(repo):
    name = repo["name"]
    desc = (repo.get("description") or "").strip() or "—"
    if len(desc) > 110:
        desc = desc[:107].rstrip() + "…"
    lang = repo.get("language")
    badge = ""
    if lang:
        color = LANG_COLORS.get(lang, "586069")
        label = lang.replace(" ", "%20").replace("+", "%2B")
        badge = f'<br><img src="https://img.shields.io/badge/{label}-{color}?style=flat-square"/>'
    stars = repo.get("stargazers_count", 0)
    star = f" ⭐ {stars}" if stars else ""
    return (
        f'<td align="center" width="50%" valign="top">'
        f'<a href="{repo["html_url"]}"><b>{name}</b></a>{star}<br>'
        f'<sub>{desc}</sub>{badge}</td>'
    )


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
    picks = [
        r for r in repos
        if not r["fork"] and not r["private"] and not r.get("archived")
        and r["name"] not in SKIP
    ][:COUNT]

    rows = []
    for i in range(0, len(picks), 2):
        rows.append("  <tr>\n    " + "\n    ".join(card(r) for r in picks[i:i + 2]) + "\n  </tr>")
    table = "<table>\n" + "\n".join(rows) + "\n</table>"

    with open(README, encoding="utf-8") as f:
        content = f.read()
    new = replace_block(content, START, END, table)
    new = replace_block(new, "<!--LANGS:START-->", "<!--LANGS:END-->", lang_bar(repos))

    if new != content:
        with open(README, "w", encoding="utf-8") as f:
            f.write(new)
        print(f"Updated: {len(picks)} repos + language bar.")
    else:
        print("No change.")


if __name__ == "__main__":
    main()
