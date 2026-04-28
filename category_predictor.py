import math
import re
from collections import Counter, defaultdict

from product_catalog import find_product_reference, load_products


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize_text(text):
    return TOKEN_PATTERN.findall((text or "").lower())


def product_text(product):
    return " ".join(
        [
            product.get("name", ""),
            product.get("color", ""),
            product.get("size", ""),
            product.get("material", ""),
            product.get("description", ""),
        ]
    )


class ProductCategoryPredictor:
    def __init__(self):
        self.category_counts = Counter()
        self.token_counts = defaultdict(Counter)
        self.total_tokens = Counter()
        self.vocabulary = set()
        self.total_examples = 0

    def fit(self, products):
        for product in products:
            category = product.get("category")
            if not category:
                continue

            self.category_counts[category] += 1
            self.total_examples += 1
            for token in tokenize_text(product_text(product)):
                self.token_counts[category][token] += 1
                self.total_tokens[category] += 1
                self.vocabulary.add(token)
        return self

    def predict_proba(self, text):
        tokens = tokenize_text(text)
        if not self.category_counts:
            return {}

        vocabulary_size = max(len(self.vocabulary), 1)
        scores = {}
        for category, category_count in self.category_counts.items():
            score = math.log(category_count / self.total_examples)
            denominator = self.total_tokens[category] + vocabulary_size
            for token in tokens:
                numerator = self.token_counts[category][token] + 1
                score += math.log(numerator / denominator)
            scores[category] = score

        max_score = max(scores.values())
        exp_scores = {
            category: math.exp(score - max_score)
            for category, score in scores.items()
        }
        total = sum(exp_scores.values())
        return {
            category: score / total
            for category, score in exp_scores.items()
        }

    def predict(self, text):
        probabilities = self.predict_proba(text)
        if not probabilities:
            return None, 0
        category, probability = max(
            probabilities.items(),
            key=lambda item: item[1],
        )
        return category, probability


def train_category_predictor(csv_path="products.csv"):
    products = load_products(csv_path)
    return ProductCategoryPredictor().fit(products)


def predict_category(query, csv_path="products.csv"):
    product = find_product_reference(query, csv_path)
    text = product_text(product) if product else query
    predictor = train_category_predictor(csv_path)
    category, probability = predictor.predict(text)
    return {
        "category": category,
        "confidence": probability,
        "matched_product": product,
    }


def format_category_prediction(result):
    if not result["category"]:
        return "I do not have enough product data to predict a category."

    source = ""
    if result.get("matched_product"):
        product = result["matched_product"]
        source = f" for {product['product_id']} - {product['name']}"

    return (
        f"Predicted category{source}: {result['category']} "
        f"(confidence: {result['confidence'] * 100:.2f}%)."
    )


def evaluate_category_predictor(csv_path="products.csv"):
    products = load_products(csv_path)
    if not products:
        return {
            "total": 0,
            "correct": 0,
            "accuracy": 0,
            "results": [],
        }

    predictor = train_category_predictor(csv_path)
    results = []
    correct = 0
    for product in products:
        predicted_category, confidence = predictor.predict(product_text(product))
        expected_category = product.get("category")
        is_correct = predicted_category == expected_category
        if is_correct:
            correct += 1
        results.append(
            {
                "product_id": product.get("product_id"),
                "name": product.get("name"),
                "expected": expected_category,
                "predicted": predicted_category,
                "confidence": confidence,
                "correct": is_correct,
            }
        )

    total = len(products)
    return {
        "total": total,
        "correct": correct,
        "accuracy": correct / total if total else 0,
        "results": results,
    }
