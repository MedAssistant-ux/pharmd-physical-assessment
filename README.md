# PharmD Physical Assessment Audio Course

Hands-free study course for Physical Assessment for Pharmacist Clinicians. Listen in the car, on a walk, or anywhere you can wear headphones. The full lesson is also available as a transcript on the companion web page for visual review.

**Live site:** https://medassistant-ux.github.io/pharmd-physical-assessment/
**Podcast feed:** https://medassistant-ux.github.io/pharmd-physical-assessment/feed.xml

## Subscribe in your podcast app

### Apple Podcasts (iPhone)
1. Open the Podcasts app → Library tab
2. Tap the three-dot menu (top right) → **Follow a Show by URL**
3. Paste: `https://medassistant-ux.github.io/pharmd-physical-assessment/feed.xml`

### Pocket Casts, Overcast, Castro
**Add by URL** → paste the feed URL above.

### Hands-free playback in the car
- Pair your phone via Bluetooth or CarPlay/Android Auto
- Say *"Hey Siri, play PharmD Physical Assessment Audio Course"*
- Use steering wheel controls for play/pause/skip

## Curriculum

| # | Module | Topic |
|---|--------|-------|
| 1 | Foundations | Clinical reasoning, scope, four exam techniques, SOAP |
| 2 | Vital signs | BP technique, orthostatic, RR, HR, SpO2, temp, pain, general survey |
| 3 | Skin, hair, nails | Drug rashes, SJS/TEN, DRESS, AGEP, nail findings |
| 4 | HEENT | Pupils, fundoscopy basics, otoscopy, oral exam, thyroid |
| 5 | Respiratory | Inspection, percussion, breath sounds, asthma/COPD exam |
| 6 | Cardiovascular | S1-S4, four classic murmurs, JVP, edema |
| 7 | Peripheral vascular | Pulses, ABI, arterial vs. venous insufficiency, DVT, lymph nodes |
| 8 | Abdominal | Inspect-auscultate-percuss-palpate, organomegaly, drug GI findings |
| 9 | Musculoskeletal | Joint exam, gait, statin myopathy, FQ tendinopathy |
| 10 | Neurologic | Mental status, cranial nerves, motor/sensory, reflexes |
| 11 | Endocrine | Thyroid, diabetic foot, Cushing's, adrenal insufficiency |
| 12 | Genitourinary | CVA tenderness, BPH/incontinence, drug-induced urinary findings |
| 13 | Geriatric & pediatric | Frailty, polypharmacy, pediatric vitals, growth charts |
| 14 | Integration | Focused assessment templates + 20 board-style review questions |

## Local development

```bash
pip install -r requirements.txt

# Generate audio for one episode (or all)
python scripts/generate_audio.py 01
python scripts/generate_audio.py          # generates everything missing
python scripts/generate_audio.py --force  # regenerate all

# Build site + RSS feed (after MP3s exist)
python scripts/build_feed.py --base-url https://medassistant-ux.github.io/pharmd-physical-assessment
```

## Stack

- **edge-tts** — free TTS via Microsoft Edge's neural voices (en-US-AriaNeural)
- **ffmpeg** — audio loudness normalization (-16 LUFS, podcast standard)
- **mutagen** — MP3 duration parsing
- **Plain HTML/CSS** — no framework, mobile-first

## License

Personal study material. Not medical advice.
