import json
import os
from pathlib import Path

import duckdb

DB_PATH = Path(__file__).parent / "data" / "submissions.duckdb"

_conn = None


def get_conn():
    global _conn
    if _conn is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _conn = duckdb.connect(str(DB_PATH))
    return _conn


def init_db():
    conn = get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id VARCHAR PRIMARY KEY,
            supplier_name VARCHAR,
            items VARCHAR,
            total_cost DOUBLE,
            category VARCHAR,
            lead_time_days INTEGER,
            created_date VARCHAR,
            expected_delivery_date VARCHAR,
            status VARCHAR,
            notes VARCHAR
        )
        """
    )


def insert_purchase_order(po: dict) -> None:
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO purchase_orders
        (id, supplier_name, items, total_cost, category, lead_time_days,
         created_date, expected_delivery_date, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            po["id"],
            po["supplier_name"],
            json.dumps(po["items"]),
            po["total_cost"],
            po["category"],
            po["lead_time_days"],
            po["created_date"],
            po["expected_delivery_date"],
            po["status"],
            po.get("notes"),
        ],
    )


def list_purchase_orders() -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT id, supplier_name, items, total_cost, category, lead_time_days,
               created_date, expected_delivery_date, status, notes
        FROM purchase_orders
        ORDER BY created_date DESC, id DESC
        """
    ).fetchall()
    return [
        {
            "id": r[0],
            "supplier_name": r[1],
            "items": json.loads(r[2]) if r[2] else [],
            "total_cost": r[3],
            "category": r[4],
            "lead_time_days": r[5],
            "created_date": r[6],
            "expected_delivery_date": r[7],
            "status": r[8],
            "notes": r[9],
        }
        for r in rows
    ]
