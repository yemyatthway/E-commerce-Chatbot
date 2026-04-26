import csv
import os


PRODUCTS_CSV = "products.csv"


def load_products(csv_path=PRODUCTS_CSV):
    if not os.path.exists(csv_path):
        return []

    with open(csv_path, mode="r") as file:
        return list(csv.DictReader(file))


def get_product_by_id(product_id, csv_path=PRODUCTS_CSV):
    product_id = (product_id or "").strip().lower()
    for product in load_products(csv_path):
        if product["product_id"].lower() == product_id:
            return product
    return None


def format_product(product):
    return (
        f"{product['product_id']} - {product['name']} | "
        f"{product['color']} | {product['size']} | "
        f"${product['price']} | Stock: {product['stock']}"
    )


def format_product_list(products):
    if not products:
        return "No products are available right now."
    return "\n".join(format_product(product) for product in products)
