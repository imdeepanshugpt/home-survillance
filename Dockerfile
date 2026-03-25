# ═══════════════════════════════════════════════════
#  AI Surveillance System
#  Base: Miniconda (standard for CV/ML projects)
#  Handles OpenCV + NumPy + ffmpeg without conflicts
#  Works on: Windows / Mac / Linux (amd64 + arm64)
# ═══════════════════════════════════════════════════

FROM continuumio/miniconda3:latest

LABEL description="AI Home Surveillance — Ollama + Telegram"

# ── Minimal system deps (rest handled by conda) ──────
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Create conda environment ──────────────────────────
COPY environment.yml .
RUN conda env create -f environment.yml && \
    conda clean -afy

# ── Use conda env as default shell ───────────────────
SHELL ["conda", "run", "-n", "surveillance", "/bin/bash", "-c"]

# ── Working directory ────────────────────────────────
WORKDIR /app

# ── Copy project (structure-aware) ───────────────────
COPY main.py .
COPY config/ ./config/
COPY src/    ./src/

# ── Create output directories ────────────────────────
RUN mkdir -p logs snapshots

# ── Default environment variables ────────────────────
# Override in .env or docker-compose.yml
ENV OLLAMA_MODEL=llava \
    OLLAMA_HOST=http://ollama:11434 \
    TELEGRAM_BOT_TOKEN="" \
    TELEGRAM_CHAT_ID="" \
    ENHANCE_LOW_LIGHT=true \
    MOTION_THRESHOLD=3000 \
    COOLDOWN_SECONDS=30 \
    CHECK_INTERVAL=2 \
    SEND_ALL_FRAMES=false \
    DASHBOARD_PORT=8080

EXPOSE 8080

# ── Run via conda env ─────────────────────────────────
ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "surveillance"]
CMD ["python3", "main.py"]
