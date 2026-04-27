import time

from chatbot_engine import ChatbotEngine


def generate_response(tag, engine, bot_name):
    response = engine.get_response_text(tag)
    return f"{bot_name}: {response}"


if __name__ == "__main__":
    try:
        engine = ChatbotEngine.from_files("data.pth", "intents.json")
    except Exception as e:
        print(f"Error loading chatbot model: {e}")
        raise SystemExit

    test_queries = []
    for intent in engine.intents["intents"]:
        test_queries.extend(intent.get("queries", []))

    total_queries = len(test_queries)
    total_correct = 0
    total_wrong = 0
    total_time = 0

    bot_name = "Lyla"
    print("Response Generation Test Results:")

    for query in test_queries:
        start_time = time.time()
        tag, _probability = engine.predict(query)
        response = generate_response(tag, engine, bot_name)
        response_time = time.time() - start_time
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
    if total_queries:
        print(f"Average Response Time: {total_time / total_queries:.4f} seconds")
