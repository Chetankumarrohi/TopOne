from app.core.database import SessionLocal

from app.investments.models.investment_product import (
    InvestmentProduct,
)


PRODUCTS = [
    {
        "name": "Nifty 50 Index Fund",
        "product_type": "MUTUAL_FUND",
        "isin": "INFDEMO00001",
        "symbol": "NIFTY50",
        "provider": "Demo AMC",
        "category": "Index",
        "sub_category": "Large Cap Index",
        "asset_class": "EQUITY",
        "risk_level": "Moderate",
        "nav": 212.45,
        "expense_ratio": 0.20,
        "minimum_sip": 500,
        "minimum_lumpsum": 1000,
        "return_1y": 11.2,
        "return_3y": 14.8,
        "return_5y": 13.6,
        "volatility": 12.4,
        "purchase_allowed": True,
        "sip_allowed": True,
        "source": "DEMO",
    },
    {
        "name": "Flexi Cap Growth Fund",
        "product_type": "MUTUAL_FUND",
        "isin": "INFDEMO00002",
        "symbol": "FLEXIGROWTH",
        "provider": "Demo AMC",
        "category": "Flexi Cap",
        "sub_category": "Diversified Equity",
        "asset_class": "EQUITY",
        "risk_level": "Moderately High",
        "nav": 158.30,
        "expense_ratio": 0.62,
        "minimum_sip": 1000,
        "minimum_lumpsum": 1000,
        "return_1y": 13.6,
        "return_3y": 18.2,
        "return_5y": 16.4,
        "volatility": 14.1,
        "purchase_allowed": True,
        "sip_allowed": True,
        "source": "DEMO",
    },
    {
        "name": "Balanced Advantage Fund",
        "product_type": "MUTUAL_FUND",
        "isin": "INFDEMO00003",
        "symbol": "BALADV",
        "provider": "Demo AMC",
        "category": "Hybrid",
        "sub_category": "Dynamic Asset Allocation",
        "asset_class": "HYBRID",
        "risk_level": "Moderate",
        "nav": 96.20,
        "expense_ratio": 0.78,
        "minimum_sip": 500,
        "minimum_lumpsum": 1000,
        "return_1y": 9.8,
        "return_3y": 12.6,
        "return_5y": 11.9,
        "volatility": 8.9,
        "purchase_allowed": True,
        "sip_allowed": True,
        "source": "DEMO",
    },
    {
        "name": "Gold ETF Fund",
        "product_type": "ETF",
        "isin": "INFDEMO00004",
        "symbol": "GOLDETF",
        "provider": "Demo ETF Provider",
        "category": "Gold",
        "sub_category": "Gold ETF",
        "asset_class": "GOLD",
        "risk_level": "Moderate",
        "nav": 68.40,
        "expense_ratio": 0.35,
        "minimum_sip": 500,
        "minimum_lumpsum": 1000,
        "return_1y": 10.4,
        "return_3y": 11.5,
        "return_5y": 10.8,
        "volatility": 9.5,
        "purchase_allowed": True,
        "sip_allowed": True,
        "source": "DEMO",
    },
]


def seed_products():
    db = SessionLocal()

    try:
        for product_data in PRODUCTS:
            existing = (
                db.query(InvestmentProduct)
                .filter(
                    InvestmentProduct.isin
                    == product_data["isin"]
                )
                .first()
            )

            if existing:
                continue

            product = InvestmentProduct(
                **product_data
            )

            db.add(product)

        db.commit()

        count = (
            db.query(InvestmentProduct)
            .count()
        )

        print(
            f"Investment products ready. "
            f"Total products: {count}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    seed_products()