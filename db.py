import csv
import hashlib
import hmac
import os
from datetime import datetime
import pyodbc


DEFAULT_DRIVER = "ODBC Driver 18 for SQL Server"
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"
DEFAULT_ADMIN_ROLE = "admin"


def _normalize_trust_cert(conn_str):
    normalized = conn_str.replace(
        "TrustServerCertificate=True",
        "TrustServerCertificate=yes",
    )
    normalized = normalized.replace(
        "TrustServerCertificate=False",
        "TrustServerCertificate=no",
    )
    return normalized


def _ensure_encrypt(conn_str):
    if "Encrypt=" in conn_str or "ENCRYPT=" in conn_str:
        return conn_str
    return f"{conn_str};Encrypt=yes"


def _normalize_server(conn_str):
    if "Server=localhost" in conn_str and "Server=localhost," not in conn_str:
        return conn_str.replace("Server=localhost", "Server=127.0.0.1,1433")
    return conn_str


def _parse_conn_str(raw_conn_str):
    parts = [p for p in raw_conn_str.split(";") if p.strip()]
    items = []
    for part in parts:
        if "=" in part:
            key, value = part.split("=", 1)
            items.append((key.strip(), value.strip()))
        else:
            items.append((part.strip(), ""))
    return items


def _normalize_credentials(raw_conn_str):
    items = _parse_conn_str(raw_conn_str)
    normalized = []
    for key, value in items:
        key_lower = key.lower()
        if key_lower in {"user id", "userid", "uid"}:
            normalized.append(("UID", value))
        elif key_lower in {"password", "pwd"}:
            normalized.append(("PWD", value))
        else:
            normalized.append((key, value))
    return ";".join(
        f"{k}={v}" if v != "" else k for k, v in normalized
    )


def _build_odbc_conn_str(raw_conn_str):
    raw_conn_str = raw_conn_str.strip()
    raw_conn_str = _normalize_trust_cert(raw_conn_str)
    raw_conn_str = _ensure_encrypt(raw_conn_str)
    raw_conn_str = _normalize_server(raw_conn_str)
    raw_conn_str = _normalize_credentials(raw_conn_str)
    if "Driver=" in raw_conn_str or "DRIVER=" in raw_conn_str:
        return raw_conn_str
    return f"Driver={{{DEFAULT_DRIVER}}};{raw_conn_str}"


def get_connection():
    raw = os.getenv(
        "MSSQL_CONNECTION_STRING",
        (
            "Server=127.0.0.1,1433;Database=ChatbotDb;User Id=sa;"
            "Password=Ryen@123;TrustServerCertificate=yes;Encrypt=yes"
        ),
    )
    conn_str = _build_odbc_conn_str(raw)
    return pyodbc.connect(conn_str)


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            IF OBJECT_ID(N'dbo.orders', N'U') IS NULL
            BEGIN
                CREATE TABLE dbo.orders (
                    order_number NVARCHAR(50) NOT NULL PRIMARY KEY,
                    customer_email NVARCHAR(255) NOT NULL,
                    customer_address NVARCHAR(500) NOT NULL,
                    customer_name NVARCHAR(255) NULL,
                    status NVARCHAR(100) NOT NULL,
                    current_location NVARCHAR(255) NOT NULL,
                    expected_delivery_date DATE NULL,
                    product_id NVARCHAR(50) NULL,
                    product_name NVARCHAR(255) NULL,
                    quantity INT NOT NULL DEFAULT 1,
                    unit_price DECIMAL(10, 2) NULL,
                    total_price DECIMAL(10, 2) NULL
                );
            END
            """
        )
        cursor.execute(
            """
            IF COL_LENGTH('dbo.orders', 'customer_name') IS NULL
            BEGIN
                ALTER TABLE dbo.orders ADD customer_name NVARCHAR(255) NULL;
            END
            """
        )
        cursor.execute(
            """
            IF EXISTS (
                SELECT 1
                FROM sys.columns
                WHERE object_id = OBJECT_ID(N'dbo.orders')
                  AND name = 'expected_delivery_date'
                  AND is_nullable = 0
            )
            BEGIN
                ALTER TABLE dbo.orders ALTER COLUMN expected_delivery_date DATE NULL;
            END
            """
        )
        optional_columns = {
            "product_id": "NVARCHAR(50) NULL",
            "product_name": "NVARCHAR(255) NULL",
            "quantity": "INT NOT NULL CONSTRAINT DF_orders_quantity DEFAULT 1",
            "unit_price": "DECIMAL(10, 2) NULL",
            "total_price": "DECIMAL(10, 2) NULL",
        }
        for column, definition in optional_columns.items():
            cursor.execute(
                f"""
                IF COL_LENGTH('dbo.orders', '{column}') IS NULL
                BEGIN
                    ALTER TABLE dbo.orders ADD {column} {definition};
                END
                """
            )
        cursor.execute(
            """
            IF OBJECT_ID(N'dbo.users', N'U') IS NULL
            BEGIN
                CREATE TABLE dbo.users (
                    user_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
                    username NVARCHAR(100) NOT NULL UNIQUE,
                    password_hash NVARCHAR(255) NOT NULL,
                    role NVARCHAR(50) NOT NULL,
                    full_name NVARCHAR(255) NULL,
                    email NVARCHAR(255) NULL,
                    address NVARCHAR(500) NULL
                );
            END
            """
        )
        conn.commit()
    seed_default_admin()


def hash_password(password):
    salt = os.urandom(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100000,
    )
    return f"{salt.hex()}:{password_hash.hex()}"


def verify_password(password, stored_hash):
    try:
        salt_hex, hash_hex = stored_hash.split(":", 1)
        expected_hash = bytes.fromhex(hash_hex)
        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            100000,
        )
        return hmac.compare_digest(actual_hash, expected_hash)
    except ValueError:
        return False


def seed_default_admin():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM dbo.users WHERE username = ?;",
            DEFAULT_ADMIN_USERNAME,
        )
        if cursor.fetchone():
            return

        cursor.execute(
            """
            INSERT INTO dbo.users
                (username, password_hash, role, full_name, email)
            VALUES (?, ?, ?, ?, ?);
            """,
            DEFAULT_ADMIN_USERNAME,
            hash_password(DEFAULT_ADMIN_PASSWORD),
            DEFAULT_ADMIN_ROLE,
            "Default Admin",
            "admin@example.com",
        )
        conn.commit()


def authenticate_user(username, password):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT username, password_hash, role, full_name, email, address
            FROM dbo.users
            WHERE username = ?;
            """,
            username,
        )
        row = cursor.fetchone()
        if not row or not verify_password(password, row.password_hash):
            return None
        return {
            "username": row.username,
            "role": row.role,
            "full_name": row.full_name,
            "email": row.email,
            "address": row.address,
        }


def _is_table_empty():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(1) FROM dbo.orders;")
        count = cursor.fetchone()[0]
        return count == 0


def seed_from_csv(csv_path="orders.csv"):
    if not os.path.exists(csv_path):
        return
    if not _is_table_empty():
        return

    rows = []
    with open(csv_path, mode="r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            parsed_date = _parse_order_date(row.get("expected_delivery_date"))
            rows.append(
                (
                    row["order_number"],
                    row["customer_email"],
                    row["customer_address"],
                    row.get("customer_name"),
                    row["status"],
                    row["current_location"],
                    parsed_date,
                    row.get("product_id"),
                    row.get("product_name"),
                    int(row.get("quantity") or 1),
                    row.get("unit_price") or None,
                    row.get("total_price") or None,
                )
            )

    if not rows:
        return

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.fast_executemany = True
        cursor.executemany(
            """
            INSERT INTO dbo.orders
                (
                    order_number,
                    customer_email,
                    customer_address,
                    customer_name,
                    status,
                    current_location,
                    expected_delivery_date,
                    product_id,
                    product_name,
                    quantity,
                    unit_price,
                    total_price
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            rows,
        )
        conn.commit()


def _parse_order_date(raw_date):
    raw_date = (raw_date or "").strip()
    if not raw_date or raw_date.upper() == "N/A":
        return None
    return datetime.strptime(raw_date, "%d/%m/%Y").date()


def fetch_order_info(order_number):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                order_number,
                customer_email,
                customer_address,
                customer_name,
                status,
                current_location,
                expected_delivery_date,
                product_id,
                product_name,
                quantity,
                unit_price,
                total_price
            FROM dbo.orders
            WHERE order_number = ?;
            """,
            order_number,
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "order_number": row.order_number,
            "customer_email": row.customer_email,
            "customer_address": row.customer_address,
            "customer_name": getattr(row, "customer_name", None),
            "status": row.status,
            "current_location": row.current_location,
            "expected_delivery_date": str(row.expected_delivery_date),
            "product_id": getattr(row, "product_id", None),
            "product_name": getattr(row, "product_name", None),
            "quantity": getattr(row, "quantity", None),
            "unit_price": getattr(row, "unit_price", None),
            "total_price": getattr(row, "total_price", None),
        }


def verify_customer_email(order_number, customer_email):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 1
            FROM dbo.orders
            WHERE order_number = ? AND customer_email = ?;
            """,
            order_number,
            customer_email,
        )
        return cursor.fetchone() is not None


def fetch_customer_address(email):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT customer_address
            FROM dbo.orders
            WHERE customer_email = ?;
            """,
            email,
        )
        row = cursor.fetchone()
        return row.customer_address if row else None


def update_address(order_number, new_address):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE dbo.orders
            SET customer_address = ?
            WHERE order_number = ?;
            """,
            new_address,
            order_number,
        )
        conn.commit()


def update_order_status(order_number, status, current_location=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        if current_location:
            cursor.execute(
                """
                UPDATE dbo.orders
                SET status = ?, current_location = ?
                WHERE order_number = ?;
                """,
                status,
                current_location,
                order_number,
            )
        else:
            cursor.execute(
                """
                UPDATE dbo.orders
                SET status = ?
                WHERE order_number = ?;
                """,
                status,
                order_number,
            )
        updated_count = cursor.rowcount
        conn.commit()
        return updated_count > 0


def delete_order(order_number):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM dbo.orders
            WHERE order_number = ?;
            """,
            order_number,
        )
        deleted_count = cursor.rowcount
        conn.commit()
        return deleted_count > 0


def create_order(
    order_number,
    customer_email,
    customer_address,
    status,
    current_location,
    expected_delivery_date=None,
    customer_name=None,
    product_id=None,
    product_name=None,
    quantity=1,
    unit_price=None,
    total_price=None,
):
    parsed_date = _parse_order_date(expected_delivery_date)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM dbo.orders WHERE order_number = ?;",
            order_number,
        )
        if cursor.fetchone():
            return False, "Order number already exists."

        cursor.execute(
            """
            INSERT INTO dbo.orders
                (
                    order_number,
                    customer_email,
                    customer_address,
                    customer_name,
                    status,
                    current_location,
                    expected_delivery_date,
                    product_id,
                    product_name,
                    quantity,
                    unit_price,
                    total_price
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            order_number,
            customer_email,
            customer_address,
            customer_name,
            status,
            current_location,
            parsed_date,
            product_id,
            product_name,
            quantity,
            unit_price,
            total_price,
        )
        conn.commit()
        return True, "Order created."
