from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="AI Voice Agent")


@app.get("/health")
def health():
    return {"status": "ok"}


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
