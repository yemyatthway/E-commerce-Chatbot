import json
import random
import time

import torch

from model import NeuralNet
from nltk_utils import bag_of_words, tokenize


def load_model_data(file_path):
    try:
        data = torch.load(file_path)
        return (
            data["input_size"],
            data["hidden_size"],
            data["output_size"],
            data['all_words'],
            data['tags'],
            data["model_state"],
        )
    except Exception as e:
        print(f"Error loading model data: {e}")
        return None, None, None, None, None, None


def generate_response(tag, intents, bot_name):
    for intent in intents['intents']:
        if tag == intent["tag"]:
            response = random.choice(intent['responses'])
            return f"{bot_name}: {response}"
    return f"{bot_name}: I do not understand..."


if __name__ == "__main__":
    (
        input_size,
        hidden_size,
        output_size,
        all_words,
        tags,
        model_state,
    ) = load_model_data("data.pth")

    if None in [input_size, hidden_size, output_size, all_words, tags, model_state]:
        raise SystemExit

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = NeuralNet(input_size, hidden_size, output_size).to(device)
    model.load_state_dict(model_state)
    model.eval()

    try:
        with open("intents.json", 'r') as file:
            intents = json.load(file)
    except Exception as e:
        print(f"Error loading intents data: {e}")
        raise SystemExit

    test_queries = []
    for intent in intents['intents']:
        if 'queries' in intent:
            test_queries.extend(intent['queries'])

    total_queries = len(test_queries)
    total_correct = 0
    total_wrong = 0
    total_time = 0

    bot_name = "Lyla"
    print("Response Generation Test Results:")

    for query in test_queries:
        start_time = time.time()

        sentence = tokenize(query)
        X = bag_of_words(sentence, all_words)
        X = X.reshape(1, X.shape[0])
        X = torch.from_numpy(X).to(device)

        output = model(X)
        _, predicted = torch.max(output, dim=1)
        tag = tags[predicted.item()]

        response = generate_response(tag, intents, bot_name)
        end_time = time.time()
        response_time = end_time - start_time
        total_time += response_time

        print(f"Query: {query}")
        print(f"{response} (Response time: {response_time:.4f} seconds)")
        user_input = input("Press Enter if correct, Space if wrong: ")
        if user_input == "":
            total_correct += 1
        elif user_input == " ":
            total_wrong += 1
        else:
            print("Invalid input. Skipping...")
        print()

    print("\nSummary:")
    print(f"Total Queries: {total_queries}")
    print(f"Total Correct: {total_correct}")
    print(f"Total Wrong: {total_wrong}")
    print(f"Average Response Time: {total_time / total_queries:.4f} seconds")
