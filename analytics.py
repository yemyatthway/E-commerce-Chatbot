import csv
from collections import Counter, defaultdict
from itertools import combinations


ORDERS_CSV = "orders.csv"


def load_csv_order_rows(csv_path=ORDERS_CSV):
    with open(csv_path, mode="r") as file:
        return list(csv.DictReader(file))


def load_database_order_rows():
    from db import get_connection

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                order_number,
                status,
                current_location,
                expected_delivery_date,
                customer_address,
                customer_name,
                customer_email,
                product_id,
                product_name,
                quantity,
                unit_price,
                total_price
            FROM dbo.orders;
            """
        )
        rows = []
        for row in cursor.fetchall():
            rows.append(
                {
                    "order_number": row.order_number,
                    "status": row.status,
                    "current_location": row.current_location,
                    "expected_delivery_date": row.expected_delivery_date,
                    "customer_address": row.customer_address,
                    "customer_name": row.customer_name,
                    "customer_email": row.customer_email,
                    "product_id": row.product_id,
                    "product_name": row.product_name,
                    "quantity": row.quantity,
                    "unit_price": row.unit_price,
                    "total_price": row.total_price,
                }
            )
        return rows


def load_order_rows(csv_path=ORDERS_CSV, use_database=True):
    if use_database:
        try:
            return load_database_order_rows()
        except Exception:
            pass
    return load_csv_order_rows(csv_path)


def _quantity(row):
    try:
        return int(row.get("quantity") or 1)
    except ValueError:
        return 1


def _total_price(row):
    try:
        return float(row.get("total_price") or 0)
    except ValueError:
        return 0


def product_popularity(csv_path=ORDERS_CSV, limit=5, use_database=True):
    quantity_counter = Counter()
    revenue_counter = Counter()
    name_by_id = {}

    for row in load_order_rows(csv_path, use_database):
        if row.get("status", "").lower() == "cancelled":
            continue

        product_id = row.get("product_id")
        if not product_id:
            continue

        name_by_id[product_id] = row.get("product_name") or product_id
        quantity_counter[product_id] += _quantity(row)
        revenue_counter[product_id] += _total_price(row)

    return [
        {
            "product_id": product_id,
            "product_name": name_by_id.get(product_id, product_id),
            "units_sold": units_sold,
            "revenue": revenue_counter[product_id],
        }
        for product_id, units_sold in quantity_counter.most_common(limit)
    ]


def format_product_popularity(rows):
    if not rows:
        return "No product sales data is available yet."

    lines = ["Product popularity analysis from saved orders:"]
    for index, row in enumerate(rows, start=1):
        lines.append(
            f"{index}. {row['product_id']} - {row['product_name']} | "
            f"Units sold: {row['units_sold']} | Revenue: ${row['revenue']:.2f}"
        )
    return "\n".join(lines)


def market_basket_analysis(
    csv_path=ORDERS_CSV,
    min_support=2,
    limit=5,
    use_database=True,
):
    baskets = defaultdict(set)
    product_names = {}

    for row in load_order_rows(csv_path, use_database):
        if row.get("status", "").lower() == "cancelled":
            continue

        product_id = row.get("product_id")
        customer_email = row.get("customer_email")
        if not product_id or not customer_email:
            continue

        baskets[customer_email].add(product_id)
        product_names[product_id] = row.get("product_name") or product_id

    pair_counter = Counter()
    item_counter = Counter()
    basket_count = 0
    for basket in baskets.values():
        if len(basket) < 2:
            continue
        basket_count += 1
        for product_id in basket:
            item_counter[product_id] += 1
        for pair in combinations(sorted(basket), 2):
            pair_counter[pair] += 1

    results = []
    for pair, support_count in pair_counter.most_common():
        if support_count < min_support:
            continue
        left, right = pair
        support = support_count / max(basket_count, 1)
        left_support = item_counter[left] / max(basket_count, 1)
        right_support = item_counter[right] / max(basket_count, 1)
        confidence_left_to_right = support_count / max(item_counter[left], 1)
        confidence_right_to_left = support_count / max(item_counter[right], 1)
        lift_left_to_right = confidence_left_to_right / max(right_support, 0.000001)
        lift_right_to_left = confidence_right_to_left / max(left_support, 0.000001)
        results.append(
            {
                "pair": pair,
                "names": tuple(product_names[product_id] for product_id in pair),
                "support_count": support_count,
                "support": support,
                "confidence_left_to_right": confidence_left_to_right,
                "confidence_right_to_left": confidence_right_to_left,
                "lift_left_to_right": lift_left_to_right,
                "lift_right_to_left": lift_right_to_left,
            }
        )
        if len(results) >= limit:
            break

    return results


def format_market_basket_analysis(rows):
    if not rows:
        return "No frequent product pairs were found yet."

    lines = ["Market basket analysis from saved orders:"]
    for row in rows:
        left, right = row["pair"]
        left_name, right_name = row["names"]
        lines.append(
            f"- {left} ({left_name}) + {right} ({right_name}) | "
            f"Support count: {row['support_count']} | "
            f"Support: {row['support']:.0%} | "
            f"Confidence {left}->{right}: {row['confidence_left_to_right']:.0%} | "
            f"Lift: {row['lift_left_to_right']:.2f}"
        )
    return "\n".join(lines)
