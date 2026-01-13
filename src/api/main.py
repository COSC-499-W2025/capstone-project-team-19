from fastapi import FastAPI

app = FastAPI(title="Capstone API")

@app.get("/health")
def health():
    return {"status": "ok"}