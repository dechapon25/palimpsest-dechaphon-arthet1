# Phase 06 Context — UI Redesign (Claude Design handoff)

## Phase Boundary

Replace `src/palimpsest/app.py` CUSTOM_CSS + Gradio layout to match the Claude Design handoff file `Palimpsest UI.dc.html`. No backend changes. All 10 `outputs_full` tuple elements stay identical.

## Design Spec (source: Claude Design project 6d2852ab)

### Design tokens
| Token | Value |
|-------|-------|
| Background | `#F1EADA` (parchment) |
| Card background | `#FBF8F0` |
| Text primary | `#23190F` |
| Text secondary | `#6E6353` |
| Text muted | `#8A7E6B` / `#A99C86` |
| Accent (terracotta) | `#AE3B2C` |
| Green (success/done) | `#2F6E5A` |
| Amber (uncertain) | `#D9952E` |
| Blue (notes) | `#4A5A86` |
| Border | `rgba(35,25,15,0.12)` |
| Card shadow | `0 18px 40px -30px rgba(35,25,15,0.4)` |
| Border radius (cards) | `16px` |
| Border radius (pills) | `999px` |

### Fonts (Google Fonts)
```css
@import url('https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Hanken+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');
```
- **Spectral** (serif): headings, transcription text, card titles
- **Hanken Grotesk** (sans): body, buttons, labels
- **IBM Plex Mono** (mono): raw text, metadata values, file sizes

### Background decoration
Fixed watermark behind content: italic Spectral text in `rgba(35,25,15,0.038)`, `40px`, rotated `-1deg`. Latin/Spanish manuscript text content.

### 3 UI States (controlled via gr.State in Python)

**State 1 — Initial:**
- Header: logo mark (P, dark bg, terracotta bottom shadow) + "Palimpsest" + subtitle
- Upload zone: dashed `#AE3B2C66` border, file preview thumbnail, file name + size
- CTA button: full-width, terracotta bg, white text, box-shadow

**State 2 — Processing (NEW — does not exist yet):**
- File thumbnail + name in header
- Card with: title "Transcribiendo…", progress % label (terracotta), progress bar (terracotta fill)
- 4 steps list with icons: ✓ (green circle) | spinner (animated) | pending dot
  1. Restauración de la imagen
  2. Transcripción paleográfica
  3. Análisis histórico
  4. Mapa de confianza

**State 3 — Results:**
- File row + "Procesamiento completado" (green) + metadata bar
- Metadata bar: 5 pills — Tiempo / Modelo / Palabras / Inciertas / Confianza
- Grid `1.55fr 1fr`:
  - **Transcripción card**: segment toggle (Limpiada|Original), copy button, scrollable text
    - Limpiada: Spectral 18px lineHeight 1.95
    - Original: IBM Plex Mono 13.5px pre-wrap
  - **Mapa de confianza card**: tokens with amber highlight spans + hover tooltip, gradient legend
- **Notas históricas** (full width): `repeat(auto-fill, minmax(290px,1fr))` card grid
  - Each card: entity name (Spectral bold) + type pill (color by type) + description

### Type pills (notes)
| Type | Color |
|------|-------|
| Persona | `#AE3B2C` |
| Lugar | `#2F6E5A` |
| Fecha | `#B07A1E` |
| Documento/Institución | `#4A5A86` |

### Confidence highlight logic
- `score >= 0.95` → plain text
- `score < 0.95` → `rgba(217,149,46, alpha)` bg where `alpha = min(0.62, (1-score)*1.05*intensity) + 0.05`
- `inset 0 -2px 0 rgba(174,59,44,0.42)` bottom shadow on uncertain spans
- Hover: `rgba(217,149,46,0.78)` + `outline: 2px solid #AE3B2C`

### Header "Nueva transcripción" button
Visible only in Results state. Top-right in header. Ghost style with border.

## Gradio constraints (DO NOT change)

- `outputs_full` tuple = 10 elements in exact order — do not add/remove
- `gr.File(type="filepath")` — do not change
- `transcribe_manuscript()` is async — keep async
- `render_confidence_html()` signature unchanged (output is gr.HTML)
- `render_context_table()` → rename/replace with `render_context_cards()` returning HTML
- Backend pipeline unchanged

## Implementation approach

**Processing state**: Use `gr.Progress` (Gradio 4+ built-in) + async generator yielding intermediate UI updates. The 4 steps map to pipeline stages. Since pipeline is a black box (single await), simulate step progress with a background task or use `gr.Progress` indeterminate mode during the single await.

**Alternative**: Keep single-shot async (no generator), show processing state via CSS class on submit, revert on complete. Simpler, avoids generator complexity.

**Recommended**: CSS-only processing state — on submit_btn.click, show a `gr.HTML` processing card (pre-rendered, all 4 steps visible with spinner on first), hide on completion. No generator needed. Processing time ~20-40s, user sees the card.

## Files to change

- `src/palimpsest/app.py` — all CSS + layout (primary target)
  - CUSTOM_CSS: complete rewrite
  - Layout: add processing_section (gr.HTML, visible=False), update outputs_full to 11 elements (adds processing_section)
  - render_context_table → render_context_cards (returns HTML not Markdown)
  - render_confidence_html → update highlight logic to match design
  - reset_manuscript → outputs tuple must match new length

## Canonical references

- Design file: `.planning/phases/06-ui-redesign-claude-design/06-CONTEXT.md` (this file)
- Current app: `src/palimpsest/app.py`
- Current CSS: lines 49-167 in app.py (CUSTOM_CSS constant)
- Gradio 6.19.0 CSS vars: `--loader-color`, `--block-background-fill`, etc.
