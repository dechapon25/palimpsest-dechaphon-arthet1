# Design Parity Gaps — Palimpsest UI.dc.html vs app.py (post 06-02)

Source of truth: claude.ai/design project 6d2852ab-237c-4ef2-8f6c-68b767d5cc49, file `Palimpsest UI.dc.html` (fetched 2026-07-03 via DesignSync MCP).

## Verbatim design values

### Header
- Layout: `display:flex;align-items:flex-end;justify-content:space-between;padding:28px 2px 18px;border-bottom:1px solid rgba(35,25,15,0.13);margin-bottom:36px`
- Logo mark: 46x46px, `border-radius:11px;background:#23190F;color:#F1EADA`, Spectral 700 26px, `box-shadow:inset 0 -3px 0 #AE3B2C`
- Title: Spectral 600 27px, `letter-spacing:-0.01em`
- Subtitle: `font-size:12.5px;letter-spacing:0.14em;text-transform:uppercase;color:#8A7E6B;margin-top:7px;font-weight:600` — text "Transcripción de manuscritos"
- Right badge: `IBM Plex Mono 12px;color:#6E6353;border:1px solid rgba(35,25,15,0.13);border-radius:999px;padding:7px 13px;background:rgba(251,248,240,0.7)` with 7px green dot (#2F6E5A) — text "ADK · 4 agentes"
- "Nueva transcripción" button lives in header right (only visible in results): ghost style `border:1px solid rgba(35,25,15,0.22);border-radius:9px;padding:9px 15px;font-weight:600;font-size:14px` + refresh SVG icon

### Background watermark
- Radial gradients: `radial-gradient(1100px 620px at 50% -8%, rgba(255,255,255,0.55), transparent 62%), radial-gradient(820px 520px at 102% 104%, rgba(174,59,44,0.05), transparent 58%)`
- Multi-line justified text block (NOT single line): `top:90px;left:-3%;right:-3%;bottom:0;overflow:hidden;font-family:Spectral;font-style:italic;font-size:40px;line-height:2.5;color:rgba(35,25,15,0.038);text-align:justify;transform:rotate(-1deg)`
- Text: "In nomine Dei omnipotentis notum sit cunctis presentem cartam videntibus quod ego concedo et cognosco quod vendo vobis domos quas habeo per hereditatem patris mei anno Domini millesimo quingentesimo · sepan cuantos esta carta vieren cómo yo otorgo y conozco que vendo unas casas que tengo por herencia de mi padre que santa gloria haya · ..." (repeat to fill)

### Initial state
- H1: Spectral 600 38px, `line-height:1.15;letter-spacing:-0.015em;text-align:center` — "Sube un manuscrito para transcribir"
- Sub paragraph: `text-align:center;color:#6E6353;font-size:16px;line-height:1.6;max-width:480px;margin:0 auto 32px` — "Restauramos la imagen, transcribimos la escritura, anotamos el contexto histórico y medimos la confianza de cada palabra."
- Content column: `max-width:680px;margin:34px auto 0`
- Drop zone: `border:1.5px dashed rgba(174,59,44,0.40);border-radius:16px;padding:18px;background:rgba(174,59,44,0.025)`
- Primary button: full width, `gap:10px;font-weight:600;font-size:16px;color:#FBF8F0;background:#AE3B2C;border-radius:11px;padding:15px;box-shadow:0 14px 26px -12px rgba(174,59,44,0.8)`

### Processing state
- Column `max-width:680px;margin:34px auto 0`
- Card: `background:#FBF8F0;border:1px solid rgba(35,25,15,0.12);border-radius:16px;padding:28px;box-shadow:0 18px 40px -28px rgba(35,25,15,0.4)`
- Card header row: "Transcribiendo…" Spectral 600 20px LEFT + progress % IBM Plex Mono 13px #AE3B2C RIGHT
- Progress bar: 7px height, `border-radius:99px;background:rgba(35,25,15,0.08)`, fill #AE3B2C
- 4 steps, each row `gap:14px;padding:9px 0`:
  - done: 24px circle `background:#2F6E5A` with white checkmark SVG
  - active: 20px spinner ring `border:2.5px solid rgba(35,25,15,0.15);border-top-color:#AE3B2C;animation:pal-spin 0.7s linear infinite`
  - pending: 11px empty circle `border:2px solid rgba(35,25,15,0.18)`
  - label: 15px; active=600 #23190F; done=500 #23190F; pending=500 #A99C86
- Step labels: Restauración de la imagen / Transcripción paleográfica / Análisis histórico / Mapa de confianza
- Gradio constraint: no Python generator — approximate step advancement with CSS animation-delay per step (e.g. steps activate at 0s/6s/14s/24s), or keep static active-first with spinner. Prefer CSS-delay approximation.

### Results — top bar (replaces current status_md pills)
- Row: `flex-wrap:wrap;gap:14px 22px;margin-bottom:24px;padding-bottom:22px;border-bottom:1px solid rgba(35,25,15,0.1)`
- Left: file thumb chip + filename 600 14px + green check row `font-size:12.5px;color:#2F6E5A;font-weight:600` "Procesamiento completado"
- Right: 5 metadata boxes `flex-direction:column;gap:2px;padding:8px 14px;border:1px solid rgba(35,25,15,0.12);border-radius:10px;background:rgba(251,248,240,0.6);min-width:74px`
  - label: `font-size:10.5px;letter-spacing:0.08em;text-transform:uppercase;color:#A99C86;font-weight:600`
  - value: IBM Plex Mono 15px 500 #23190F; Inciertas value #AE3B2C; Confianza value #2F6E5A
  - Tiempo / Modelo / Palabras / Inciertas / Confianza

### Section headers (all three result cards)
- `display:flex;align-items:center;gap:10px` + accent bar `width:6px;height:18px;border-radius:2px` + h2 Spectral 600 19px
- Transcripción bar: #AE3B2C · Mapa de confianza bar: #D9952E · Notas históricas bar: #4A5A86
- Card header zone separated by `border-bottom:1px solid rgba(35,25,15,0.09);padding:18px 22px`

### Transcription card
- Segmented toggle: container `padding:3px;background:rgba(35,25,15,0.06);border-radius:10px`; active seg `background:#FBF8F0;color:#AE3B2C;box-shadow:0 2px 5px -2px rgba(35,25,15,0.35);border-radius:7px;padding:6px 14px;font-size:13px;font-weight:600`; inactive `color:#8A7E6B`
- Copy button: icon + label "Copiar"→"Copiado" (green #2F6E5A when copied), `border:1px solid rgba(35,25,15,0.14);border-radius:8px;padding:6px 12px;font-size:13px`
- Body: `padding:26px 28px;max-height:420px;overflow:auto`
- Clean text: Spectral 18px line-height 1.95 #2A2014
- Raw text: IBM Plex Mono 13.5px line-height 1.95 #6E6353 white-space:pre-wrap

### Confidence card
- Header includes readout line below title: `min-height:20px;font-size:13px;font-weight:500` — default "Pasa el cursor sobre una palabra resaltada para ver su confianza." color #8A7E6B; on hover «word» — NN% de confianza (color: ≥85% #2F6E5A, ≥60% #B07A1E, else #AE3B2C). Gradio constraint: no server round-trip on hover — implement readout with pure JS injected via title attr fallback OR keep title tooltips + add static hint line.
- Body: Spectral 16px line-height 2.05 color #3A2E20, `max-height:300px;overflow:auto;padding:22px 24px`
- Highlight (score<0.95): `background:rgba(217,149,46,ALPHA);padding:1px 3px;border-radius:4px;box-shadow:inset 0 -2px 0 rgba(174,59,44,0.42);cursor:help` — ALPHA = min(0.62,(1-s)*1.05*0.85)+0.05
- Footer legend: `padding:14px 24px 18px;border-top:1px solid rgba(35,25,15,0.09)` — "Cierto" + gradient bar `height:8px;border-radius:99px;background:linear-gradient(90deg, rgba(217,149,46,0.04), rgba(217,149,46,0.85));box-shadow:inset 0 -2px 0 rgba(174,59,44,0.3)` + "Incierto"; labels `font-size:11.5px;color:#8A7E6B;font-weight:600`

### Notes card
- Header right: `IBM Plex Mono 12px #8A7E6B` — "{N} entidades"
- Entity cards: `border:1px solid rgba(35,25,15,0.11);border-radius:12px;padding:16px 17px;background:rgba(247,242,231,0.5)`
- Entity name: Spectral 600 16.5px
- Type pill: `IBM Plex Mono 10.5px 500;letter-spacing:0.04em;text-transform:uppercase;padding:3px 8px;border-radius:6px;color:{c};background:{c}1f;border:1px solid {c}40`
- Type colors: Persona #AE3B2C · Lugar #2F6E5A · Fecha #B07A1E · Documento/Institución #4A5A86
- Desc: 13.5px line-height 1.55 #6E6353

### Not to implement
- "Vista" reference switcher (bottom pill) — design-preview artifact only
- File chip with X-remove in drop zone — Gradio gr.File renders its own chip
