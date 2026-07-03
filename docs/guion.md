Guión Video — Palimpsest (≤5 min, narrar en inglés)

Setup antes de grabar

1. Abre OBS Studio
2. Captura: pantalla completa del monitor principal
3. Micrófono activo
4. Cierra todas las terminales — sin GOOGLE_API_KEY visible (T-04-W-01)
5. Prepara en pestañas del navegador:
  - https://palimpsest.cpaz.es
  - https://github.com/carlosapsa/palimpsest
6. Prepara en editor (VSCode): orchestrator.py, mcp/server.py, cleaning.py, security/intake.py
7. Prepara imagen: data/samples/colon_1498_15c.jpg lista para subir

---
0:00–0:30 — El Problema

Muestra: colon_1498_15c.jpg a pantalla completa

Narra:

▎ "This is a real legal fragment from Spain's national archives — a lawsuit
▎ between Christopher Columbus and the Crown over the grants promised to him
▎ for the discovery of the Americas. For most researchers, it's completely
▎ unreadable — not because it's damaged, but because the handwriting is dense
▎ archaic cursive, full of abbreviations that disappeared from the language
▎ centuries ago. Without paleography training, documents like this stay
▎ locked. Palimpsest unlocks them."

---
0:30–1:00 — Arquitectura

Muestra: README.md en el navegador (sección del diagrama de arquitectura)

Narra:

▎ "Palimpsest uses four specialized agents running in sequence with Google's
▎ Agent Development Kit. First, a Transcription Agent reads the handwriting
▎ using Gemini Pro vision. Then a Cleaning Agent — packaged as a reusable ADK
▎ Agent Skill — expands abbreviations and normalizes archaic spelling. A
▎ Context Agent calls a FastMCP server with four historical-context tools,
▎ using Wikidata and Wikipedia. Finally, a Verification Agent scores every
▎ word with a confidence value. The pipeline is an ADK SequentialAgent — and
▎ it covers the four course concepts: multi-agent orchestration, an MCP
▎ server, security features, and an Agent Skill."

---
1:00–3:30 — Demo en vivo

Muestra: https://palimpsest.cpaz.es en el navegador

Narra:

▎ "Let me show it live. I'll upload the Columbus document."

Sube data/samples/colon_1498_15c.jpg. Mientras procesa (~30s, se ve la tarjeta
de progreso con los 4 pasos):

▎ "The pipeline is running — you can see the four stages: image intake,
▎ paleographic transcription, historical analysis, and the confidence map —
▎ all in sequence."

Cuando termine, recorre la página de resultados (una sola página, sin pestañas):

Tarjeta Transcripción — toggle en "Original":

▎ "This is what Gemini Pro vision reads directly from the handwriting. Notice
▎ the abbreviations: Almirante is written 'Almir.te', 'S.M.' for Su Majestad,
▎ 'dho' for dicho, 'I.dias' for Indias."

Cambia el toggle a "Limpiada":

▎ "The Cleaning Agent expanded every abbreviation. 'Almir.te' becomes
▎ Almirante, 'S.M.' becomes Su Majestad, 'Pleyto' is normalized to Pleito.
▎ Archaic spelling corrected, line structure preserved."

Tarjeta Mapa de Confianza:

▎ "Amber highlights mark words below the 0.95 confidence threshold — hover
▎ shows the score and the reason. The researcher sees exactly where to focus
▎ their review."

Tarjetas de Notas Históricas (abajo):

▎ "The Context Agent called the MCP server — Wikidata resolved Christopher
▎ Columbus, the Catholic Monarchs, and the places in this document. Each card
▎ shows the entity type and a short historical description."

Barra de metadatos:

▎ "And the metadata bar summarizes the run: processing time, model, word
▎ count, uncertain words, and overall confidence."

---
3:30–4:30 — Código

Muestra: VSCode, 4 archivos en secuencia rápida

orchestrator.py (SequentialAgent):

▎ "The SequentialAgent definition — four LlmAgents chained in order. This is
▎ the ADK multi-agent course concept."

mcp/server.py (herramientas FastMCP):

▎ "The FastMCP server exposes four tools. Wikidata SPARQL and Wikipedia REST —
▎ no API key required."

cleaning.py (AgentTool):

▎ "The cleaning agent packaged as an AgentTool — reusable by any future agent.
▎ This is the ADK Agent Skill course concept."

security/intake.py (filetype.guess):

▎ "Security layer: magic-byte validation before Pillow parses the file, EXIF
▎ stripping, size limits, and prompt injection defense in every agent's
▎ system prompt."

---
4:30–5:00 — Cierre

Muestra: navegador con https://palimpsest.cpaz.es y github.com/carlosapsa/palimpsest

Narra:

▎ "Palimpsest is live at palimpsest dot cpaz dot es — try it with any scanned
▎ historical Spanish manuscript. The full source is on GitHub. Four course
▎ concepts: a multi-agent ADK SequentialAgent pipeline, a FastMCP server with
▎ four tools, SEC-01 through SEC-04 security features, and a reusable ADK
▎ Agent Skill. One pipeline, no paleography expertise required."

---
Después de grabar

1. Sube a YouTube — visibilidad Unlisted o Public
2. Copia URL (https://youtu.be/XXXXX)
3. Captura pantalla de la UI con el pipeline completo (imagen de portada para el writeup)
4. Añade la URL del video a docs/writeup.md
5. Envía el submission a Kaggle con la URL del writeup y el video
