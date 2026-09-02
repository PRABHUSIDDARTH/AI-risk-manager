from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .models.db import init_db
from .routers import score, batch, orders
from .services.scorer import is_model_loaded, get_model_version
from .models.schemas import HealthResponse

app = FastAPI(
    title="Return Risk Scorer",
    description="AI-powered e-commerce return risk scoring system",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    init_db()

app.include_router(score.router)
app.include_router(batch.router)
app.include_router(orders.router)

@app.get('/health', response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status='ok',
        model_loaded=is_model_loaded(),
        model_version=get_model_version()
    )
