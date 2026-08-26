import os
import sys
import unittest
from datetime import date, timedelta

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
import app.investments.models.portfolio_transaction

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.users.model import User
from app.investments.models.holding import InvestmentHolding
from app.investments.models.investment_product import InvestmentProduct
from app.auth.jwt_handler import create_access_token
from app.investments.services.portfolio_valuation_service import (
    value_holding,
    value_user_portfolio,
    value_all_portfolios_batch,
    get_latest_price_for_holding,
)
from app.investments.services.portfolio_snapshot_service import (
    create_or_update_portfolio_snapshot,
)


class TestPortfolioValuation(unittest.TestCase):
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

        # Seed test user
        self.user = User(
            full_name="Valuation Test User",
            email="valtest@example.com",
            password="hashedpassword",
            is_active=True,
        )
        self.db.add(self.user)
        self.db.commit()
        self.db.refresh(self.user)

        self.token = create_access_token(data={"sub": str(self.user.id)})

        def override_get_db():
            try:
                yield self.db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_mutual_fund_nav_valuation(self):
        # Create an InvestmentProduct with NAV
        product = InvestmentProduct(
            name="Axis Small Cap Fund",
            isin="INF846K01EW2",
            symbol="AXISSMALL",
            nav=75.5,
            nav_date=date.today(),
        )
        self.db.add(product)
        self.db.commit()

        # Create a mutual fund holding
        mf_holding = InvestmentHolding(
            user_id=self.user.id,
            asset_type="MUTUAL_FUND",
            asset_name="Axis Small Cap Fund",
            isin="INF846K01EW2",
            quantity=100.0,
            average_buy_price=60.0,
            invested_amount=6000.0,
            current_price=60.0,
            current_value=6000.0,
            sync_status="ACTIVE",
        )
        self.db.add(mf_holding)
        self.db.commit()

        # Perform valuation
        res = value_holding(self.db, mf_holding)
        self.assertEqual(res["current_price"], 75.5)
        self.assertEqual(res["current_value"], 7550.0)
        self.assertEqual(res["total_gain"], 1550.0)
        self.assertEqual(res["total_gain_percentage"], 25.83)
        self.assertEqual(res["valuation_source"], "AMFI_NAV")

    def test_stock_valuation(self):
        stock_holding = InvestmentHolding(
            user_id=self.user.id,
            asset_type="STOCK",
            asset_name="TCS",
            symbol="TCS",
            quantity=10.0,
            average_buy_price=3000.0,
            invested_amount=30000.0,
            current_price=3500.0,
            current_value=35000.0,
            sync_status="ACTIVE",
        )
        self.db.add(stock_holding)
        self.db.commit()

        res = value_holding(self.db, stock_holding)
        self.assertEqual(res["current_price"], 3500.0)
        self.assertEqual(res["current_value"], 35000.0)
        self.assertEqual(res["total_gain"], 5000.0)
        self.assertEqual(res["total_gain_percentage"], 16.67)

    def test_zero_quantity_holding(self):
        zero_holding = InvestmentHolding(
            user_id=self.user.id,
            asset_type="STOCK",
            asset_name="Sold Stock",
            quantity=0.0,
            average_buy_price=100.0,
            invested_amount=0.0,
            current_price=150.0,
            current_value=0.0,
            sync_status="ACTIVE",
        )
        self.db.add(zero_holding)
        self.db.commit()

        res = value_holding(self.db, zero_holding)
        self.assertEqual(res["current_value"], 0.0)
        self.assertEqual(res["total_gain"], 0.0)
        self.assertEqual(res["total_gain_percentage"], 0.0)

    def test_missing_price_fallback(self):
        # Holding with missing price and unmapped product
        unknown_holding = InvestmentHolding(
            user_id=self.user.id,
            asset_type="OTHER",
            asset_name="Custom Real Estate Fund",
            quantity=5.0,
            average_buy_price=10000.0,
            invested_amount=50000.0,
            current_price=0.0,
            current_value=0.0,
            sync_status="ACTIVE",
        )
        self.db.add(unknown_holding)
        self.db.commit()

        res = value_holding(self.db, unknown_holding)
        # Should gracefully fall back to average_buy_price without error
        self.assertEqual(res["current_price"], 10000.0)
        self.assertEqual(res["current_value"], 50000.0)
        self.assertEqual(res["valuation_source"], "FALLBACK_COST_PRICE")

    def test_cost_basis_preservation(self):
        holding = InvestmentHolding(
            user_id=self.user.id,
            asset_type="STOCK",
            asset_name="Wipro",
            quantity=20.0,
            average_buy_price=400.0,
            invested_amount=8000.0,
            current_price=400.0,
            current_value=8000.0,
        )
        self.db.add(holding)
        self.db.commit()

        # Update market price
        holding.current_price = 500.0
        self.db.commit()

        value_user_portfolio(self.db, self.user.id)
        self.db.refresh(holding)

        # Assert cost basis was NOT overwritten by valuation
        self.assertEqual(holding.average_buy_price, 400.0)
        self.assertEqual(holding.invested_amount, 8000.0)
        # Assert market values WERE updated
        self.assertEqual(holding.current_value, 10000.0)
        self.assertEqual(holding.total_gain, 2000.0)

    def test_stale_price_detection(self):
        # Product with NAV date 10 days ago
        old_date = date.today() - timedelta(days=10)
        product = InvestmentProduct(
            name="Stale MF",
            isin="INF123STALE01",
            nav=50.0,
            nav_date=old_date,
        )
        self.db.add(product)
        self.db.commit()

        holding = InvestmentHolding(
            user_id=self.user.id,
            asset_type="MUTUAL_FUND",
            asset_name="Stale MF",
            isin="INF123STALE01",
            quantity=10.0,
            average_buy_price=40.0,
            invested_amount=400.0,
            current_price=40.0,
            sync_status="ACTIVE",
        )
        self.db.add(holding)
        self.db.commit()

        res = value_holding(self.db, holding)
        self.assertTrue(res["is_stale"])
        self.assertEqual(res["sync_status"], "STALE")

    def test_batch_valuation_and_snapshot_sequence(self):
        holding = InvestmentHolding(
            user_id=self.user.id,
            asset_type="STOCK",
            asset_name="Infosys",
            quantity=10.0,
            average_buy_price=1000.0,
            invested_amount=10000.0,
            current_price=1200.0,
            sync_status="ACTIVE",
        )
        self.db.add(holding)
        self.db.commit()

        batch_res = value_all_portfolios_batch(self.db)
        self.assertGreaterEqual(batch_res["processed_users"], 1)

        snapshot_res = create_or_update_portfolio_snapshot(self.db, self.user.id)
        self.assertEqual(snapshot_res["market_value"], 12000.0)
        self.assertEqual(snapshot_res["invested_value"], 10000.0)
        self.assertEqual(snapshot_res["pnl"], 2000.0)

    def test_revalue_api_endpoint(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        res = self.client.post("/portfolio/revalue", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["user_id"], self.user.id)


if __name__ == "__main__":
    unittest.main()
