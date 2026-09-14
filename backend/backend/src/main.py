from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference

from src.interfaces.api.health import router as health_router

# Disable default /docs and /redoc pages
app = FastAPI(
    title="Smart Greenhouse API",
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json",
)

# Root route
@app.get("/")
async def root():
    return {"message": "Smart Greenhouse API is running"}


# Custom Scalar documentation route
@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )


# Include health router
app.include_router(health_router)
