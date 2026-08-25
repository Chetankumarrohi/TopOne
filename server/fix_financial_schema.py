import sqlite3
from pathlib import Path


# Change this only if your database filename is different.
DB_PATH = Path("investigenie.db")


REQUIRED_COLUMNS = {
    "monthly_debt_payment": "FLOAT NOT NULL DEFAULT 0",
    "net_worth": "FLOAT NOT NULL DEFAULT 0",
    "savings_rate": "FLOAT NOT NULL DEFAULT 0",
    "debt_to_income_ratio": "FLOAT NOT NULL DEFAULT 0",
    "emergency_months": "FLOAT NOT NULL DEFAULT 0",
    "investment_ratio": "FLOAT NOT NULL DEFAULT 0",
}


def main():
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        print("Run: find . -name '*.db'")
        return

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        "PRAGMA table_info(financial_profiles)"
    )

    existing_columns = {
        row[1]
        for row in cursor.fetchall()
    }

    print("Existing columns:")
    for column in sorted(existing_columns):
        print(f"  ✓ {column}")

    print("\nChecking required columns...")

    for column_name, definition in REQUIRED_COLUMNS.items():
        if column_name in existing_columns:
            print(
                f"  ✓ {column_name} already exists"
            )
            continue

        cursor.execute(
            f"""
            ALTER TABLE financial_profiles
            ADD COLUMN {column_name} {definition}
            """
        )

        print(
            f"  + Added {column_name}"
        )

    connection.commit()
    connection.close()

    print(
        "\n✅ Financial profile schema updated successfully."
    )


if __name__ == "__main__":
    main()