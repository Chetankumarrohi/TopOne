from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine

# Routers
from app.auth.router import router as auth_router
from app.users.router import router as users_router

from app.identity.routers.profile_router import (
    router as profile_router,
)

from app.identity.routers.financial_router import (
    router as financial_router,
)

from app.identity.routers.risk_router import (
    router as risk_router,
)

from app.identity.routers.goal_router import (
    router as goal_router,
)

from app.identity.routers.wealth_router import (
    router as wealth_router,
)

from app.identity.routers.financial_twin_router import (
    router as financial_twin_router,
)

from app.investments.routers.portfolio_router import (
    router as portfolio_router,
)

from app.investments.routers.investment_router import (
    router as investment_router,
)

from app.investments.services.fund_scheduler_service import (
    start_fund_scheduler,
    stop_fund_scheduler,
    get_fund_scheduler_status,
)

from app.investments.routers.pipeline_admin_router import (
    router as pipeline_admin_router,
)


# Import models so SQLAlchemy registers them
import app.users.model
import app.identity.models.user_profile
import app.identity.models.financial_profile
import app.identity.models.risk_profile
import app.identity.models.risk_answer
import app.identity.models.investment_goal
import app.identity.models.wealth_dna

import app.investments.models.holding
import app.investments.models.investment_product
import app.investments.models.investment_order
import app.investments.models.fund_nav_history
import app.investments.models.fund_pipeline_run
import app.investments.models.fund_pipeline_lock
import app.investments.models.fund_pipeline_incident
import app.investments.models.portfolio_snapshot


# Create database tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI application lifecycle.

    The fund scheduler starts when the API process starts
    and shuts down cleanly when the API process exits.

    Pipeline-level database locking provides the final
    protection against overlapping executions across
    multiple application processes.
    """

    start_fund_scheduler()

    try:
        yield

    finally:
        stop_fund_scheduler()


app = FastAPI(
    title="InvestiGenie API",
    version="1.0.0",
    description="AI Wealth Operating System",
    lifespan=lifespan,
)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.1.2:3000",
        "http://192.168.1.3:3000",
    ],

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register routers
app.include_router(auth_router)
app.include_router(users_router)

app.include_router(profile_router)
app.include_router(financial_router)
app.include_router(risk_router)
app.include_router(goal_router)
app.include_router(wealth_router)
app.include_router(financial_twin_router)

app.include_router(portfolio_router)
app.include_router(investment_router)

app.include_router(pipeline_admin_router)



@app.get("/", tags=["System"])
def root():
    return {
        "message": "InvestiGenie API Running 🚀"
    }


@app.get("/health", tags=["System"])
def health():
    scheduler_status = (
        get_fund_scheduler_status()
    )

    return {
        "status": "healthy",
        "scheduler": scheduler_status,
    }