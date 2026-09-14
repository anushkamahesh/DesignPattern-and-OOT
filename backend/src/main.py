from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.interfaces.api.sensors import router as sensors_router

app = FastAPI(title="Smart Greenhouse API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sensors_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def read_root():
    return {"message": "Smart Greenhouse API is running"}
