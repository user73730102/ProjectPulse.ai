from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import timedelta
import os
import logging

import models, database, auth
from auth import (
    Token, create_access_token, verify_password, get_user_by_email,
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
)
from routers import documents, submittals, ncr, agents

logging.basicConfig(level=logging.INFO)

# Create upload directories for local file storage
for d in ["uploads/specifications", "uploads/submittals", "uploads/drawings", "uploads/test_reports"]:
    os.makedirs(d, exist_ok=True)

app = FastAPI(
    title="ProjectPulse AI — EPC Intelligence Platform",
    description="AI-powered compliance, RFI, and project intelligence for Data Centre EPC delivery.",
    version="1.0.0",
)

# CORS — in production restrict to your actual frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files statically (local disk — Phase 1)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Register routers
app.include_router(documents.router)
app.include_router(submittals.router)
app.include_router(ncr.router)
app.include_router(agents.router)


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.post("/token", response_model=Token, tags=["Auth"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db),
):
    user = get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/me", tags=["Auth"])
async def read_current_user(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_active": current_user.is_active,
    }


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "ProjectPulse AI API"}
