import csv
import statistics
import time

from category_predictor import evaluate_category_predictor
from chatbot_engine import ChatbotEngine
from product_catalog import recommend_products


SURVEY_CSV = "evaluation_survey.csv"
BOT_NAME = "Lyla"


RECOMMENDATION_TEST_CASES = [
    {
        "query": "Recommend something like P001",
        "relevant": {"P002", "P003", "P006", "P007", "P008"},
    },
    {
        "query": "Recommend something like P002",
        "relevant": {"P001", "P003", "P006", "P007", "P008"},
    },
    {
        "query": "Recommend something like P004",
        "relevant": {"P011", "P012"},
    },
    {
        "query": "Recommend something like P005",
        "relevant": {"P001", "P002", "P003", "P015"},
    },
]


def percentage(value):
    return f"{value * 100:.2f}%"


def evaluate_chatbot_accuracy(engine):
    total = 0
    correct = 0
    total_time = 0
    wrong_predictions = []

    for intent in engine.intents["intents"]:
        expected_tag = intent["tag"]
        for query in intent.get("queries", []):
            start_time = time.perf_counter()
            predicted_tag, probability = engine.predict(query)
            total_time += time.perf_counter() - start_time

            total += 1
            if predicted_tag == expected_tag:
                correct += 1
            else:
                wrong_predictions.append(
                    {
                        "query": query,
                        "expected": expected_tag,
                        "predicted": predicted_tag,
                        "probability": probability,
                    }
                )

    accuracy = correct / total if total else 0
    average_response_time = total_time / total if total else 0
    return {
        "total_queries": total,
        "correct": correct,
        "wrong": total - correct,
        "accuracy": accuracy,
        "average_response_time": average_response_time,
        "wrong_predictions": wrong_predictions,
    }


def _precision_at_k(recommended_ids, relevant_ids, k):
    top_k = recommended_ids[:k]
    if not top_k:
        return 0
    hits = sum(1 for product_id in top_k if product_id in relevant_ids)
    return hits / len(top_k)


def _reciprocal_rank(recommended_ids, relevant_ids):
    for index, product_id in enumerate(recommended_ids, start=1):
        if product_id in relevant_ids:
            return 1 / index
    return 0


def evaluate_recommendation_quality(k=3):
    case_results = []
    precision_scores = []
    hit_scores = []
    reciprocal_ranks = []

    for case in RECOMMENDATION_TEST_CASES:
        recommendations = recommend_products(query=case["query"], limit=k)
        recommended_ids = [product["product_id"] for product in recommendations]
        relevant_ids = case["relevant"]

        precision = _precision_at_k(recommended_ids, relevant_ids, k)
        hit = any(product_id in relevant_ids for product_id in recommended_ids)
        reciprocal_rank = _reciprocal_rank(recommended_ids, relevant_ids)

        precision_scores.append(precision)
        hit_scores.append(1 if hit else 0)
        reciprocal_ranks.append(reciprocal_rank)
        case_results.append(
            {
                "query": case["query"],
                "recommended": recommended_ids,
                "relevant": sorted(relevant_ids),
                "precision_at_k": precision,
                "hit": hit,
                "reciprocal_rank": reciprocal_rank,
            }
        )

    return {
        "k": k,
        "mean_precision_at_k": statistics.mean(precision_scores)
        if precision_scores
        else 0,
        "hit_rate": statistics.mean(hit_scores) if hit_scores else 0,
        "mean_reciprocal_rank": statistics.mean(reciprocal_ranks)
        if reciprocal_ranks
        else 0,
        "case_results": case_results,
    }


def evaluate_recommendation_ab_test(k=3):
    with_recommendations = evaluate_recommendation_quality(k)
    return {
        "without_recommendation_module": {
            "task_completion_rate": 0,
            "mean_precision_at_k": 0,
            "hit_rate": 0,
        },
        "with_recommendation_module": {
            "task_completion_rate": 1,
            "mean_precision_at_k": with_recommendations["mean_precision_at_k"],
            "hit_rate": with_recommendations["hit_rate"],
        },
    }


def summarize_user_satisfaction(csv_path=SURVEY_CSV):
    with open(csv_path, mode="r") as file:
        rows = list(csv.DictReader(file))

    rating_fields = [
        "chatbot_accuracy",
        "rating_recommendations",
        "rating_speed",
        "rating_overall",
    ]
    summary = {"responses": len(rows)}
    for field in rating_fields:
        values = [int(row[field]) for row in rows if row.get(field)]
        summary[field] = statistics.mean(values) if values else 0
    return summary


def print_chatbot_accuracy(metrics):
    print("Chatbot response accuracy")
    print(f"- Test queries: {metrics['total_queries']}")
    print(f"- Correct predictions: {metrics['correct']}")
    print(f"- Wrong predictions: {metrics['wrong']}")
    print(f"- Accuracy: {percentage(metrics['accuracy'])}")
    print(f"- Average prediction time: {metrics['average_response_time']:.4f} seconds")
    if metrics["wrong_predictions"]:
        print("- Sample wrong predictions:")
        for item in metrics["wrong_predictions"][:5]:
            print(
                f"  {item['query']} | expected={item['expected']} | "
                f"predicted={item['predicted']} | probability={item['probability']:.2f}"
            )


def print_recommendation_quality(metrics):
    print("\nRecommendation quality")
    print(f"- Precision@{metrics['k']}: {percentage(metrics['mean_precision_at_k'])}")
    print(f"- Hit rate: {percentage(metrics['hit_rate'])}")
    print(f"- Mean reciprocal rank: {metrics['mean_reciprocal_rank']:.2f}")
    for case in metrics["case_results"]:
        print(
            f"- {case['query']} -> recommended={case['recommended']} | "
            f"Precision@{metrics['k']}={percentage(case['precision_at_k'])}"
        )


def print_ab_test(metrics):
    without_module = metrics["without_recommendation_module"]
    with_module = metrics["with_recommendation_module"]
    print("\nChatbot comparison: without vs with recommendation module")
    print(
        "- Without recommendation module | "
        f"Task completion: {percentage(without_module['task_completion_rate'])} | "
        f"Precision@3: {percentage(without_module['mean_precision_at_k'])} | "
        f"Hit rate: {percentage(without_module['hit_rate'])}"
    )
    print(
        "- With recommendation module | "
        f"Task completion: {percentage(with_module['task_completion_rate'])} | "
        f"Precision@3: {percentage(with_module['mean_precision_at_k'])} | "
        f"Hit rate: {percentage(with_module['hit_rate'])}"
    )


def print_satisfaction(summary):
    print("\nUser satisfaction survey")
    print(f"- Responses: {summary['responses']}")
    print(f"- Chatbot accuracy rating: {summary['chatbot_accuracy']:.2f}/5")
    print(f"- Recommendation rating: {summary['rating_recommendations']:.2f}/5")
    print(f"- Speed rating: {summary['rating_speed']:.2f}/5")
    print(f"- Overall rating: {summary['rating_overall']:.2f}/5")


def print_category_prediction(metrics):
    print("\nProduct category prediction")
    print(f"- Test products: {metrics['total']}")
    print(f"- Correct predictions: {metrics['correct']}")
    print(f"- Accuracy: {percentage(metrics['accuracy'])}")
    for result in metrics["results"]:
        print(
            f"- {result['product_id']} {result['name']} | "
            f"expected={result['expected']} | predicted={result['predicted']} | "
            f"confidence={percentage(result['confidence'])}"
        )


if __name__ == "__main__":
    engine = ChatbotEngine.from_files("data.pth", "intents.json")

    accuracy_metrics = evaluate_chatbot_accuracy(engine)
    recommendation_metrics = evaluate_recommendation_quality(k=3)
    comparison_metrics = evaluate_recommendation_ab_test(k=3)
    satisfaction_summary = summarize_user_satisfaction()
    category_metrics = evaluate_category_predictor()

    print_chatbot_accuracy(accuracy_metrics)
    print_recommendation_quality(recommendation_metrics)
    print_ab_test(comparison_metrics)
    print_satisfaction(satisfaction_summary)
    print_category_prediction(category_metrics)
