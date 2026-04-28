import csv
import os
import re
from collections import Counter


PRODUCTS_CSV = "products.csv"
PRODUCT_ID_PATTERN = re.compile(r"\bP\d{3,}\b", re.IGNORECASE)


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


def find_product_reference(text, csv_path=PRODUCTS_CSV):
    normalized = (text or "").strip().lower()
    if not normalized:
        return None

    product_id_match = PRODUCT_ID_PATTERN.search(normalized)
    if product_id_match:
        product = get_product_by_id(product_id_match.group(0), csv_path)
        if product:
            return product

    for product in load_products(csv_path):
        name = product["name"].lower()
        if name in normalized or normalized in name:
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


def _product_tokens(product):
    text = " ".join(
        [
            product.get("name", ""),
            product.get("category", ""),
            product.get("color", ""),
            product.get("size", ""),
            product.get("material", ""),
            product.get("description", ""),
        ]
    ).lower()
    return set(re.findall(r"[a-z0-9]+", text))


def _price(product):
    try:
        return float(product.get("price") or 0)
    except ValueError:
        return 0


def _stock(product):
    try:
        return int(product.get("stock") or 0)
    except ValueError:
        return 0


def _similarity_score(candidate, source):
    score = 0
    if candidate.get("category") == source.get("category"):
        score += 4
    if candidate.get("material") == source.get("material"):
        score += 2
    if candidate.get("color") == source.get("color"):
        score += 1.5
    if candidate.get("size") == source.get("size"):
        score += 1

    candidate_tokens = _product_tokens(candidate)
    source_tokens = _product_tokens(source)
    if candidate_tokens or source_tokens:
        overlap = len(candidate_tokens & source_tokens)
        union = len(candidate_tokens | source_tokens)
        score += 2 * (overlap / union)

    price_gap = abs(_price(candidate) - _price(source))
    score += max(0, 1 - (price_gap / 25))
    score += min(_stock(candidate), 20) / 20
    return score


def _preference_profile(products):
    profile = {
        "category": Counter(),
        "color": Counter(),
        "material": Counter(),
        "size": Counter(),
    }
    for product in products:
        for field in profile:
            value = product.get(field)
            if value:
                profile[field][value] += 1
    return profile


def _preference_score(candidate, profile):
    weights = {
        "category": 3,
        "material": 2,
        "color": 1.5,
        "size": 1,
    }
    return sum(
        weights[field] * profile[field][candidate.get(field, "")]
        for field in profile
    )


def recommend_products(
    query=None,
    viewed_product_ids=None,
    cart_product_ids=None,
    limit=3,
    csv_path=PRODUCTS_CSV,
):
    products = load_products(csv_path)
    if not products:
        return []

    product_by_id = {product["product_id"]: product for product in products}
    source_products = []
    explicit_source_ids = set()
    explicit_product = find_product_reference(query, csv_path)
    if explicit_product:
        source_products.append(explicit_product)
        explicit_source_ids.add(explicit_product["product_id"])

    cart_ids = set(cart_product_ids or [])
    if not explicit_product:
        for product_id in cart_product_ids or []:
            product = product_by_id.get(product_id)
            if product and product not in source_products:
                source_products.append(product)

        for product_id in viewed_product_ids or []:
            product = product_by_id.get(product_id)
            if product and product not in source_products:
                source_products.append(product)

    viewed_ids = set(viewed_product_ids or [])
    source_ids = explicit_source_ids
    if not explicit_product:
        source_ids |= cart_ids
    if not explicit_product and len(viewed_ids) < len(products):
        source_ids |= viewed_ids
    candidates = [product for product in products if product["product_id"] not in source_ids]

    if not candidates:
        candidates = products

    if not source_products:
        ranked = sorted(
            candidates,
            key=lambda product: (
                _stock(product),
                product.get("category") == "Gift Set",
                -_price(product),
            ),
            reverse=True,
        )
        return ranked[:limit]

    profile = _preference_profile(source_products)
    ranked = sorted(
        candidates,
        key=lambda product: (
            max(_similarity_score(product, source) for source in source_products)
            + _preference_score(product, profile),
            _stock(product),
        ),
        reverse=True,
    )
    return ranked[:limit]


def recommendation_reason(product, source_products=None):
    source_products = source_products or []
    if source_products:
        source = source_products[0]
        matching_fields = [
            field
            for field in ("category", "material", "color", "size")
            if product.get(field) == source.get(field)
        ]
        if matching_fields:
            return "matches your interest in " + ", ".join(matching_fields)
    if _stock(product) > 0:
        return "available now and fits common mug preferences"
    return "closest catalog match"


def format_recommendation_list(products):
    if not products:
        return "I do not have enough product data to make recommendations right now."
    lines = ["Recommended products:"]
    for product in products:
        lines.append(f"- {format_product(product)}")
    return "\n".join(lines)
