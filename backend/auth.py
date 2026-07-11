from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List
import models, database

# IMPORTANT: In production, load this from .env — never hard-code in real deployments.
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Role definitions ---
# Baked into JWT claims from day one. Add the UI enforcement incrementally.
# Roles: contractor | engineer | auditor | pm
class Role:
    CONTRACTOR = "contractor"
    ENGINEER = "engineer"
    AUDITOR = "auditor"
    PM = "pm"

VALID_ROLES = {Role.CONTRACTOR, Role.ENGINEER, Role.AUDITOR, Role.PM}


# --- Token schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None
    role: str | None = None   # Role is embedded in every token from the start


# --- Password utils ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# --- Token creation ---
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    data must include 'sub' (email) and 'role'.
    Role is embedded in the JWT payload so every downstream check is stateless.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# --- User lookup ---
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


# --- Dependency: get current authenticated user ---
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(database.get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email, role=role)
    except JWTError:
        raise credentials_exception

    user = get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user


# --- Role-based access dependency factory ---
def require_roles(allowed_roles: List[str]):
    """
    Usage in a route:
        @router.get("/ncr/approve")
        def approve_ncr(current_user: models.User = Depends(require_roles([Role.ENGINEER, Role.PM]))):
    """
    async def role_checker(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(database.get_db)
    ):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            role: str = payload.get("role")
            email: str = payload.get("sub")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' is not authorised for this action."
            )
            
        user = get_user_by_email(db, email=email)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user

    return role_checker
