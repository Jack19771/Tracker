# Bazowy obraz Pythona
FROM python:3.10

# Ustawienie katalogu roboczego w kontenerze
WORKDIR /app

# Skopiowanie plików aplikacji
COPY ./app /app

# Instalacja zależności
RUN pip install --no-cache-dir -r requirements.txt

# Uruchomienie aplikacji FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
