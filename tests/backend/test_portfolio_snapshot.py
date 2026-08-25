import os
import sys
import unittest
from datetime import date

# Ensure server package is on python path
SERVER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../server"))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.core.config  # noqa: F401
from app.core.database import Base

import app.users.model  # noqa: F401
import app.identity.models.user_profile  # noqa: F401
import app.identity.models.financial_profile  # noqa: F401
import app.identity.models.risk_profile  # noqa: F401
import app.identity.models.risk_answer  # noqa: F401
import app.identity.models.investment_goal  # noqa: F401
import app.identity.models.wealth_dna  # noqa: F401

import app.investments.models.holding  # noqa: F401
import app.investments.models.investment_product  # noqa: F401
import app.investments.models.investment_order  # noqa: F401
import app.investments.models.fund_nav_history  # noqa: F401
import app.investments.models.fund_pipeline_run  # noqa: F401
import app.investments.models.fund_pipeline_lock  # noqa: F401
import app.investments.models.fund_pipeline_incident  # noqa: F401
import app.investments.models.portfolio_snapshot  # noqa: F401

from app.users.model import User
from app.investments.models.holding import InvestmentHolding
from app.investments.models.portfolio_snapshot import PortfolioSnapshot
from app.investments.services.portfolio_snapshot_service import (
    create_or_update_portfolio_snapshot,
)



class TestPortfolioSnapshotEngine(unittest.TestCase):
    def setUp(self):
        # In-memory SQLite database for fast isolated unit testing
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(bind=self.engine)
        TestingSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )
        self.db = TestingSessionLocal()

        # Create dummy user
        self.test_user = User(
            full_name="Test Investor",
            email="investor@example.com",
            password="hashed_password",
        )
        self.db.add(self.test_user)
        self.db.commit()
        self.db.refresh(self.test_user)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_empty_portfolio(self):
        """Empty portfolio yields zeros for all values."""
        result = create_or_update_portfolio_snapshot(
            self.db,
            self.test_user.id,
            snapshot_date=date(2026, 8, 25),
        )

        self.assertEqual(
            result,
            {
                "snapshot_date": "2026-08-25",
                "market_value": 0.0,
                "invested_value": 0.0,
                "pnl": 0.0,
                "pnl_percentage": 0.0,
            },
        )

        # Check DB row count
        count = (
            self.db.query(PortfolioSnapshot)
            .filter_by(user_id=self.test_user.id)
            .count()
        )
        self.assertEqual(count, 1)

    def test_positive_return(self):
        """Portfolio with positive gain calculates correct PnL and PnL %."""
        holding = InvestmentHolding(
            user_id=self.test_user.id,
            asset_type="MUTUAL_FUND",
            asset_name="Flexi Cap Fund",
            quantity=100.0,
            average_buy_price=10.0,
            invested_amount=1000.0,
            current_price=15.0,
            current_value=1500.0,
            total_gain=500.0,
            total_gain_percentage=50.0,
            sync_status="ACTIVE",
        )
        self.db.add(holding)
        self.db.commit()

        result = create_or_update_portfolio_snapshot(
            self.db,
            self.test_user.id,
            snapshot_date=date(2026, 8, 25),
        )

        self.assertEqual(result["snapshot_date"], "2026-08-25")
        self.assertEqual(result["invested_value"], 1000.0)
        self.assertEqual(result["market_value"], 1500.0)
        self.assertEqual(result["pnl"], 500.0)
        self.assertEqual(result["pnl_percentage"], 50.0)

    def test_negative_return(self):
        """Portfolio with negative gain calculates correct negative PnL and PnL %."""
        holding = InvestmentHolding(
            user_id=self.test_user.id,
            asset_type="STOCK",
            asset_name="Tech Stock",
            quantity=50.0,
            average_buy_price=20.0,
            invested_amount=1000.0,
            current_price=16.0,
            current_value=800.0,
            total_gain=-200.0,
            total_gain_percentage=-20.0,
            sync_status="ACTIVE",
        )
        self.db.add(holding)
        self.db.commit()

        result = create_or_update_portfolio_snapshot(
            self.db,
            self.test_user.id,
            snapshot_date=date(2026, 8, 25),
        )

        self.assertEqual(result["snapshot_date"], "2026-08-25")
        self.assertEqual(result["invested_value"], 1000.0)
        self.assertEqual(result["market_value"], 800.0)
        self.assertEqual(result["pnl"], -200.0)
        self.assertEqual(result["pnl_percentage"], -20.0)

    def test_zero_invested_value(self):
        """Zero invested value handles pnl_percentage safely without division by zero."""
        holding = InvestmentHolding(
            user_id=self.test_user.id,
            asset_type="OTHER",
            asset_name="Bonus Asset",
            quantity=10.0,
            average_buy_price=0.0,
            invested_amount=0.0,
            current_price=50.0,
            current_value=500.0,
            total_gain=500.0,
            total_gain_percentage=0.0,
            sync_status="ACTIVE",
        )
        self.db.add(holding)
        self.db.commit()

        result = create_or_update_portfolio_snapshot(
            self.db,
            self.test_user.id,
            snapshot_date=date(2026, 8, 25),
        )

        self.assertEqual(result["invested_value"], 0.0)
        self.assertEqual(result["market_value"], 500.0)
        self.assertEqual(result["pnl"], 500.0)
        self.assertEqual(result["pnl_percentage"], 0.0)

    def test_duplicate_same_day_execution(self):
        """Executing snapshot creation twice on the same day updates row idempotently (1 DB row)."""
        holding = InvestmentHolding(
            user_id=self.test_user.id,
            asset_type="GOLD",
            asset_name="Gold ETF",
            quantity=10.0,
            average_buy_price=100.0,
            invested_amount=1000.0,
            current_price=110.0,
            current_value=1100.0,
            total_gain=100.0,
            total_gain_percentage=10.0,
            sync_status="ACTIVE",
        )
        self.db.add(holding)
        self.db.commit()

        # Run 1st time
        res1 = create_or_update_portfolio_snapshot(
            self.db,
            self.test_user.id,
            snapshot_date=date(2026, 8, 25),
        )
        self.assertEqual(res1["market_value"], 1100.0)

        # Update market price of holding
        holding.current_price = 120.0
        holding.current_value = 1200.0
        holding.total_gain = 200.0
        self.db.commit()

        # Run 2nd time on same date
        res2 = create_or_update_portfolio_snapshot(
            self.db,
            self.test_user.id,
            snapshot_date=date(2026, 8, 25),
        )
        self.assertEqual(res2["market_value"], 1200.0)
        self.assertEqual(res2["pnl"], 200.0)
        self.assertEqual(res2["pnl_percentage"], 20.0)

        # Check DB row count: MUST be exactly 1
        snapshots = (
            self.db.query(PortfolioSnapshot)
            .filter_by(
                user_id=self.test_user.id,
                snapshot_date=date(2026, 8, 25),
            )
            .all()
        )
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0].market_value, 1200.0)


if __name__ == "__main__":
    unittest.main()
