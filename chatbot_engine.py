import json
import random

import torch

from model import NeuralNet
from nltk_utils import bag_of_words, tokenize


CONFIDENCE_THRESHOLD = 0.75
PRODUCT_QUESTION_TAGS = {"items", "product_availability", "sizes", "material"}


def get_device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_intents(file_path="intents.json"):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def is_cancel_order_request(user_input):
    normalized = user_input.lower()
    cancel_words = {"cancel", "delete", "remove"}
    return "order" in normalized and any(word in normalized for word in cancel_words)


def is_create_order_request(user_input):
    normalized = user_input.lower()
    create_words = {"create", "place", "make", "add", "buy"}
    return any(word in normalized for word in create_words) and (
        "order" in normalized or "product" in normalized
    )


def is_admin_login_request(user_input):
    return user_input.lower() in {"admin login", "login as admin", "admin"}


def is_admin_logout_request(user_input):
    return user_input.lower() in {"admin logout", "logout"}


def is_update_status_request(user_input):
    normalized = user_input.lower()
    status_words = {"status", "location", "shipped", "delivered", "processing"}
    update_words = {"update", "change", "set", "mark"}
    return (
        "order" in normalized
        and any(word in normalized for word in status_words)
        and any(word in normalized for word in update_words)
    )


def is_recommendation_request(user_input):
    normalized = user_input.lower()
    recommendation_words = {
        "recommend",
        "recommendation",
        "suggest",
        "suggestion",
        "similar",
        "personalized",
        "best match",
        "you think i should buy",
        "what should i buy",
    }
    return any(word in normalized for word in recommendation_words)


def is_product_popularity_request(user_input):
    normalized = user_input.lower()
    popularity_words = {
        "popular product",
        "popular products",
        "product popularity",
        "best selling",
        "best-selling",
        "top selling",
        "top products",
        "sales analysis",
        "analytics",
    }
    return any(word in normalized for word in popularity_words)


def is_market_basket_request(user_input):
    normalized = user_input.lower()
    basket_words = {
        "market basket",
        "apriori",
        "frequently bought together",
        "bought together",
        "product pairs",
        "basket analysis",
    }
    return any(word in normalized for word in basket_words)


def is_category_prediction_request(user_input):
    normalized = user_input.lower()
    category_words = {
        "predict category",
        "category prediction",
        "what category",
        "which category",
        "classify product",
        "classify this product",
        "product category",
    }
    return any(word in normalized for word in category_words)


class ChatbotEngine:
    def __init__(self, model, all_words, tags, intents, device=None):
        self.model = model
        self.all_words = all_words
        self.tags = tags
        self.intents = intents
        self.device = device or get_device()

    @classmethod
    def from_files(cls, model_path="data.pth", intents_path="intents.json"):
        device = get_device()
        data = torch.load(model_path, map_location=device)
        model = NeuralNet(
            data["input_size"],
            data["hidden_size"],
            data["output_size"],
        ).to(device)
        model.load_state_dict(data["model_state"])
        model.eval()
        return cls(
            model=model,
            all_words=data["all_words"],
            tags=data["tags"],
            intents=load_intents(intents_path),
            device=device,
        )

    def predict(self, sentence):
        tokens = tokenize(sentence)
        features = bag_of_words(tokens, self.all_words)
        features = features.reshape(1, features.shape[0])
        features = torch.from_numpy(features).to(self.device)

        with torch.no_grad():
            output = self.model(features)
            _, predicted = torch.max(output, dim=1)
            probs = torch.softmax(output, dim=1)

        tag = self.tags[predicted.item()]
        probability = probs[0][predicted.item()].item()
        return tag, probability

    def get_response_text(self, tag, context=None):
        for intent in self.intents["intents"]:
            if tag != intent["tag"]:
                continue

            if context:
                for response in intent["responses"]:
                    if "{context}" in response:
                        return response.format(context=context)

            response = random.choice(intent["responses"])
            if "{context}" in response:
                return response.format(context=tag)
            return response

        return "I do not understand..."
