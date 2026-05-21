"""Build podcast RSS feed (feed.xml) and per-episode HTML pages.

Run after generate_audio.py:
    python scripts/build_feed.py --base-url https://medassistant-ux.github.io/REPO
"""
from __future__ import annotations

import argparse
import html
import re
from datetime import datetime, timezone, timedelta
from email.utils import format_datetime
from pathlib import Path

from mutagen.mp3 import MP3

ROOT = Path(__file__).resolve().parent.parent
TRANSCRIPTS = ROOT / "transcripts"
AUDIO = ROOT / "audio"
DOCS = ROOT / "docs"
EP_DIR = DOCS / "episodes"

SHOW_TITLE = "PharmD Physical Assessment Audio Course"
SHOW_DESC = (
    "Hands-free study course for Physical Assessment for Pharmacist Clinicians. "
    "Each episode covers learning objectives, core content, drug-related pearls, "
    "red flags, and an audio quiz with pause-and-answer pacing."
)
SHOW_AUTHOR = "Joshua Belcher"
SHOW_EMAIL = "joshua.belcher18@gmail.com"
SHOW_CATEGORY = "Education"
SHOW_LANG = "en-us"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    raw = text[3:end].strip()
    body = text[end + 4 :].lstrip("\n")
    fm: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm, body


def mp3_duration(path: Path) -> int:
    try:
        return int(MP3(str(path)).info.length)
    except Exception:
        return 0


def hms(seconds: int) -> str:
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def md_to_simple_html(body: str) -> str:
    """Minimal markdown to HTML: headings, lists, paragraphs, bold/italic."""
    lines = body.splitlines()
    out: list[str] = []
    in_list = False
    para: list[str] = []

    def flush_para() -> None:
        if para:
            out.append("<p>" + " ".join(para) + "</p>")
            para.clear()

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            flush_para()
            close_list()
            continue
        if line.startswith("### "):
            flush_para(); close_list()
            out.append(f"<h3>{html.escape(line[4:].strip())}</h3>")
            continue
        if line.startswith("## "):
            flush_para(); close_list()
            out.append(f"<h2>{html.escape(line[3:].strip())}</h2>")
            continue
        if line.startswith("# "):
            flush_para(); close_list()
            out.append(f"<h1>{html.escape(line[2:].strip())}</h1>")
            continue
        m = re.match(r"\s*[-*]\s+(.*)", line)
        if m:
            flush_para()
            if not in_list:
                out.append("<ul>")
                in_list = True
            item = inline_md(m.group(1))
            out.append(f"<li>{item}</li>")
            continue
        close_list()
        para.append(inline_md(line))
    flush_para()
    close_list()
    return "\n".join(out)


def inline_md(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    # Remove [pause] markers from displayed transcript
    s = re.sub(r"\[pause(?:=\d+(?:\.\d+)?)?\]", "", s)
    return s


def write_episode_page(meta: dict, body: str, base_url: str, out_path: Path) -> None:
    title = html.escape(meta["title"])
    ep = html.escape(meta["episode"])
    duration = meta["duration_hms"]
    audio_url = f"{base_url}/audio/{meta['mp3']}"
    transcript_html = md_to_simple_html(body)
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Episode {ep}: {title}</title>
<link rel="stylesheet" href="../style.css">
</head>
<body>
<header class="topbar">
  <a href="../index.html" class="back">&larr; All episodes</a>
  <span class="ep-num">Episode {ep}</span>
</header>
<main class="lesson">
  <h1>{title}</h1>
  <p class="meta">Duration: {duration}</p>
  <div class="player">
    <audio controls preload="none" src="{audio_url}"></audio>
    <a class="dl" href="{audio_url}">Download MP3</a>
  </div>
  <article class="transcript">
    {transcript_html}
  </article>
</main>
<footer><a href="../index.html">&larr; All episodes</a> &middot; <a href="../subscribe.html">Subscribe in podcast app</a></footer>
</body>
</html>
"""
    out_path.write_text(page, encoding="utf-8")


def write_index_page(items: list[dict], base_url: str) -> None:
    cards = []
    for it in items:
        cards.append(
            f"""<a class="card" href="episodes/{it['slug']}.html">
  <div class="ep-num">Ep {html.escape(it['episode'])}</div>
  <div class="ep-title">{html.escape(it['title'])}</div>
  <div class="ep-meta">{it['duration_hms']}</div>
  <div class="ep-desc">{html.escape(it.get('summary',''))}</div>
</a>"""
        )
    cards_html = "\n".join(cards)
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{SHOW_TITLE}</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="hero">
  <h1>{SHOW_TITLE}</h1>
  <p class="tagline">Hands-free study for Physical Assessment for Pharmacist Clinicians.</p>
  <div class="actions">
    <a class="btn primary" href="subscribe.html">Subscribe in podcast app</a>
    <a class="btn" href="feed.xml">RSS feed</a>
  </div>
</header>
<main class="ep-list">
  {cards_html}
</main>
<footer>Generated with edge-tts &middot; <a href="https://github.com/MedAssistant-ux">GitHub</a></footer>
</body>
</html>
"""
    (DOCS / "index.html").write_text(page, encoding="utf-8")


def write_subscribe_page(base_url: str) -> None:
    feed_url = f"{base_url}/feed.xml"
    podcast_proto = feed_url.replace("https://", "podcast://").replace("http://", "podcast://")
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Subscribe &mdash; {SHOW_TITLE}</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="topbar"><a href="index.html" class="back">&larr; Home</a></header>
<main class="lesson">
  <h1>Subscribe in your podcast app</h1>
  <p>Tap the button on your phone to open the feed in your default podcast app:</p>
  <p><a class="btn primary big" href="{podcast_proto}">Open in Podcasts app</a></p>

  <h2>Or paste the feed URL manually</h2>
  <p>This works in Apple Podcasts, Pocket Casts, Overcast, Spotify, and others:</p>
  <pre class="feedurl">{feed_url}</pre>

  <h3>Apple Podcasts (iPhone)</h3>
  <ul>
    <li>Open Podcasts &rarr; Library tab</li>
    <li>Tap the three-dots menu (top right) &rarr; <em>Follow a Show by URL</em></li>
    <li>Paste the URL above and tap <em>Follow</em></li>
  </ul>

  <h3>Pocket Casts / Overcast / Castro</h3>
  <ul>
    <li>Search or Add Podcast &rarr; <em>Add by URL</em></li>
    <li>Paste the URL above</li>
  </ul>

  <h3>Hands-free playback in the car</h3>
  <ul>
    <li>Connect phone to car via Bluetooth or CarPlay/Android Auto</li>
    <li>Say "Hey Siri, play {SHOW_TITLE}" (or "Hey Google, play ...")</li>
    <li>Use steering wheel controls to skip/back/pause</li>
  </ul>
</main>
</body>
</html>
"""
    (DOCS / "subscribe.html").write_text(page, encoding="utf-8")


def write_stylesheet() -> None:
    css = """:root {
  --bg: #0f172a;
  --panel: #1e293b;
  --text: #e2e8f0;
  --muted: #94a3b8;
  --accent: #38bdf8;
  --accent-2: #22d3ee;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: var(--bg); color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, system-ui, sans-serif;
  line-height: 1.55; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

.hero { padding: 2rem 1.25rem 1.5rem; text-align: center;
  background: linear-gradient(160deg, #0c4a6e, #0f172a 70%); }
.hero h1 { margin: 0 0 .25rem; font-size: 1.6rem; letter-spacing: -0.01em; }
.hero .tagline { margin: 0 0 1.25rem; color: var(--muted); }
.actions { display:flex; gap:.5rem; justify-content:center; flex-wrap:wrap; }
.btn { display:inline-block; padding:.65rem 1rem; border-radius: 999px;
  background: var(--panel); color: var(--text); border: 1px solid #334155; }
.btn.primary { background: var(--accent); color: #042f3a; border-color: transparent; font-weight:600; }
.btn.big { font-size: 1.1rem; padding: .9rem 1.5rem; }

.topbar { display:flex; justify-content:space-between; align-items:center;
  padding: .9rem 1rem; background: var(--panel); border-bottom: 1px solid #334155; }
.topbar .back { color: var(--accent); }
.topbar .ep-num { color: var(--muted); font-size: .9rem; }

.ep-list { display: grid; gap: .75rem; padding: 1rem; max-width: 720px; margin: 0 auto; }
.card { display:block; padding: 1rem; background: var(--panel);
  border-radius: 12px; border: 1px solid #334155; color: var(--text); }
.card:hover { border-color: var(--accent); text-decoration: none; }
.card .ep-num { font-size: .75rem; color: var(--accent-2); font-weight: 600; letter-spacing: .05em; }
.card .ep-title { font-size: 1.1rem; font-weight: 600; margin: .2rem 0 .15rem; }
.card .ep-meta { font-size: .8rem; color: var(--muted); margin-bottom: .4rem; }
.card .ep-desc { font-size: .9rem; color: var(--muted); }

.lesson { max-width: 720px; margin: 0 auto; padding: 1rem 1.25rem 3rem; }
.lesson h1 { margin: .3rem 0 .25rem; font-size: 1.5rem; }
.lesson .meta { color: var(--muted); margin: 0 0 1rem; font-size:.9rem; }
.player { background: var(--panel); padding: 1rem; border-radius: 12px; margin-bottom: 1.5rem; }
.player audio { width: 100%; }
.player .dl { display:inline-block; margin-top: .6rem; font-size: .85rem; }

.transcript h2 { margin-top: 2rem; color: var(--accent-2); font-size: 1.15rem; }
.transcript h3 { margin-top: 1.25rem; color: var(--text); font-size: 1rem; }
.transcript ul { padding-left: 1.25rem; }
.transcript li { margin: .25rem 0; }
.transcript p { color: #cbd5e1; }
.transcript code { background: #0b1220; padding: .1rem .3rem; border-radius: 4px; font-size: .9em; }

.feedurl { background: #0b1220; padding: .75rem; border-radius: 8px; overflow-x: auto;
  border: 1px solid #334155; font-size:.85rem; }

footer { text-align: center; padding: 2rem 1rem 3rem; color: var(--muted); font-size: .85rem; }
"""
    (DOCS / "style.css").write_text(css, encoding="utf-8")


def write_rss(items: list[dict], base_url: str) -> None:
    now = datetime.now(timezone.utc)
    item_xml_parts = []
    # Older episode # gets older pubDate so podcast apps order correctly
    for i, it in enumerate(items):
        pub = now - timedelta(days=(len(items) - i) * 2)
        pub_rfc = format_datetime(pub)
        title_esc = html.escape(it["title"])
        ep = html.escape(it["episode"])
        desc = html.escape(it.get("summary", ""))
        mp3_url = f"{base_url}/audio/{it['mp3']}"
        size = it["mp3_size"]
        dur = it["duration_hms"]
        guid = f"{base_url}/audio/{it['mp3']}"
        item_xml_parts.append(f"""    <item>
      <title>Ep {ep}: {title_esc}</title>
      <description>{desc}</description>
      <enclosure url="{mp3_url}" length="{size}" type="audio/mpeg"/>
      <guid isPermaLink="false">{guid}</guid>
      <pubDate>{pub_rfc}</pubDate>
      <itunes:author>{SHOW_AUTHOR}</itunes:author>
      <itunes:duration>{dur}</itunes:duration>
      <itunes:episode>{ep}</itunes:episode>
      <itunes:explicit>false</itunes:explicit>
    </item>""")
    items_xml = "\n".join(item_xml_parts)
    last_build = format_datetime(now)
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>{html.escape(SHOW_TITLE)}</title>
    <link>{base_url}</link>
    <language>{SHOW_LANG}</language>
    <description>{html.escape(SHOW_DESC)}</description>
    <itunes:author>{SHOW_AUTHOR}</itunes:author>
    <itunes:summary>{html.escape(SHOW_DESC)}</itunes:summary>
    <itunes:owner>
      <itunes:name>{SHOW_AUTHOR}</itunes:name>
      <itunes:email>{SHOW_EMAIL}</itunes:email>
    </itunes:owner>
    <itunes:explicit>false</itunes:explicit>
    <itunes:category text="{SHOW_CATEGORY}"/>
    <itunes:image href="{base_url}/cover.png"/>
    <lastBuildDate>{last_build}</lastBuildDate>
{items_xml}
  </channel>
</rss>
"""
    (DOCS / "feed.xml").write_text(feed, encoding="utf-8")


def build(base_url: str) -> None:
    EP_DIR.mkdir(parents=True, exist_ok=True)
    items: list[dict] = []
    for md in sorted(TRANSCRIPTS.glob("*.md")):
        fm, body = parse_frontmatter(md.read_text(encoding="utf-8"))
        slug = md.stem
        mp3_name = f"{slug}.mp3"
        mp3_path = AUDIO / mp3_name
        if not mp3_path.exists():
            print(f"  [warn] missing audio for {slug}, skipping in feed")
            continue
        dur_s = mp3_duration(mp3_path)
        meta = {
            "episode": fm.get("episode", slug.split("-")[0]),
            "title": fm.get("title", slug),
            "summary": fm.get("summary", ""),
            "slug": slug,
            "mp3": mp3_name,
            "mp3_size": mp3_path.stat().st_size,
            "duration_hms": hms(dur_s),
        }
        items.append(meta)
        write_episode_page(meta, body, base_url, EP_DIR / f"{slug}.html")

    items.sort(key=lambda x: x["episode"])
    write_index_page(items, base_url)
    write_subscribe_page(base_url)
    write_stylesheet()
    write_rss(items, base_url)
    print(f"Built site for {len(items)} episode(s) with base URL {base_url}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True,
                    help="Public base URL of the GitHub Pages site, no trailing slash")
    args = ap.parse_args()
    base = args.base_url.rstrip("/")
    build(base)


if __name__ == "__main__":
    main()
