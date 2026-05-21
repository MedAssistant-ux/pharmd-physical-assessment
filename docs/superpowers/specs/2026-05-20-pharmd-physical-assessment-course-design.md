# PharmD Physical Assessment Audio Course — Design Spec

**Date:** 2026-05-20
**Owner:** joshua.belcher18@gmail.com
**GitHub account:** MedAssistant-ux

## Purpose

Self-study curriculum for a Physical Assessment for Pharmacist Clinicians class, designed to be consumed hands-free while driving. Audio-first, with a synced web mirror for visual review.

## Success criteria

- All 14 modules play through a podcast app via the user's phone over car Bluetooth
- Voice-control playback works (Siri/Google Assistant)
- Each lesson covers learning objectives, core content, drug-related pearls, red flags, and an audio quiz with pause-and-answer pacing
- Total runtime ~5–6 hours
- New/updated lessons appear automatically in the podcast app after a `git push`

## Architecture

```
Markdown lesson scripts  ─►  edge-tts (Aria voice)  ─►  MP3s
        │                                                │
        └──────────►  Jekyll/static site  ◄──────────────┤
                            │                            │
                            ▼                            ▼
                   GitHub Pages (web)              RSS feed.xml
                            │                            │
                            ▼                            ▼
                      phone browser                 podcast app
                                                          │
                                                          ▼
                                                    car Bluetooth
```

## Components

### 1. Lesson scripts (`/transcripts/*.md`)
Markdown source of truth. Each module has frontmatter (title, episode #, duration estimate, learning objectives) and a body written in spoken-word style with `[pause]` markers, mnemonics spelled out phonetically, and quiz sections.

### 2. TTS pipeline (`/scripts/generate_audio.py`)
- Reads markdown, strips frontmatter
- Converts `[pause]` to SSML breaks
- Calls `edge-tts` with `en-US-AriaNeural`
- Outputs MP3 to `/audio/episode-NN-slug.mp3`
- ffmpeg normalizes loudness (-16 LUFS, podcast standard)

### 3. RSS builder (`/scripts/build_feed.py`)
Generates `feed.xml` with proper iTunes podcast tags so Apple Podcasts and Spotify accept it. Reads from each script's frontmatter + the generated MP3's actual duration.

### 4. Web site (`/docs/` for GitHub Pages)
Mobile-first single-page-ish layout:
- Home: episode list with play buttons and short descriptions
- Lesson page: embedded `<audio>` player + full transcript + key tables/mnemonics
- "Subscribe in podcast app" button (links to `podcast://...feed.xml`)
- Plain HTML/CSS, no framework — fast on mobile data

### 5. Curriculum (14 modules)

| # | Module | Focus |
|---|--------|-------|
| 1 | Foundations | Clinical reasoning, pharmacist scope, SOAP notes, exam techniques (inspection/palpation/percussion/auscultation) |
| 2 | Vital signs & general survey | BP technique, orthostatic, HR, RR, SpO2, temp, pain, general appearance |
| 3 | Skin, hair, nails | Drug rashes, SJS/TEN, ADR identification, lesion morphology |
| 4 | HEENT | Pupils, fundoscopy basics, otoscopy, oral exam, thyroid palpation |
| 5 | Respiratory | Inspection, palpation, percussion, auscultation; wheeze/crackles/rhonchi; inhaler-related findings |
| 6 | Cardiovascular | Heart sounds S1-S4, murmurs, JVP, edema, drug-induced changes |
| 7 | Peripheral vascular & lymphatic | Pulses, ABI, lymph nodes, DVT signs |
| 8 | Abdominal / GI | Inspection, auscultation-first sequence, organomegaly, drug-induced GI findings |
| 9 | Musculoskeletal | ROM, joint exam, gait, drug-induced (statin myopathy, FQ tendinopathy) |
| 10 | Neurologic | Mental status, cranial nerves, motor/sensory, reflexes, gait |
| 11 | Endocrine | Thyroid, diabetic foot exam, signs of Cushing/adrenal insufficiency |
| 12 | Genitourinary | Pharmacist-scope: CVA tenderness, edema, BPH symptom review |
| 13 | Geriatric & pediatric variations | Frailty, polypharmacy red flags, pediatric vital ranges, growth charts |
| 14 | Integration & board review | Focused assessments for ambulatory care; 20 board-style questions read aloud |

Each episode: ~25 minutes target. Format:
1. Intro (30 sec) — episode #, learning objectives
2. Core content (15-18 min)
3. Drug/pharmacist pearls (3-4 min)
4. Red flags / when to refer (2-3 min)
5. Audio quiz (3-4 min) — 5 questions, 5-second pause, then answer + rationale

## Tooling

| Tool | Purpose | Status |
|------|---------|--------|
| Python 3.11 | Scripts | Installed |
| edge-tts | TTS engine (free, Microsoft Neural voices) | To install |
| ffmpeg | Audio normalization | Installed |
| Jinja2 | RSS templating | To install via pip |
| Git + GitHub CLI | Version control + repo creation | Installed + authenticated |

## Repo layout

```
/
├── audio/                    Generated MP3 episodes
├── transcripts/              Markdown lesson sources
├── docs/                     GitHub Pages site root
│   ├── index.html
│   ├── style.css
│   ├── episodes/
│   │   └── *.html
│   └── feed.xml              Podcast RSS
├── scripts/
│   ├── generate_audio.py
│   ├── build_feed.py
│   └── build_site.py
├── requirements.txt
└── README.md
```

## Hands-free user flow

1. User opens Apple Podcasts (or Pocket Casts) on iPhone
2. "Add a Show by URL" → paste `https://medassistant-ux.github.io/<repo>/feed.xml`
3. Episodes auto-download
4. In car: "Hey Siri, play PharmD Physical Assessment" → starts via Bluetooth
5. Skip/back via steering wheel controls

## Out of scope

- Quiz scoring or progress tracking (the audio quiz is verbal only)
- Spaced repetition / Anki integration
- Video content
- Live class material specific to user's instructor (we don't have their syllabus)

## Risks & mitigations

- **edge-tts service changes:** It's a free unofficial wrapper around Microsoft Edge's Read Aloud. If it breaks, fallback is `pyttsx3` (offline, robotic) or paid (ElevenLabs/OpenAI TTS).
- **Audio quality vs. course-specific content:** We're aligning to Jones generally; if the user's class uses different terminology or emphasis, content may not 1:1 match the exam. User can share syllabus later for targeted updates.
- **Generation time:** ~6 hours of audio. We generate Module 1 as a sample first, get approval, then bulk-generate.

## Validation checkpoint

After scaffolding + Module 1 sample MP3 is generated, the user listens and approves voice/pacing/style before we generate the remaining 13 modules.
