from datetime import date
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.investments.models.holding import InvestmentHolding
from app.investments.models.portfolio_transaction import PortfolioTransaction

VALID_TRANSACTION_TYPES = {
    "BUY",
    "SELL",
    "SIP",
    "REDEMPTION",
    "DIVIDEND",
    "BONUS",
    "SPLIT",
    "SWITCH_IN",
    "SWITCH_OUT",
    "FEE",
}

OUTFLOW_TYPES = {"SELL", "REDEMPTION", "SWITCH_OUT"}
INFLOW_TYPES = {"BUY", "SIP", "SWITCH_IN", "BONUS"}


def record_transaction(
    db: Session,
    user_id: int,
    data: dict[str, Any],
) -> dict[str, Any]:
    """
    Creates an immutable portfolio transaction and reconciles the corresponding holding.
    Provides idempotency protection via external_reference.
    Prevents impossible states (e.g. selling more units than available).
    """
    tx_type = str(data.get("transaction_type", "")).upper().strip()
    if tx_type not in VALID_TRANSACTION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transaction type '{tx_type}'. Allowed types: {sorted(list(VALID_TRANSACTION_TYPES))}",
        )

    external_ref = data.get("external_reference")
    if external_ref:
        existing_tx = (
            db.query(PortfolioTransaction)
            .filter(
                PortfolioTransaction.user_id == user_id,
                PortfolioTransaction.external_reference == external_ref,
            )
            .first()
        )
        if existing_tx:
            return _format_transaction_response(existing_tx)

    asset_type = str(data.get("asset_type", "MUTUAL_FUND")).upper().strip()
    asset_name = str(data.get("asset_name", "")).strip()
    symbol = data.get("symbol")
    isin = data.get("isin")

    if not asset_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="asset_name is required",
        )

    quantity = float(data.get("quantity", 0.0) or 0.0)
    price = float(data.get("price", 0.0) or 0.0)
    fees = float(data.get("fees", 0.0) or 0.0)
    taxes = float(data.get("taxes", 0.0) or 0.0)

    if quantity < 0 or price < 0 or fees < 0 or taxes < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity, price, fees, and taxes must be non-negative numbers",
        )

    gross_amount = float(data.get("gross_amount") or (quantity * price))

    if tx_type in INFLOW_TYPES:
        net_amount = gross_amount + fees + taxes
    else:
        net_amount = max(0.0, gross_amount - fees - taxes)

    tx_date_raw = data.get("transaction_date")
    if isinstance(tx_date_raw, str):
        tx_date = date.fromisoformat(tx_date_raw)
    elif isinstance(tx_date_raw, date):
        tx_date = tx_date_raw
    else:
        tx_date = date.today()

    holding_id = data.get("holding_id")
    holding: Optional[InvestmentHolding] = None

    if holding_id:
        holding = (
            db.query(InvestmentHolding)
            .filter(
                InvestmentHolding.id == holding_id,
                InvestmentHolding.user_id == user_id,
            )
            .first()
        )

    if not holding:
        # Search existing holding by ISIN, symbol, or asset_name
        query = db.query(InvestmentHolding).filter(
            InvestmentHolding.user_id == user_id,
            InvestmentHolding.sync_status == "ACTIVE",
        )
        if isin:
            holding = query.filter(InvestmentHolding.isin == isin).first()
        elif symbol:
            holding = query.filter(InvestmentHolding.symbol == symbol).first()
        else:
            holding = query.filter(InvestmentHolding.asset_name == asset_name).first()

    # Validation for selling / redeeming: prevent selling more units than available
    if tx_type in OUTFLOW_TYPES:
        available_units = holding.quantity if holding else 0.0
        if quantity > available_units:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient units available for {asset_name}. Held: {available_units}, Requested {tx_type}: {quantity}",
            )

    # If no holding exists for an inflow transaction, create a new holding
    if not holding and tx_type in INFLOW_TYPES:
        holding = InvestmentHolding(
            user_id=user_id,
            asset_type=asset_type,
            asset_name=asset_name,
            symbol=symbol,
            isin=isin,
            quantity=0.0,
            average_buy_price=price,
            invested_amount=0.0,
            current_price=price,
            current_value=0.0,
            total_gain=0.0,
            total_gain_percentage=0.0,
            sync_status="ACTIVE",
        )
        db.add(holding)
        db.flush()

    transaction = PortfolioTransaction(
        user_id=user_id,
        holding_id=holding.id if holding else None,
        asset_type=asset_type,
        asset_name=asset_name,
        symbol=symbol,
        isin=isin,
        transaction_type=tx_type,
        quantity=quantity,
        price=price,
        gross_amount=round(gross_amount, 2),
        fees=round(fees, 2),
        taxes=round(taxes, 2),
        net_amount=round(net_amount, 2),
        transaction_date=tx_date,
        source=str(data.get("source", "MANUAL")),
        external_reference=external_ref,
        notes=data.get("notes"),
    )
    db.add(transaction)
    db.flush()

    # Reconcile holding quantity and invested amount if holding is associated
    if holding:
        if tx_type in INFLOW_TYPES:
            new_qty = holding.quantity + quantity
            new_invested = holding.invested_amount + net_amount
            holding.quantity = round(new_qty, 4)
            holding.invested_amount = round(new_invested, 2)
            if new_qty > 0:
                holding.average_buy_price = round(new_invested / new_qty, 2)
        elif tx_type in OUTFLOW_TYPES:
            new_qty = max(0.0, holding.quantity - quantity)
            ratio = (quantity / holding.quantity) if holding.quantity > 0 else 1.0
            new_invested = max(0.0, holding.invested_amount * (1.0 - ratio))
            holding.quantity = round(new_qty, 4)
            holding.invested_amount = round(new_invested, 2)

        elif tx_type == "SPLIT":
            split_ratio = price if price > 0 else 2.0
            holding.quantity = round(holding.quantity * split_ratio, 4)
            if holding.quantity > 0:
                holding.average_buy_price = round(holding.invested_amount / holding.quantity, 2)

        holding.current_value = round(holding.quantity * holding.current_price, 2)
        holding.total_gain = round(holding.current_value - holding.invested_amount, 2)
        if holding.invested_amount > 0:
            holding.total_gain_percentage = round((holding.total_gain / holding.invested_amount) * 100, 2)
        else:
            holding.total_gain_percentage = 0.0

    db.commit()
    db.refresh(transaction)

    return _format_transaction_response(transaction)


def get_user_transactions(
    db: Session,
    user_id: int,
    holding_id: Optional[int] = None,
    symbol: Optional[str] = None,
    isin: Optional[str] = None,
    transaction_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 50,
) -> dict[str, Any]:
    """
    Queries portfolio transactions for an authenticated user with filtering and pagination.
    """
    query = db.query(PortfolioTransaction).filter(
        PortfolioTransaction.user_id == user_id
    )

    if holding_id:
        query = query.filter(PortfolioTransaction.holding_id == holding_id)

    if symbol:
        query = query.filter(PortfolioTransaction.symbol == symbol)

    if isin:
        query = query.filter(PortfolioTransaction.isin == isin)

    if transaction_type:
        query = query.filter(
            PortfolioTransaction.transaction_type == transaction_type.upper()
        )

    if start_date:
        query = query.filter(PortfolioTransaction.transaction_date >= start_date)

    if end_date:
        query = query.filter(PortfolioTransaction.transaction_date <= end_date)

    total = query.count()
    items = (
        query.order_by(
            PortfolioTransaction.transaction_date.desc(),
            PortfolioTransaction.id.desc(),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [_format_transaction_response(tx) for tx in items],
    }


def get_transaction_by_id(
    db: Session,
    user_id: int,
    transaction_id: int,
) -> dict[str, Any]:
    """
    Retrieves a single portfolio transaction ensuring user isolation.
    """
    tx = (
        db.query(PortfolioTransaction)
        .filter(
            PortfolioTransaction.id == transaction_id,
            PortfolioTransaction.user_id == user_id,
        )
        .first()
    )
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    return _format_transaction_response(tx)


def reconcile_user_portfolio_ledger(
    db: Session,
    user_id: int,
) -> dict[str, Any]:
    """
    Recalculates and reconciles all holding quantities, invested amounts, and values
    from the historical transaction ledger. Preserves current manual holdings by backfilling
    initial transactions for holdings that do not yet have transaction records.
    """
    # 1. Backfill legacy manual holdings with an initial transaction record
    migrate_manual_holdings_to_ledger(db, user_id)

    # 2. Query all holdings for the user
    holdings = (
        db.query(InvestmentHolding)
        .filter(InvestmentHolding.user_id == user_id)
        .all()
    )

    processed_count = 0
    total_tx_count = 0

    for holding in holdings:
        txs = (
            db.query(PortfolioTransaction)
            .filter(
                PortfolioTransaction.user_id == user_id,
                PortfolioTransaction.holding_id == holding.id,
            )
            .order_by(
                PortfolioTransaction.transaction_date.asc(),
                PortfolioTransaction.id.asc(),
            )
            .all()
        )

        total_tx_count += len(txs)

        if not txs:
            continue

        running_qty = 0.0
        running_invested = 0.0

        for tx in txs:
            ttype = tx.transaction_type.upper()
            if ttype in INFLOW_TYPES:
                running_qty += tx.quantity
                running_invested += tx.net_amount
            elif ttype in OUTFLOW_TYPES:
                ratio = (tx.quantity / running_qty) if running_qty > 0 else 1.0
                running_qty = max(0.0, running_qty - tx.quantity)
                running_invested = max(0.0, running_invested * (1.0 - ratio))
            elif ttype == "SPLIT":
                split_ratio = tx.price if tx.price > 0 else 2.0
                running_qty = running_qty * split_ratio

        holding.quantity = round(running_qty, 4)
        holding.invested_amount = round(running_invested, 2)
        if holding.quantity > 0:
            holding.average_buy_price = round(holding.invested_amount / holding.quantity, 2)
        else:
            holding.average_buy_price = 0.0

        holding.current_value = round(holding.quantity * holding.current_price, 2)
        holding.total_gain = round(holding.current_value - holding.invested_amount, 2)
        if holding.invested_amount > 0:
            holding.total_gain_percentage = round((holding.total_gain / holding.invested_amount) * 100, 2)
        else:
            holding.total_gain_percentage = 0.0

        processed_count += 1

    db.commit()

    return {
        "message": "Portfolio holdings successfully reconciled from transaction ledger.",
        "user_id": user_id,
        "processed_holdings": processed_count,
        "total_transactions": total_tx_count,
        "status": "success",
    }


def migrate_manual_holdings_to_ledger(
    db: Session,
    user_id: int,
) -> int:
    """
    Backfills initial BUY transaction records for existing manual holdings that have no ledger history.
    This preserves current manual holdings during the migration to a transaction-ledger architecture.
    """
    holdings = (
        db.query(InvestmentHolding)
        .filter(InvestmentHolding.user_id == user_id)
        .all()
    )

    created_txs = 0

    for holding in holdings:
        existing_tx_count = (
            db.query(PortfolioTransaction)
            .filter(
                PortfolioTransaction.user_id == user_id,
                PortfolioTransaction.holding_id == holding.id,
            )
            .count()
        )

        if existing_tx_count == 0 and holding.quantity > 0:
            gross = holding.quantity * holding.average_buy_price
            init_tx = PortfolioTransaction(
                user_id=user_id,
                holding_id=holding.id,
                asset_type=holding.asset_type,
                asset_name=holding.asset_name,
                symbol=holding.symbol,
                isin=holding.isin,
                transaction_type="BUY",
                quantity=holding.quantity,
                price=holding.average_buy_price,
                gross_amount=round(gross, 2),
                fees=0.0,
                taxes=0.0,
                net_amount=round(holding.invested_amount or gross, 2),
                transaction_date=date.today(),
                source="MANUAL_MIGRATION",
                external_reference=f"INIT-HOLDING-{holding.id}",
                notes="Initial ledger migration from existing manual holding",
            )
            db.add(init_tx)
            created_txs += 1

    if created_txs > 0:
        db.commit()

    return created_txs


def _format_transaction_response(tx: PortfolioTransaction) -> dict[str, Any]:
    return {
        "id": tx.id,
        "user_id": tx.user_id,
        "holding_id": tx.holding_id,
        "asset_type": tx.asset_type,
        "asset_name": tx.asset_name,
        "symbol": tx.symbol,
        "isin": tx.isin,
        "transaction_type": tx.transaction_type,
        "quantity": tx.quantity,
        "price": tx.price,
        "gross_amount": tx.gross_amount,
        "fees": tx.fees,
        "taxes": tx.taxes,
        "net_amount": tx.net_amount,
        "transaction_date": str(tx.transaction_date),
        "source": tx.source,
        "external_reference": tx.external_reference,
        "notes": tx.notes,
        "created_at": tx.created_at.isoformat() if tx.created_at else None,
    }
