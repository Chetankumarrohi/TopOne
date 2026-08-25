import os
import sys
import unittest
from datetime import date, timedelta

# Ensure server package is on python path
SERVER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../server"))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

import app.core.config  # noqa: F401
from app.core.database import Base, get_db

# Import domain models so mappers register
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

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

from app.main import app
from app.users.model import User
from app.auth.jwt_handler import create_access_token
from app.investments.models.portfolio_snapshot import PortfolioSnapshot


from sqlalchemy.pool import StaticPool


class TestPortfolioHistoryAPI(unittest.TestCase):
    def setUp(self):
        # In-memory SQLite database with StaticPool for single connection sharing
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

        # Override get_db dependency
        def override_get_db():
            try:
                yield self.db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

        # Create user A
        self.user_a = User(
            full_name="Investor A",
            email="investora@example.com",
            password="hashed_password",
        )
        # Create user B
        self.user_b = User(
            full_name="Investor B",
            email="investorb@example.com",
            password="hashed_password",
        )
        self.db.add_all([self.user_a, self.user_b])
        self.db.commit()
        self.db.refresh(self.user_a)
        self.db.refresh(self.user_b)

        # Generate tokens
        self.token_a = create_access_token({"sub": str(self.user_a.id)})
        self.token_b = create_access_token({"sub": str(self.user_b.id)})

        self.headers_a = {"Authorization": f"Bearer {self.token_a}"}
        self.headers_b = {"Authorization": f"Bearer {self.token_b}"}

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_unauthenticated(self):
        """Unauthenticated GET /portfolio/history returns 401."""
        response = self.client.get("/portfolio/history")
        self.assertEqual(response.status_code, 401)

    def test_empty_history(self):
        """Authenticated user with no snapshots returns []."""
        response = self.client.get(
            "/portfolio/history",
            headers=self.headers_a,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_range_cutoffs_and_sorting(self):
        """Seed snapshots across dates and verify range cutoffs & ascending date order."""
        today = date.today()

        # Seed snapshots for User A
        snapshots_data = [
            (today - timedelta(days=10), 1100.0, 1000.0, 100.0, 10.0),   # In 1M, 3M, 6M, 1Y, ALL
            (today - timedelta(days=50), 1050.0, 1000.0, 50.0, 5.0),     # In 3M, 6M, 1Y, ALL
            (today - timedelta(days=120), 1000.0, 1000.0, 0.0, 0.0),     # In 6M, 1Y, ALL
            (today - timedelta(days=200), 950.0, 1000.0, -50.0, -5.0),   # In 1Y, ALL
            (today - timedelta(days=400), 900.0, 1000.0, -100.0, -10.0), # In ALL only
        ]

        for sdate, mval, ival, pnl, pnl_pct in snapshots_data:
            snap = PortfolioSnapshot(
                user_id=self.user_a.id,
                snapshot_date=sdate,
                market_value=mval,
                invested_value=ival,
                pnl=pnl,
                pnl_percentage=pnl_pct,
            )
            self.db.add(snap)

        self.db.commit()

        # -----------------------------------------------------
        # Range 1M (<= 30 days)
        # -----------------------------------------------------
        res_1m = self.client.get(
            "/portfolio/history?range=1M",
            headers=self.headers_a,
        )
        self.assertEqual(res_1m.status_code, 200)
        data_1m = res_1m.json()
        self.assertEqual(len(data_1m), 1)
        self.assertEqual(data_1m[0]["date"], str(today - timedelta(days=10)))
        self.assertEqual(data_1m[0]["market_value"], 1100.0)

        # -----------------------------------------------------
        # Range 3M (<= 90 days)
        # -----------------------------------------------------
        res_3m = self.client.get(
            "/portfolio/history?range=3M",
            headers=self.headers_a,
        )
        self.assertEqual(res_3m.status_code, 200)
        data_3m = res_3m.json()
        self.assertEqual(len(data_3m), 2)
        # Ascending order check
        self.assertEqual(data_3m[0]["date"], str(today - timedelta(days=50)))
        self.assertEqual(data_3m[1]["date"], str(today - timedelta(days=10)))

        # -----------------------------------------------------
        # Range 6M (<= 180 days)
        # -----------------------------------------------------
        res_6m = self.client.get(
            "/portfolio/history?range=6M",
            headers=self.headers_a,
        )
        self.assertEqual(res_6m.status_code, 200)
        data_6m = res_6m.json()
        self.assertEqual(len(data_6m), 3)

        # -----------------------------------------------------
        # Range 1Y (<= 365 days)
        # -----------------------------------------------------
        res_1y = self.client.get(
            "/portfolio/history?range=1Y",
            headers=self.headers_a,
        )
        self.assertEqual(res_1y.status_code, 200)
        data_1y = res_1y.json()
        self.assertEqual(len(data_1y), 4)

        # -----------------------------------------------------
        # Range ALL (No cutoff)
        # -----------------------------------------------------
        res_all = self.client.get(
            "/portfolio/history?range=ALL",
            headers=self.headers_a,
        )
        self.assertEqual(res_all.status_code, 200)
        data_all = res_all.json()
        self.assertEqual(len(data_all), 5)
        # Ascending order check
        self.assertEqual(data_all[0]["date"], str(today - timedelta(days=400)))
        self.assertEqual(data_all[-1]["date"], str(today - timedelta(days=10)))

    def test_user_isolation(self):
        """User A cannot access User B's historical snapshots."""
        today = date.today()

        snap_a = PortfolioSnapshot(
            user_id=self.user_a.id,
            snapshot_date=today,
            market_value=5000.0,
            invested_value=4000.0,
            pnl=1000.0,
            pnl_percentage=25.0,
        )
        snap_b = PortfolioSnapshot(
            user_id=self.user_b.id,
            snapshot_date=today,
            market_value=9999.0,
            invested_value=9000.0,
            pnl=999.0,
            pnl_percentage=11.1,
        )
        self.db.add_all([snap_a, snap_b])
        self.db.commit()

        # Query User A history
        res_a = self.client.get(
            "/portfolio/history?range=ALL",
            headers=self.headers_a,
        )
        self.assertEqual(res_a.status_code, 200)
        data_a = res_a.json()
        self.assertEqual(len(data_a), 1)
        self.assertEqual(data_a[0]["market_value"], 5000.0)

        # Query User B history
        res_b = self.client.get(
            "/portfolio/history?range=ALL",
            headers=self.headers_b,
        )
        self.assertEqual(res_b.status_code, 200)
        data_b = res_b.json()
        self.assertEqual(len(data_b), 1)
        self.assertEqual(data_b[0]["market_value"], 9999.0)


if __name__ == "__main__":
    unittest.main()
