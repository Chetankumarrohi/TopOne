import os
import unittest
from datetime import date
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys

# Ensure server package is on python path
SERVER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../server"))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

# Initialize environment variables before importing app modules
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test_secret_key_for_testing_12345")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")

import app.core.config  # noqa: F401
from app.core.database import Base


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

from app.users.model import User
from app.investments.models.holding import InvestmentHolding
from app.investments.models.portfolio_snapshot import PortfolioSnapshot
from app.investments.services.portfolio_snapshot_batch_service import (
    run_daily_portfolio_snapshots,
)


class TestPortfolioSnapshotBatchService(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        TestingSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )
        self.db = TestingSessionLocal()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_batch_empty_db(self):
        result = run_daily_portfolio_snapshots(self.db)
        self.assertEqual(result["total_users"], 0)
        self.assertEqual(result["processed"], 0)
        self.assertEqual(result["succeeded"], 0)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(result["failures"], [])

    def test_batch_active_user_with_holdings(self):
        user = User(
            full_name="Active User",
            email="active@example.com",
            password="hashedpassword",
            is_active=True,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        holding = InvestmentHolding(
            user_id=user.id,
            asset_type="MUTUAL_FUND",
            asset_name="Test Fund",
            quantity=100.0,
            average_buy_price=50.0,
            invested_amount=5000.0,
            current_price=60.0,
            current_value=6000.0,
            total_gain=1000.0,
            total_gain_percentage=20.0,
            sync_status="ACTIVE",
        )
        self.db.add(holding)
        self.db.commit()

        result = run_daily_portfolio_snapshots(self.db)
        self.assertEqual(result["total_users"], 1)
        self.assertEqual(result["succeeded"], 1)
        self.assertEqual(result["failed"], 0)

        snapshots = self.db.query(PortfolioSnapshot).filter(PortfolioSnapshot.user_id == user.id).all()
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0].market_value, 6000.0)
        self.assertEqual(snapshots[0].invested_value, 5000.0)
        self.assertEqual(snapshots[0].pnl, 1000.0)
        self.assertEqual(snapshots[0].pnl_percentage, 20.0)

    def test_batch_user_without_holdings_and_inactive_user(self):
        # User 1: Active, but no holdings -> should be skipped
        user_no_holdings = User(
            full_name="No Holdings User",
            email="noholdings@example.com",
            password="hashedpassword",
            is_active=True,
        )
        # User 2: Inactive, has holdings -> should be skipped
        user_inactive = User(
            full_name="Inactive User",
            email="inactive@example.com",
            password="hashedpassword",
            is_active=False,
        )
        self.db.add_all([user_no_holdings, user_inactive])
        self.db.commit()
        self.db.refresh(user_inactive)

        holding = InvestmentHolding(
            user_id=user_inactive.id,
            asset_type="STOCK",
            asset_name="Test Stock",
            quantity=10.0,
            average_buy_price=100.0,
            invested_amount=1000.0,
            current_price=110.0,
            current_value=1100.0,
            sync_status="ACTIVE",
        )
        self.db.add(holding)
        self.db.commit()

        result = run_daily_portfolio_snapshots(self.db)
        self.assertEqual(result["total_users"], 0)
        self.assertEqual(result["succeeded"], 0)

    def test_batch_per_user_failure_isolation(self):
        user1 = User(
            full_name="User One",
            email="user1@example.com",
            password="pass",
            is_active=True,
        )
        user2 = User(
            full_name="User Two",
            email="user2@example.com",
            password="pass",
            is_active=True,
        )
        self.db.add_all([user1, user2])
        self.db.commit()
        self.db.refresh(user1)
        self.db.refresh(user2)

        h1 = InvestmentHolding(user_id=user1.id, asset_type="CASH", asset_name="Cash", invested_amount=100, current_value=100, sync_status="ACTIVE")
        h2 = InvestmentHolding(user_id=user2.id, asset_type="CASH", asset_name="Cash", invested_amount=200, current_value=200, sync_status="ACTIVE")
        self.db.add_all([h1, h2])
        self.db.commit()

        real_func = __import__("app.investments.services.portfolio_snapshot_service", fromlist=["create_or_update_portfolio_snapshot"]).create_or_update_portfolio_snapshot

        def mock_create_or_update(db, user_id, snapshot_date=None):
            if user_id == user1.id:
                raise ValueError("Simulated failure for user1")
            return real_func(db, user_id, snapshot_date)

        with patch("app.investments.services.portfolio_snapshot_batch_service.create_or_update_portfolio_snapshot", side_effect=mock_create_or_update):
            result = run_daily_portfolio_snapshots(self.db)

        self.assertEqual(result["total_users"], 2)
        self.assertEqual(result["succeeded"], 1)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(len(result["failures"]), 1)
        self.assertEqual(result["failures"][0]["user_id"], user1.id)

    def test_batch_idempotent_rerun(self):
        user = User(
            full_name="Idempotent User",
            email="idempotent@example.com",
            password="pass",
            is_active=True,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        holding = InvestmentHolding(
            user_id=user.id,
            asset_type="GOLD",
            asset_name="Gold ETF",
            invested_amount=5000.0,
            current_value=5500.0,
            sync_status="ACTIVE",
        )
        self.db.add(holding)
        self.db.commit()

        # Run first time
        res1 = run_daily_portfolio_snapshots(self.db)
        self.assertEqual(res1["succeeded"], 1)

        # Run second time on same day
        res2 = run_daily_portfolio_snapshots(self.db)
        self.assertEqual(res2["succeeded"], 1)

        snapshots = self.db.query(PortfolioSnapshot).filter(
            PortfolioSnapshot.user_id == user.id,
            PortfolioSnapshot.snapshot_date == date.today(),
        ).all()
        self.assertEqual(len(snapshots), 1)


if __name__ == "__main__":
    unittest.main()
