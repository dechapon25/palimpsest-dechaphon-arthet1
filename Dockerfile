FROM python:3.11-slim

WORKDIR /app

# Layer 1: dependencies (cached when only source changes).
# Separate from source COPY so rebuilds triggered by code changes reuse this layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install curl for HEALTHCHECK.
# Combined in a single apt-get RUN to keep layer count minimal.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Layer 2: application source and sample data.
COPY src/ ./src/
COPY data/samples/ ./data/samples/

# src/ layout: expose package to Python without pip install -e .
# pyproject.toml only contains [tool.ruff] — no [project] section — so
# pip install -e . fails. PYTHONPATH is the correct fix (RESEARCH.md Finding 2).
ENV PYTHONPATH=/app/src

# Gradio container binding: GRADIO_SERVER_NAME overrides the default 127.0.0.1.
# Without this, Gradio is unreachable outside the container even with -p port mapping
# (RESEARCH.md Pitfall 4; gradio.app/guides/deploying-gradio-with-docker).
ENV GRADIO_SERVER_NAME=0.0.0.0

# Prevent stdout buffering — critical for FastMCP stdio subprocess.
# Any buffered print() to stdout corrupts the JSON-RPC channel used by McpToolset
# (RESEARCH.md Pitfall 2; fastmcp issue #507).
ENV PYTHONUNBUFFERED=1

EXPOSE 7860

# HEALTHCHECK uses a 90s start-period to account for Gradio startup time
# and the first load_dotenv() + ADK initialization calls.
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# NOTE: Do NOT set GOOGLE_API_KEY here. Credentials are injected at runtime only:
#   docker run -e GOOGLE_API_KEY=<your-key> palimpsest
# Baking credentials into an image layer violates DEP-03 and T-04-01.
CMD ["python", "-m", "palimpsest.app"]
