from fastapi import FastAPI

app = FastAPI(title="Oakland Stock Pipeline - Tracer Bullet")

@app.get("/")
def read_root():
    return {"status": "healthy", "message": "Pipeline plumbing is operational!"}