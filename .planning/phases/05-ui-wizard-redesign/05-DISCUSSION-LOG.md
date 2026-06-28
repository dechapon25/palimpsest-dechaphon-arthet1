---
phase: 05
name: ui-wizard-redesign
date: 2026-06-28
---

# Phase 05 Discussion Log

## Session — 2026-06-28

### Area 1 — Interaction model

**Question:** ¿Cuántos pasos tendría el wizard?
**Options presented:** 2 pasos / 3 pasos / 4 pasos
**User response:** "Me gustaría que fuera mostrando la información a medida que la tenga: transcripción en raw, luego limpio, context y verificación, para dar la sensación de que todo va avanzando"
**Decision:** Progressive reveal — resultados aparecen incrementalmente en una sola página conforme llegan del pipeline.

### Area 2 — Results layout

**Question:** ¿Cómo se muestran las 3 secciones en resultados?
**Options presented:** Tabs / Acordeón / Scrollable
**User response:** "Como tú consideres más UX friendly"
**Decision (Claude):** Progressive reveal sin tabs — cada sección aparece al recibir su dato, de arriba a abajo.

### Area 3 — Raw/Cleaned toggle

**Question:** ¿Qué pasa con el toggle Raw/Cleaned?
**User response:** "Decide tú, hazme una propuesta en castellano"
**Decision (Claude):** Toggle mantenido pero de-emphasized — pequeño radio dentro de la tarjeta de transcripción.

### Area 4 — Propuesta general

**Propuesta presentada:** Wizard de revelación progresiva (upload screen → spinner con mensajes → revelación incremental de resultados)
**User response:** "Sí, adelante"

### Area 5 — Estilo visual

**Question:** ¿Cómo quieres el estilo visual?
**Options presented:** Minimalista oscuro / Minimalista claro / Neutro Gradio
**User response:** "Estilo tipo Bento Grid + Glassmorphism"
**Decision:** CSS personalizado: grid layout tipo bento, tarjetas con backdrop-filter blur, fondo oscuro, acento ámbar/dorado.

## Deferred Ideas

- Streaming word-by-word — requiere cambios en pipeline, fuera de scope
- Mobile breakpoints responsive — nice-to-have, fase posterior
- Panel de preview de imagen — scope creep
