from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    full_name = Column(
        String(100),
        nullable=False,
    )

    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password = Column(
        String(255),
        nullable=False,
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_admin = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # -----------------------------
    # Identity Relationships
    # -----------------------------

    profile = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    financial_profile = relationship(
        "FinancialProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    risk_profile = relationship(
        "RiskProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    goals = relationship(
        "InvestmentGoal",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    wealth_dna = relationship(
        "WealthDNA",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    investment_holdings = relationship(
        "InvestmentHolding",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    portfolio_snapshots = relationship(
        "PortfolioSnapshot",
        back_populates="user",
        cascade="all, delete-orphan",
    )