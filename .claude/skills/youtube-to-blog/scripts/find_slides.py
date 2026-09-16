#!/usr/bin/env python3
"""Find a talk's slide deck, download it, and extract its text page by page.

Usage: find_slides.py <metadata.json> <out-dir> [--pick N] [--url URL]

Where it looks, in order:
  1. Links in the video description: direct .pdf links, GitHub files, GitHub repos (searched).
  2. Known per-year conference slide repos inferred from the title (CppCon, C++Now).
Candidates are ranked by how many title/speaker words they share, and the best match is
downloaded when it is clearly ahead. Otherwise the candidates are listed; rerun with --pick N.
--url skips the search and downloads that PDF directly.

Writes to <out-dir>:
  slides.pdf   the deck
  slides.txt   text per page ("=== page N ===" headers), from pdftotext -layout
  slides.json  every candidate found, with scores, plus links to open by hand
Requires pdftotext (poppler) for the text step.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request

SLIDE_EXT = (".pdf", ".pptx", ".key", ".odp")
MANUAL_HOSTS = ("speakerdeck.com", "slideshare.net", "docs.google.com/presentation",
                "slides.com", "slides.meetingcpp.com", ".github.io")
KNOWN_REPOS = [
    (r"cppcon\s*(20\d\d)", "CppCon/CppCon{}"),
    (r"(?:c\+\+|cpp)\s*now\s*(20\d\d)", "boostcon/cppnow_presentations_{}"),
]
STOP = set("""the a an of and to in on for you do not about with is it how what why your from by at
is are be we our this that my me i vs pdf pptx key odp presentations presentation slides slide talk
lightning keynote conference cppcon accu sea cppnow now meeting ndc goto main blob tree""".split())


def tokens(text):
    text = text.lower().replace("c++", "cpp")
    return {t for t in re.findall(r"[a-z0-9]+", text)
            if len(t) > 1 and t not in STOP and not re.fullmatch(r"20\d\d", t)}


def get_json(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                               "User-Agent": "youtube-to-blog"})
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def search_repo(owner, repo, want, sub=""):
    """Return [(score, raw_url, path)] for slide files in a GitHub repo."""
    try:
        branch = get_json(f"https://api.github.com/repos/{owner}/{repo}")["default_branch"]
        tree = get_json(f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1")
    except Exception as e:  # rate limit, private repo, 404
        print(f"  (could not list {owner}/{repo}: {e})", file=sys.stderr)
        return []
    out = []
    for e in tree.get("tree", []):
        p = e["path"]
        if e["type"] != "blob" or not p.lower().endswith(SLIDE_EXT) or not p.startswith(sub):
            continue
        score = len(tokens(p) & want)
        if score:
            raw = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{urllib.parse.quote(p)}"
            out.append((score, raw, f"{owner}/{repo}: {p}"))
    return out


def collect(meta):
    title = meta.get("title") or ""
    desc = meta.get("description") or ""
    want = tokens(title)
    links = sorted(set(re.findall(r"https?://[^\s\"'<>)\]]+", desc)))
    cands, manual = [], []

    for url in links:
        low = url.lower()
        m = re.match(r"https://github\.com/([^/]+)/([^/#?]+)(?:/(?:blob|tree)/[^/]+/?(.*))?", url)
        if m:
            owner, repo, sub = m.group(1), m.group(2), urllib.parse.unquote(m.group(3) or "")
            if sub.lower().endswith(SLIDE_EXT):  # a direct file link
                raw = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                cands.append((100, raw, f"description link: {sub}"))
            else:
                cands += search_repo(owner, repo, want, sub)
        elif low.split("?")[0].endswith(SLIDE_EXT):
            cands.append((100, url, "description link"))
        elif any(h in low for h in MANUAL_HOSTS):
            manual.append(url)

    for pattern, repo in KNOWN_REPOS:
        m = re.search(pattern, (title + " " + (meta.get("channel") or "")).lower())
        if m:
            owner, name = repo.format(m.group(1)).split("/")
            cands += search_repo(owner, name, want)

    seen, uniq = set(), []
    for c in sorted(cands, key=lambda c: -c[0]):
        if c[1] not in seen:
            seen.add(c[1])
            uniq.append(c)
    return uniq, manual


def download(url, out_dir):
    path = os.path.join(out_dir, "slides.pdf")
    req = urllib.request.Request(url, headers={"User-Agent": "youtube-to-blog"})
    with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
        f.write(r.read())
    return path


def extract(pdf, out_dir):
    proc = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(f"pdftotext failed: {proc.stderr[:500]}")
    pages = proc.stdout.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()

    def lines(page):  # ignore slide numbers/dates so build steps compare equal
        return {re.sub(r"\d+", "", l).strip() for l in page.splitlines()} - {""}

    # A slide revealed line by line appears as several pages, each a subset of the next.
    # Keep only the last, complete step; page numbers stay the PDF's own.
    keep = [(i, p) for i, p in enumerate(pages, 1)
            if i == len(pages) or not lines(p) or not lines(p) <= lines(pages[i])]
    with open(os.path.join(out_dir, "slides.txt"), "w", encoding="utf-8") as f:
        for i, page in keep:
            f.write(f"=== page {i} ===\n{page.rstrip()}\n\n")
    return len(pages), len(keep), sum(len(p.split()) for _, p in keep)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("metadata")
    ap.add_argument("out_dir")
    ap.add_argument("--pick", type=int, help="download candidate N from the list (1-based)")
    ap.add_argument("--url", help="download this PDF URL instead of searching")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    meta = json.load(open(args.metadata, encoding="utf-8"))

    if args.url:
        cands, manual, chosen = [(100, args.url, "given")], [], (100, args.url, "given")
    else:
        cands, manual = collect(meta)
        chosen = None
        if args.pick:
            chosen = cands[args.pick - 1]
        elif cands and cands[0][0] >= 2 and (len(cands) == 1 or cands[0][0] > cands[1][0]):
            chosen = cands[0]

    json.dump({"candidates": [{"score": s, "url": u, "where": w} for s, u, w in cands[:15]],
               "open_by_hand": manual, "chosen": chosen[1] if chosen else None},
              open(os.path.join(args.out_dir, "slides.json"), "w"), indent=2)

    for i, (s, u, w) in enumerate(cands[:8], 1):
        print(f"  [{i}] score {s:>3}  {w}")
    for u in manual:
        print(f"  open by hand: {u}")
    if not chosen:
        print("No clear slide deck found." + (" Rerun with --pick N if one above is right." if cands else ""))
        return
    if not chosen[1].lower().split("?")[0].endswith(".pdf"):
        print(f"Best match is not a PDF; open it by hand: {chosen[1]}")
        return

    pdf = download(chosen[1], args.out_dir)
    n, kept, words = extract(pdf, args.out_dir)
    print(f"slides: {chosen[1]}")
    print(f"saved:  {pdf}  ({n} PDF pages; {kept} after collapsing incremental builds)")
    print(f"text:   {os.path.join(args.out_dir, 'slides.txt')}  (~{words} words)")


if __name__ == "__main__":
    main()
