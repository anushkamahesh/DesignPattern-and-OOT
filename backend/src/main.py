from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference

from src.interfaces.api.health import router as health_router

app = FastAPI(
    title="Smart Greenhouse API",
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json",
)


@app.get("/")
async def root():
    return {"message": "Smart Greenhouse API is running"}


@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )


app.include_router(health_router)