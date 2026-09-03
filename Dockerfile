# ---- Base image ----
FROM python:3.11-slim

# Αποτρέπει buffering στα logs & δημιουργία .pyc αρχείων
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# curl χρειάζεται μόνο για το HEALTHCHECK παρακάτω
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Εγκατάσταση dependencies πρώτα (για να αξιοποιείται το Docker layer cache
# — αν αλλάξει μόνο ο κώδικας, δεν ξαναγίνεται pip install)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Αντιγραφή του κώδικα της εφαρμογής
COPY app.py .

EXPOSE 8501

# Healthcheck ώστε το Docker/Compose να ξέρει αν το app είναι έτοιμο
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py"]
