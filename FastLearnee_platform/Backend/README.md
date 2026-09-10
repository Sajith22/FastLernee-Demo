# FastLearnee backend

## Local demo

```powershell
cd FastLearnee_platform/Backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

The local default uses SQLite and writes uploaded files to `storage/`. Open `http://127.0.0.1:8000/docs` for the interactive API demo.

## Docker demo

```powershell
docker compose up --build
```

Docker runs FastAPI with Postgres. The API supports the prototype flow: upload material, create a quiz job, poll its status, submit answers, read progress, and generate a revision sheet.
