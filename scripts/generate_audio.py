"""Generate MP3 audio from markdown lesson scripts using edge-tts.

Usage:
    python scripts/generate_audio.py                # generate all that are missing
    python scripts/generate_audio.py 01             # generate only episode 01
    python scripts/generate_audio.py --force        # regenerate everything
"""
from __future__ import annotations

import argparse
import asyncio
import re
import subprocess
import sys
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parent.parent
TRANSCRIPTS = ROOT / "transcripts"
AUDIO = ROOT / "docs" / "audio"
VOICE = "en-US-AriaNeural"
RATE = "-5%"   # slightly slower than default for clinical content
PITCH = "+0Hz"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body) given a markdown file with --- delimited YAML."""
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


def script_to_ssml_text(body: str) -> str:
    """Strip markdown and convert [pause] / [pause=Ns] to SSML-ish breaks.

    edge-tts accepts plain text best. We translate markdown headings into spoken
    cues and pauses into actual silence by sending them as a special token that
    edge-tts respects via its <break> SSML tag.
    """
    out: list[str] = []
    for line in body.splitlines():
        s = line.rstrip()
        if not s.strip():
            out.append("")
            continue
        # Headings become section pauses
        if s.startswith("### "):
            out.append(f"[pause=1] {s[4:].strip()}. [pause=1]")
            continue
        if s.startswith("## "):
            out.append(f"[pause=2] {s[3:].strip()}. [pause=2]")
            continue
        if s.startswith("# "):
            out.append(f"{s[2:].strip()}. [pause=2]")
            continue
        # Bullet markers
        s = re.sub(r"^\s*[-*]\s+", "", s)
        # Bold/italic/code markdown
        s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
        s = re.sub(r"\*(.+?)\*", r"\1", s)
        s = re.sub(r"`(.+?)`", r"\1", s)
        out.append(s)
    text = "\n".join(out)
    # Collapse multiple blank lines into one explicit pause
    text = re.sub(r"\n{2,}", " [pause=1] ", text)
    return text


def to_ssml(text: str, voice: str, rate: str, pitch: str) -> str:
    """Wrap text in SSML, converting [pause=N] markers to <break time=Ns/>."""
    # Escape XML special chars
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Replace [pause=Ns] and [pause] (default 1s)
    text = re.sub(r"\[pause=(\d+(?:\.\d+)?)\]", r'<break time="\1s"/>', text)
    text = text.replace("[pause]", '<break time="1s"/>')
    return (
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        'xml:lang="en-US">'
        f'<voice name="{voice}"><prosody rate="{rate}" pitch="{pitch}">'
        f"{text}"
        "</prosody></voice></speak>"
    )


async def synthesize(text: str, out_path: Path) -> None:
    """edge-tts plain-text synthesis with pause markers translated inline.

    edge-tts python lib doesn't accept SSML directly; instead we feed plain text
    and rely on punctuation. Pause markers become a sequence of periods with
    spaces which produce a brief silence.
    """
    # Convert [pause=N] / [pause] to long ellipses that produce realistic silence.
    def _pause_repl(m: re.Match[str]) -> str:
        secs = float(m.group(1)) if m.group(1) else 1.0
        # Each ". " ~ ~0.3s of silence in Aria; cap reasonably
        n = max(2, int(secs * 3))
        return " " + (". " * n)

    text = re.sub(r"\[pause=(\d+(?:\.\d+)?)\]", _pause_repl, text)
    text = text.replace("[pause]", _pause_repl(re.match(r"\[pause=(1)\]", "[pause=1]")))

    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    tmp = out_path.with_suffix(".tmp.mp3")
    await communicate.save(str(tmp))
    # Normalize loudness with ffmpeg (podcast standard -16 LUFS).
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(tmp),
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-codec:a", "libmp3lame", "-b:a", "96k",
        str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Fallback: just rename if ffmpeg failed
        print(f"ffmpeg failed, using raw output: {result.stderr[:200]}", file=sys.stderr)
        tmp.replace(out_path)
    else:
        tmp.unlink(missing_ok=True)


async def generate_one(md_path: Path, force: bool = False) -> Path | None:
    fm, body = parse_frontmatter(md_path.read_text(encoding="utf-8"))
    ep_num = fm.get("episode") or md_path.stem.split("-")[0]
    slug = md_path.stem
    out_path = AUDIO / f"{slug}.mp3"
    if out_path.exists() and not force:
        print(f"  [skip] {out_path.name} already exists")
        return out_path
    print(f"  [tts ] {slug} ...", flush=True)
    speak_text = script_to_ssml_text(body)
    await synthesize(speak_text, out_path)
    size_kb = out_path.stat().st_size / 1024
    print(f"  [done] {out_path.name} ({size_kb:.0f} KB)")
    return out_path


async def main_async(filter_ep: str | None, force: bool) -> None:
    AUDIO.mkdir(exist_ok=True, parents=True)
    md_files = sorted(TRANSCRIPTS.glob("*.md"))
    if filter_ep:
        md_files = [p for p in md_files if p.stem.startswith(filter_ep)]
    if not md_files:
        print("No transcript files found.")
        return
    print(f"Generating {len(md_files)} episode(s) with voice {VOICE}, rate {RATE}")
    for md in md_files:
        await generate_one(md, force=force)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("episode", nargs="?", default=None, help="Episode number prefix, e.g. 01")
    ap.add_argument("--force", action="store_true", help="Regenerate even if MP3 exists")
    args = ap.parse_args()
    asyncio.run(main_async(args.episode, args.force))


if __name__ == "__main__":
    main()
