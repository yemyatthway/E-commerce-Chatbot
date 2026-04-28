from chatbot_engine import ChatbotEngine


if __name__ == "__main__":
    try:
        engine = ChatbotEngine.from_files("data.pth", "intents.json")
    except Exception as e:
        print(f"Error loading chatbot model: {e}")
        raise SystemExit

    total_intents = len(engine.intents["intents"])
    total_correct = 0
    total_wrong = 0

    print("Intent Recognition Test Results:")
    for intent in engine.intents["intents"]:
        print(f"Intent: {intent['tag']}")
        for query in intent.get("queries", []):
            predicted_intent, _probability = engine.predict(query)
            print(f"Query: {query}")
            print(f"Predicted Intent: {predicted_intent}")
            user_input = input("Press Enter if correct, Space if wrong: ")
            if user_input == "":
                total_correct += 1
            elif user_input == " ":
                total_wrong += 1
            else:
                print("Invalid input. Skipping...")
            print()

    print("\nSummary:")
    print(f"Total Tags: {total_intents}")
    print(f"Total Correct: {total_correct}")
    print(f"Total Wrong: {total_wrong}")

