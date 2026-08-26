import os
import sys
import unittest
from datetime import date

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
from app.investments.models.portfolio_transaction import PortfolioTransaction
from app.auth.jwt_handler import create_access_token
from app.investments.services.portfolio_transaction_service import (
    record_transaction,
    get_user_transactions,
    reconcile_user_portfolio_ledger,
)


class TestPortfolioTransactions(unittest.TestCase):
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
            full_name="Transaction Test User",
            email="txtest@example.com",
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

    def test_buy_and_sip_flow(self):
        # 1. BUY transaction
        buy_data = {
            "asset_type": "MUTUAL_FUND",
            "asset_name": "HDFC Flexi Cap Fund",
            "symbol": "HDFCFLEXI",
            "isin": "INF179K01234",
            "transaction_type": "BUY",
            "quantity": 100.0,
            "price": 50.0,
            "fees": 10.0,
            "transaction_date": "2026-08-01",
        }
        tx1 = record_transaction(self.db, self.user.id, buy_data)
        self.assertEqual(tx1["transaction_type"], "BUY")
        self.assertEqual(tx1["net_amount"], 5010.0)

        # Check created holding
        holding = self.db.query(InvestmentHolding).filter(InvestmentHolding.user_id == self.user.id).first()
        self.assertIsNotNone(holding)
        self.assertEqual(holding.quantity, 100.0)
        self.assertEqual(holding.invested_amount, 5010.0)

        # 2. SIP transaction on same fund
        sip_data = {
            "asset_type": "MUTUAL_FUND",
            "asset_name": "HDFC Flexi Cap Fund",
            "symbol": "HDFCFLEXI",
            "isin": "INF179K01234",
            "transaction_type": "SIP",
            "quantity": 50.0,
            "price": 60.0,
            "transaction_date": "2026-08-15",
        }
        tx2 = record_transaction(self.db, self.user.id, sip_data)
        self.assertEqual(tx2["transaction_type"], "SIP")

        # Verify updated holding
        self.db.refresh(holding)
        self.assertEqual(holding.quantity, 150.0)
        self.assertEqual(holding.invested_amount, 8010.0)

    def test_sell_and_redemption_flow(self):
        # BUY first
        record_transaction(
            self.db,
            self.user.id,
            {
                "asset_type": "STOCK",
                "asset_name": "Reliance Industries",
                "symbol": "RELIANCE",
                "transaction_type": "BUY",
                "quantity": 10.0,
                "price": 2500.0,
            },
        )

        # SELL 4 units
        sell_tx = record_transaction(
            self.db,
            self.user.id,
            {
                "asset_type": "STOCK",
                "asset_name": "Reliance Industries",
                "symbol": "RELIANCE",
                "transaction_type": "SELL",
                "quantity": 4.0,
                "price": 2700.0,
            },
        )
        self.assertEqual(sell_tx["transaction_type"], "SELL")

        holding = self.db.query(InvestmentHolding).filter(InvestmentHolding.symbol == "RELIANCE").first()
        self.assertEqual(holding.quantity, 6.0)
        self.assertEqual(holding.invested_amount, 15000.0)

    def test_insufficient_units_validation(self):
        # BUY 5 units
        record_transaction(
            self.db,
            self.user.id,
            {
                "asset_type": "GOLD",
                "asset_name": "Sovereign Gold Bond",
                "transaction_type": "BUY",
                "quantity": 5.0,
                "price": 6000.0,
            },
        )

        # Attempt to REDEEM 10 units (should fail with HTTP 400)
        with self.assertRaises(Exception) as ctx:
            record_transaction(
                self.db,
                self.user.id,
                {
                    "asset_type": "GOLD",
                    "asset_name": "Sovereign Gold Bond",
                    "transaction_type": "REDEMPTION",
                    "quantity": 10.0,
                    "price": 6200.0,
                },
            )
        self.assertIn("Insufficient units available", str(ctx.exception))

    def test_idempotency_protection(self):
        tx_data = {
            "asset_type": "MUTUAL_FUND",
            "asset_name": "Parag Parikh Flexi Cap",
            "transaction_type": "BUY",
            "quantity": 20.0,
            "price": 100.0,
            "external_reference": "EXT-UNIQUE-REF-999",
        }

        tx1 = record_transaction(self.db, self.user.id, tx_data)
        tx2 = record_transaction(self.db, self.user.id, tx_data)

        self.assertEqual(tx1["id"], tx2["id"])

        # Count total transactions in DB
        tx_count = self.db.query(PortfolioTransaction).filter(PortfolioTransaction.external_reference == "EXT-UNIQUE-REF-999").count()
        self.assertEqual(tx_count, 1)

    def test_api_endpoints_filtering_and_pagination(self):
        headers = {"Authorization": f"Bearer {self.token}"}

        # 1. Create via API
        payload = {
            "asset_type": "MUTUAL_FUND",
            "asset_name": "Nifty 50 Index Fund",
            "symbol": "NIFTY50",
            "transaction_type": "BUY",
            "quantity": 50.0,
            "price": 200.0,
            "transaction_date": "2026-08-20",
        }
        res = self.client.post("/portfolio/transactions", json=payload, headers=headers)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        tx_id = data["id"]
        self.assertEqual(data["asset_name"], "Nifty 50 Index Fund")

        # 2. Get by ID
        res_get = self.client.get(f"/portfolio/transactions/{tx_id}", headers=headers)
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["id"], tx_id)

        # 3. List with filters
        res_list = self.client.get("/portfolio/transactions?symbol=NIFTY50&transaction_type=BUY", headers=headers)
        self.assertEqual(res_list.status_code, 200)
        list_data = res_list.json()
        self.assertEqual(list_data["total"], 1)
        self.assertEqual(len(list_data["items"]), 1)

    def test_user_isolation(self):
        # User B
        user_b = User(
            full_name="User B",
            email="userb@example.com",
            password="password",
            is_active=True,
        )
        self.db.add(user_b)
        self.db.commit()
        self.db.refresh(user_b)

        token_b = create_access_token(data={"sub": str(user_b.id)})

        # User A creates transaction
        tx_a = record_transaction(
            self.db,
            self.user.id,
            {
                "asset_type": "CASH",
                "asset_name": "Cash Deposit",
                "transaction_type": "BUY",
                "quantity": 1.0,
                "price": 1000.0,
            },
        )

        # User B tries to view User A's transaction
        res = self.client.get(
            f"/portfolio/transactions/{tx_a['id']}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        self.assertEqual(res.status_code, 404)

    def test_ledger_reconciliation_and_migration(self):
        # 1. Manually insert a legacy holding without transactions
        legacy_holding = InvestmentHolding(
            user_id=self.user.id,
            asset_type="STOCK",
            asset_name="Tata Motors",
            symbol="TATAMOTORS",
            quantity=100.0,
            average_buy_price=400.0,
            invested_amount=40000.0,
            current_price=450.0,
            current_value=45000.0,
            total_gain=5000.0,
            total_gain_percentage=12.5,
            sync_status="ACTIVE",
        )
        self.db.add(legacy_holding)
        self.db.commit()
        self.db.refresh(legacy_holding)

        # Reconcile portfolio ledger
        result = reconcile_user_portfolio_ledger(self.db, self.user.id)
        self.assertEqual(result["status"], "success")
        self.assertGreater(result["total_transactions"], 0)

        # Check backfilled transaction in DB
        tx = self.db.query(PortfolioTransaction).filter(PortfolioTransaction.holding_id == legacy_holding.id).first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.source, "MANUAL_MIGRATION")
        self.assertEqual(tx.quantity, 100.0)

    def test_manual_holding_auto_ledger_creation(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {
            "asset_type": "STOCK",
            "asset_name": "Infosys Ltd",
            "symbol": "INFY",
            "quantity": 25.0,
            "average_buy_price": 1400.0,
            "invested_amount": 35000.0,
            "current_price": 1500.0,
            "current_value": 37500.0,
        }
        res = self.client.post("/portfolio/holdings", json=payload, headers=headers)
        self.assertEqual(res.status_code, 201)

        holding_id = res.json()["holding_id"]
        tx = self.db.query(PortfolioTransaction).filter(PortfolioTransaction.holding_id == holding_id).first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.asset_name, "Infosys Ltd")
        self.assertEqual(tx.quantity, 25.0)

    def test_reconcile_api_endpoint(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        res = self.client.post("/portfolio/transactions/reconcile", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "success")


if __name__ == "__main__":
    unittest.main()
