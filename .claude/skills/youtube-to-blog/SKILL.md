---
name: youtube-to-blog
description: Turn a YouTube tech talk (C++, systems programming, or any software engineering topic) into a concise, code-first blog post for this Jekyll blog. It pulls the talk's slide deck when one exists, and compiles and runs every C++ example to confirm what it does. Use this whenever the user shares a youtube.com or youtu.be link and wants a post, write-up, article, notes, or summary of it — including terse requests like "blog this", "write this talk up", or just a pasted conference-talk URL (CppCon, C++Now, ACCU, Meeting C++, GOTO, NDC, Strange Loop, etc.).
---

# YouTube talk → code-first blog post

The reader should get the talk's key idea in about five minutes, mostly by reading code. The post is not a recap of the talk: it is a short, runnable explanation of the best ideas in it, with links back to the video and slides.

Work in a scratch directory. Nothing but the final post goes into the blog repo.

## Workflow

### 1. Fetch the transcript

```bash
python3 <skill-dir>/scripts/fetch_transcript.py "<url>" <scratch>/<name>
```

This writes `metadata.json` (title, channel, upload date, chapters, description) and `transcript.md`: de-duplicated captions in ~30-second paragraphs with `[hh:mm:ss]` stamps, and chapter headings when the video has them. Read `transcript.md`, not the raw `.vtt` files.

### 2. Find the slides

```bash
python3 <skill-dir>/scripts/find_slides.py <scratch>/<name>/metadata.json <scratch>/<name>
```

Captions keep what the speaker says but lose everything on screen: the exact code, reference tables, and notes like "C++23 only" or "broken". Conferences usually publish the deck, and it is the speaker's own precise version of the talk. So look for it every time before writing.

The script looks in two places:
- **Links in the video description**: direct PDFs, GitHub files, and GitHub slide repos, which it searches (e.g. ACCU's `Digital-Medium/ACCU-On-Sea-Slides-2026`).
- **Known per-year conference repos** inferred from the title: `CppCon/CppCon<year>` and `boostcon/cppnow_presentations_<year>`.

It ranks the files it finds by how many words they share with the talk's title and speaker, then downloads the best match. It writes `slides.pdf`, plus `slides.txt` with the text of each page.
- A slide revealed line by line comes out as several PDF pages. `slides.txt` keeps only the final, complete one.
- The `=== page N ===` headers are the PDF's own page numbers, so you can open the same page in `slides.pdf`.
- Some decks are two-up handouts, with two slides per PDF page. The slide numbers printed on the slides then won't match the PDF page numbers.
- If it lists candidates without choosing one, pick with `--pick N`.
- If you find the deck some other way, pass it with `--url <pdf>`.
- For links it marks "open by hand" (Speaker Deck, Google Slides), try WebFetch.
- If nothing turns up, do one quick web search for `"<talk title>" <speaker> slides`. Then move on with the transcript; many talks, lightning talks especially, have no public deck.

**Using the deck:**
- **Read both.** Read `slides.txt` alongside the transcript: all of it when it's under ~15k words. For longer decks, read the parts the transcript points you to. The slides give the precise code and facts; the transcript gives the reasoning and what the speaker stressed. A slide the speaker skipped over matters less than one they spent five minutes on.
- **Look at tables and diagrams.** `pdftotext` flattens them. When a page in `slides.txt` looks like a table, a diagram, or scrambled columns, Read the PDF page itself, e.g. Read `slides.pdf` with `pages: "34"` (at most 20 pages per call). Tables often carry details the text loses, such as annotations like "caching", "broken", or "C++23" in the margin.
- **Take the API from the slides, but still compile it.** Slide code is the source of truth for how the API is spelled and used, yet it is often never compiled. When a slide is wrong, say so in the post and show the fix. Readers get real value from a verified correction.
- **Bring over reference tables.** Look for tables that sum up a topic: feature vs. standard version, which views cache, compiler support, and so on. These are often the most useful slides in the deck, and readers come back to them. When one covers a topic the post discusses, render it in markdown, trimmed to the rows the post's readers need and keeping annotations like "caching" or "broken". Credit it, e.g. "(table adapted from the slides)", and re-check any claim you can compile. Build the post from a few key slides; it is not a copy of the deck.

### 3. Pick what to keep

Choose one thesis, the sentence the reader should remember, and 3–6 points that each carry that thesis and can be shown in code. Everything else gets cut: the speaker's bio, the agenda, jokes, sponsor spots, side nuances, and Q&A tangents. The deck's section titles are a good map of what the speaker thought mattered.

Cutting is where most of the value comes from. A 90-minute talk still produces a post that reads in five minutes. When a talk is a survey ("things you don't know about C++23"), pick the 5–7 items that are most useful or most surprising, and say in one line that the post covers a selection.

### 4. Write the code

Code carries the explanation, and prose only fills the gaps between listings.

- **Every C++ listing is a complete program**: includes, `main`, and output. When several examples share types, introduce that scaffolding once as a named header (`// scaffolding.hpp`) and `#include` it in each example.
- **Show the progression**: the naive version, what goes wrong, then the fix. Label each case in its heading.
- **Comment only the lines that matter**, at the end of the line: `// <-- temporary dies here`, `// prints 42`, `// UB`.
- **Keep it minimal.** Start from the slide's code when there is a deck, and cut it down to what the point needs.
- **No slides?** Rebuild the code from what the speaker says. When the exact on-screen code matters, grab that frame and Read the PNG. Each frame downloads a short clip, so use this only for the few moments that matter:
  ```bash
  <skill-dir>/scripts/grab_frame.sh "<url>" 00:12:34 <scratch>/<name>/frame-1234.png
  ```

### 5. Verify by compiling and running

A post that teaches C++ with code that doesn't compile does more harm than no post. Compile and run every C++ listing, and record what actually happens:

```bash
clang++ -std=c++23 -Wall -Wextra -O2 case1.cpp -o case1 && ./case1
clang++ -std=c++23 -g -fsanitize=address,undefined case1.cpp -o case1-asan && ./case1-asan
```

- **Newer features.** Apple clang's libc++ lags behind (e.g. `views::stride`, `<generator>`). Try Homebrew LLVM, which uses its own newer libc++ with no extra flags: `/opt/homebrew/opt/llvm/bin/clang++ -std=c++23 ...`. Use `-std=c++2c` for C++26. If neither compiler supports a feature, say so in one line and check the code carefully by hand.
- **UB and bug demos.** Run the sanitizer build and report the real symptom, e.g. "ASan reports `stack-use-after-scope`" or "at `-O2` it prints an empty line". That concrete detail is what makes the post trustworthy.
- **Intentional compile errors.** A listing that is meant to be rejected is fine; sometimes the rejection is the point. Mark the offending line with `// error: <reason>`, and say in the prose which compilers reject it and with what message. When only one or two lines fail, prefer a compiling program with those lines commented out (`// f("x");  // error: no matching function`). Readers can then run the rest.
- **Other compilers.** When the post claims something about GCC or MSVC, or the talk does, check it on Compiler Explorer. Use `g151` for GCC 15.1 and `vcpp_v19_latest_x64` for MSVC:
  ```bash
  curl -s -X POST https://godbolt.org/api/compiler/g151/compile \
    -H 'Content-Type: application/json' -H 'Accept: application/json' \
    -d "$(jq -n --rawfile src case1.cpp '{source:$src, options:{userArguments:"-std=c++23 -O2", filters:{execute:true}}}')"
  ```
  The response has `code` (0 means it compiled) and `execResult.stdout`. You can list compiler IDs at `https://godbolt.org/api/compilers/c++`.
- **Other languages.** Run the code if the toolchain is installed; otherwise review it carefully and note that it wasn't run.

### 6. Write the post

Use the template below. Save it to `_posts/YYYY-MM-DD-<slug>.md` in the blog repo, using today's date unless the user gives one, or to whatever output path the user specifies.

When it's done, extract the code blocks from the saved file and compile them once more. Edits made while writing are where listings drift from the code you tested.

### 7. Report back

Answer in your final message; don't write a report file. Include:
- the file path;
- the thesis in one line;
- the section list;
- whether slides were found, and where;
- a compile/run table (listing → result);
- anything you couldn't verify, and anything the talk or slides got wrong.

## Style

The Sep 7, 2026 post on coroutine lambdas (`_posts/2026-09-07-cpp-immediately-invoked-coroutine-lambdas.md`) is the reference for tone and density. It was edited down from a longer draft: the variant taxonomy and side nuances were cut, and every snippet was made a complete, compiled program with its real `-O2`/ASan behavior recorded.

- **Opening**: the link line, then 1–2 sentences stating the problem or the claim directly. No "In this talk, X discusses…" and no speaker bio.
- **Headings state the point or name the case**, e.g. "Case 2: capture by value — still undefined behaviour" or "`std::expected` replaces the out-parameter". Avoid "Introduction" or "Overview".
- **Prose between listings is short**: 1–3 sentences on *why*. If something takes a paragraph to explain, it probably needs another listing.
- **Write in your own words.** Quote the speaker at most once or twice, briefly, and only when the line sums up the point better than a paraphrase would. The post is commentary that links to the talk, not a transcript of it.
- **Bold** only the one or two phrases per section that a skimmer must not miss.
- **End with `## Summary`**: a table when the post compares variants (form → behaviour → verdict), then 3–5 bullet takeaways.
- **Length: 120–250 lines of markdown.** If a draft runs past 250, cut a whole section, usually the one that needs the most setup or the most unusual toolchain, rather than trimming every section a little. Five sharp sections beat seven thin ones.

## Post template

```markdown
---
layout: single
title: "C++ - <Topic stated as the takeaway> (<Speaker>, <Conference> <Year>)"
date: YYYY-MM-DD 14:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - <topic>
  - <topic>
permalink: "YYYY/MM/DD/<slug>"
---

[<Full video title>](<https://www.youtube.com/watch?v=ID>) ([slides](<deck URL, if found>))

<1–2 sentences: the problem or the claim.>

<Shared scaffolding, if the examples need it, with one sentence on the property that matters.>

## <Case / point 1>

​```cpp
<complete program>
​```

<1–3 sentences: why. Observed behavior.>

## <Case / point 2>
...

## Summary

| Form | Behaviour | Verdict |
|---|---|---|
| ... | ... | ... |

- <takeaway>
- <takeaway>
```

Conventions:
- **Title**: `C++ - ` prefix for C++ talks. For other topics, use a quoted plain title with no prefix, e.g. `"Event Sourcing Without the Framework (Speaker, GOTO 2025)"`. When the talk's name is vague, state the takeaway instead.
- **Slug and file name**: lowercase and hyphenated, starting with `cpp-` for C++ talks and ending in the speaker's name, e.g. `cpp-coroutines-for-dummies-dominic-fischer`. The permalink uses the same slug.
- **Slides link**: the GitHub page for the deck (`https://github.com/<owner>/<repo>/blob/<branch>/<path>`) reads better than the raw download URL.
- **Categories**: `cpp` first for C++ talks, then 1–3 existing topic tags where they fit: `coroutines`, `concurrency`, `asynchrony`, `reflection`, `metaprogramming`, `templates`, `lambda`, `memory`, `move-semantics`, `concepts`, `api-design`, `static-analysis`, `ranges`, `ai`. Add a new tag only when none of these fits.
- **Conference and year** come from the video title or channel (e.g. "ACCU on Sea 2026", "CppCon 2025"). Use `upload_date` only if neither says.
