import json
import random

import torch

from db import (
    create_order,
    delete_order,
    fetch_order_info,
    init_db,
    seed_from_csv,
    update_address,
    verify_customer_email,
)
from model import NeuralNet
from nltk_utils import bag_of_words, tokenize
from product_catalog import format_product, format_product_list, get_product_by_id, load_products


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
bot_name = "Lyla"
intents = None
input_size = hidden_size = output_size = all_words = tags = model_state = None
PRODUCT_QUESTION_TAGS = {"items", "product_availability", "sizes", "material"}


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


def get_user_input():
    return input("You: ").lower()


def handle_exit_commands(sentence, bot_name):
    exit_commands = ["quit", "exit", "bye", "thanks", "that's all thanks", "goodbye"]
    if sentence in exit_commands:
        print(f"{bot_name}: Goodbye! Have a great day!")
        return True
    return False


def handle_special_cases(sentence, bot_name):
    special_cases = {
        "I don't understand": "I apologize for any confusion. Please feel free to ask again.",
        "I have to go": "Alright! Take care and see you soon!",
    }
    if sentence in special_cases:
        print(f"{bot_name}: {special_cases[sentence]}")
        return True
    return False


def get_model_output(sentence, all_words, tags, model, device):
    sentence = tokenize(sentence)
    X = bag_of_words(sentence, all_words)
    X = X.reshape(1, X.shape[0])
    X = torch.from_numpy(X).to(device)

    output = model(X)
    _, predicted = torch.max(output, dim=1)
    tag = tags[predicted.item()]

    probs = torch.softmax(output, dim=1)
    prob = probs[0][predicted.item()]

    return tag, prob.item()


def is_cancel_order_request(user_input):
    normalized = user_input.lower()
    cancel_words = ["cancel", "delete", "remove"]
    return "order" in normalized and any(word in normalized for word in cancel_words)


def is_create_order_request(user_input):
    normalized = user_input.lower()
    create_words = ["create", "place", "make", "add", "buy"]
    return any(word in normalized for word in create_words) and (
        "order" in normalized or "product" in normalized
    )


def get_response(tag, prob, intents, bot_name, context=None):
    if prob <= 0.75:
        print(f"{bot_name}: I do not understand...")
        return

    for intent in intents['intents']:
        if tag != intent["tag"]:
            continue

        if context:
            for response in intent['responses']:
                if "{context}" in response:
                    print(f"{bot_name}: {response.format(context=context)}")
                    return

            print(f"{bot_name}: {random.choice(intent['responses'])}")
            return

        if tag == "order_status":
            print(f"{bot_name}: {random.choice(intent['responses'])}")
            order_number = input("Please enter your order number: ")
            track_order(order_number)
        elif tag == "update_address":
            print(f"{bot_name}: {random.choice(intent['responses'])}")
            update_address_cli()
        elif tag == "create_order":
            print(f"{bot_name}: {random.choice(intent['responses'])}")
            create_order_cli()
        elif tag == "cancel_order":
            print(f"{bot_name}: {random.choice(intent['responses'])}")
            cancel_order_cli()
        elif tag in PRODUCT_QUESTION_TAGS:
            print(f"{bot_name}: {random.choice(intent['responses'])}")
            show_products_cli()
        else:
            response = random.choice(intent['responses'])
            if "{context}" in response:
                context = intent["tag"]
                print(f"{bot_name}: {response.format(context=context)}")
            else:
                print(f"{bot_name}: {response}")
        return


def update_address_cli():
    email = input("Please provide your email for verification: ")
    order_number = input("Please enter your order number: ")

    if not verify_customer_email(order_number, email):
        print(f"{bot_name}: Email verification failed.")
        return

    current_address = fetch_order_info(order_number)['customer_address']
    print(
        f"{bot_name}: Your current registered address is: "
        f"{current_address}"
    )

    new_address = input("Please enter your new address: ")
    print(f"{bot_name}: You entered the following address: {new_address}")
    confirmation = input("Are you sure this is your new address? (yes/no): ")

    if confirmation.lower() == "yes":
        update_address(order_number, new_address)
        print(f"{bot_name}: Your address has been updated.")
    else:
        print(f"{bot_name}: Address update cancelled.")


def track_order(order_number):
    order_info = fetch_order_info(order_number)
    if order_info:
        print("")
        print("Order Information:")
        print(f"Order Number: {order_info['order_number']}")
        print(f"Status: {order_info['status']}")
        print(f"Current Location: {order_info['current_location']}")
        print(f"Destination Address: {order_info['customer_address']}")
        print(f"Expected Delivery Date: {order_info['expected_delivery_date']}")
        print(f"Product: {order_info.get('product_name') or 'N/A'}")
        print(f"Quantity: {order_info.get('quantity') or 'N/A'}")
        print(f"Total Price: {order_info.get('total_price') or 'N/A'}")
        print("")
    else:
        print("Order not found.")


def show_products_cli():
    products = load_products()
    print("")
    print("Available Products:")
    print(format_product_list(products))
    print("")


def select_product_cli():
    products = load_products()
    if not products:
        print(f"{bot_name}: No products are available right now.")
        return None

    print("")
    print("Available Products:")
    print(format_product_list(products))
    print("")
    product_id = input("Enter the product ID for this order: ").strip()
    product = get_product_by_id(product_id)
    if not product:
        print(f"{bot_name}: Product not found.")
        return None
    return product


def create_order_cli(selected_product=None):
    product = selected_product or select_product_cli()
    if not product:
        return

    order_number = input("Enter order number: ").strip()
    customer_name = input("Enter customer name (optional): ").strip()
    customer_email = input("Enter customer email: ").strip()
    customer_address = input("Enter customer address: ").strip()
    status = input("Enter order status (e.g. Processing): ").strip()
    current_location = input("Enter current location: ").strip()
    quantity_input = input("Enter quantity: ").strip()
    expected_delivery_date = input(
        "Enter expected delivery date (dd/mm/yyyy) or leave blank: "
    ).strip()

    try:
        quantity = int(quantity_input)
    except ValueError:
        print("Quantity must be a number.")
        return

    if (
        not order_number
        or not customer_email
        or not customer_address
        or not status
        or not current_location
        or quantity < 1
    ):
        print("Order number, email, address, status, location, and quantity are required.")
        return

    try:
        unit_price = float(product["price"])
        total_price = unit_price * quantity
        ok, message = create_order(
            order_number=order_number,
            customer_email=customer_email,
            customer_address=customer_address,
            customer_name=customer_name or None,
            status=status,
            current_location=current_location,
            expected_delivery_date=expected_delivery_date or None,
            product_id=product["product_id"],
            product_name=product["name"],
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price,
        )
        if ok:
            print("Order created successfully.")
            print(f"Product: {format_product(product)}")
            print(f"Quantity: {quantity}")
            print(f"Total: ${total_price:.2f}")
        else:
            print(message)
    except Exception as e:
        print(f"Failed to create order: {e}")


def cancel_order_cli():
    order_number = input("Please enter the order number to cancel: ").strip()
    email = input("Please provide your email for verification: ").strip()

    if not order_number or not email:
        print(f"{bot_name}: Order number and email are required.")
        return

    if not verify_customer_email(order_number, email):
        print(f"{bot_name}: Email verification failed.")
        return

    confirmation = input(
        f"Are you sure you want to cancel order {order_number}? (yes/no): "
    )
    if confirmation.lower() != "yes":
        print(f"{bot_name}: Order cancellation cancelled.")
        return

    if delete_order(order_number):
        print(f"{bot_name}: Your order has been cancelled and deleted from the database.")
    else:
        print(f"{bot_name}: Order not found.")


if __name__ == "__main__":
    try:
        init_db()
        seed_from_csv("orders.csv")
    except Exception as e:
        print(f"Error initializing database: {e}")

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

    model = NeuralNet(input_size, hidden_size, output_size).to(device)
    model.load_state_dict(model_state)
    model.eval()

    try:
        with open("intents.json", 'r') as file:
            intents = json.load(file)
    except Exception as e:
        print(f"Error loading intents data: {e}")
        raise SystemExit

    bot_name = "Lyla"
    context = None

    print(
        "Hello! I am Lyla from CoffeeMugs. What do you need? "
        "(type 'quit', 'exit', or 'bye' to exit)"
    )

    while True:
        sentence = get_user_input()

        if handle_exit_commands(sentence, bot_name) or handle_special_cases(sentence, bot_name):
            break

        if is_cancel_order_request(sentence):
            tag, prob = "cancel_order", 1.0
        elif is_create_order_request(sentence):
            tag, prob = "create_order", 1.0
        else:
            tag, prob = get_model_output(sentence, all_words, tags, model, device)
        get_response(tag, prob, intents, bot_name, context)
