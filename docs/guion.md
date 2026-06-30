Guión Video — Palimpsest (≤5 min, narrar en inglés)

Setup antes de grabar

1. Abre OBS Studio
2. Captura: pantalla completa del monitor principal
3. Micrófono activo
4. Cierra todas las terminales — sin GOOGLE_API_KEY visible (T-04-W-01)
5. Prepara en pestañas del navegador:
  - http://palimpsest.cpaz.es:7860/
  - https://github.com/carlosapsa/palimpsest
6. Prepara en editor (VSCode): orchestrator.py, mcp/server.py, cleaning.py, security/intake.py
7. Prepara imagen: data/samples/pares_easy_18c.jpg lista para subir

---
0:00–0:30 — El Problema

Muestra: pares_easy_18c.jpg a pantalla completa

Narra:

▎ "This is an 18th-century Spanish colonial document frnial governor to the Viceroy. For most researchers, it'scompletely unreadable — not because it's damaged, but because the handwriting is dense colonial cursive, full of abbreviations that
▎ disappeared from the language centuries ago. Without , documents like this stay locked. Palimpsest unlocksthem."

---
0:30–1:00 — Arquitectura

Muestra: README.md en el navegador (sección del diagram

Narra:

▎ "Palimpsest uses four specialized agents running in svelopment Kit. First, a Transcription Agent reads thehandwriting using Gemini Pro vision. Then a Cleaning Agent — packaged as a reusable ADK Agent Skill — expands abbreviations and archaic spelling. A Context Agent calls a FastMCP serusing Wikidata and Wikipedia. Finally, a VerificationAgent scores every word with a confidence value. The pipeline uses SequentialAgent from ADK — the four course concepts covered: multi-agent, MCP server, security features, and Agent

---
1:00–3:30 — Demo en vivo                                                                                                                 
Muestra: http://palimpsest.cpaz.es:7860/ en el navegador                                                                                 
Narra:                                                                                                                                   
▎ "Let me show it live. I'll upload the same 18th-century document."                                                                     
Sube data/samples/pares_easy_18c.jpg. Mientras procesa (~30s):                                                                           
▎ "The pipeline is running — transcription, cleaning, entity enrichment, verification — all in sequence."                                
Cuando termine, muestra cada pestaña:                                                                                                    
▎ "Raw transcription tab — this is what Gemini Pro vision reads directly from the handwriting. Notice the abbreviations: Exmo, V.E., Dn, dho."

Cambia a Cleaned:

▎ "Cleaning Agent expanded every abbreviation. Exmo becmes Vuestra Excelencia. Archaic spelling corrected."

Cambia a Historical Notes:

▎ "Context Agent called the MCP server — Wikidata returlonial figures and places in this document."

Cambia a Confidence Highlights:

▎ "Orange words are below the 0.7 confidence threshold y where to focus their review."

---
3:30–4:30 — Código

Muestra: VSCode, 4 archivos en secuencia rápida

orchestrator.py (SequentialAgent):

▎ "The SequentialAgent definition — four LlmAgents chained in order. This is the ADK multi-agent course concept."

mcp/server.py (herramientas FastMCP):

▎ "The FastMCP server exposes four tools. Wikidata SPARQL and Wikipedia REST — no API key required."

cleaning.py (AgentTool):

▎ "The cleaning agent packaged as an AgentTool — reusable by any future agent. This is the ADK Agent Skill course concept."

security/intake.py (filetype.guess):

▎ "Security layer: magic-byte validation before Pillow parses the file, EXIF stripping, size limits, and prompt injection defense in every
▎ agent's system prompt."

---
4:30–5:00 — Cierre

Muestra: navegador con http://palimpsest.cpaz.es:7860/ y github.com/carlosapsa/palimpsest

Narra:

▎ "Palimpsest is live at palimpsest.cpaz.es port 7860 — try it with any scanned colonial manuscript. The full source is on GitHub. Four course concepts: multi-agent ADK SequentialAgent, FasSEC-01 through SEC-04 security features, and a reusableADK Agent Skill. One pipeline, no paleography expertise required."

---
Después de grabar

1. Sube a YouTube — visibilidad Unlisted o Public
2. Copia URL (https://youtu.be/XXXXX)
3. Captura pantalla de la UI con pipeline completo (cov
4. Envía señal de reanudación:
submitted: kaggle_url=https://www.kaggle.com/... video=