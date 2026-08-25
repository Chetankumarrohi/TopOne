from sqlalchemy.orm import Session

from app.auth.hashing import hash_password, verify_password
from app.auth.jwt_handler import create_access_token
from app.auth.schema import LoginRequest, RegisterRequest
from app.users.model import User


def create_user(db: Session, user: RegisterRequest) -> User:
    """
    Register a new user.
    """

    existing_user = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if existing_user:
        raise ValueError("Email is already registered.")

    db_user = User(
        full_name=user.full_name,
        email=user.email,
        password=hash_password(user.password),
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def authenticate_user(db: Session, credentials: LoginRequest):
    """
    Authenticate user credentials and generate JWT.
    """

    user = (
        db.query(User)
        .filter(User.email == credentials.email)
        .first()
    )

    if not user:
        raise ValueError("Invalid email or password.")

    if not verify_password(credentials.password, user.password):
        raise ValueError("Invalid email or password.")

    token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }