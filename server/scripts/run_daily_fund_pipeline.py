from __future__ import annotations

import json
import logging
import sys

from pathlib import Path


# Make the server root importable when this file
# is executed directly with Python.
SERVER_ROOT = Path(
    __file__
).resolve().parents[1]

if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(SERVER_ROOT),
    )


from app.core.database import SessionLocal

from app.investments.services.daily_fund_pipeline import (
    run_daily_fund_pipeline,
)


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    ),
)


def main() -> int:

    db = SessionLocal()

    try:
        print()
        print(
            "TOPONE — DAILY FUND PIPELINE"
        )
        print("=" * 55)

        result = run_daily_fund_pipeline(
            db=db,
        )

        print()
        print("=" * 55)
        print("PIPELINE RESULT")
        print("=" * 55)

        print(
            json.dumps(
                result,
                indent=2,
                default=str,
            )
        )

        status = result.get(
            "status"
        )

        if status == "SUCCESS":
            return 0

        if status == "CRITICAL":
            return 2

        return 1

    except KeyboardInterrupt:
        db.rollback()

        print(
            "\nPipeline interrupted by user."
        )

        return 130

    except Exception:
        db.rollback()

        logging.exception(
            "Unexpected daily pipeline failure."
        )

        return 1

    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(
        main()
    )