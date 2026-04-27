from chatbot_engine import (
    CONFIDENCE_THRESHOLD,
    PRODUCT_QUESTION_TAGS,
    ChatbotEngine,
    is_admin_login_request,
    is_admin_logout_request,
    is_cancel_order_request,
    is_create_order_request,
    is_update_status_request,
)
from db import (
    authenticate_user,
    create_order,
    delete_order,
    fetch_order_info,
    init_db,
    seed_from_csv,
    update_address,
    update_order_status,
    verify_customer_email,
)
from product_catalog import format_product, format_product_list, get_product_by_id, load_products


bot_name = "Lyla"


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


def get_response(tag, prob, engine, bot_name, current_user=None, context=None):
    if prob <= CONFIDENCE_THRESHOLD:
        print(f"{bot_name}: I do not understand...")
        return

    print(f"{bot_name}: {engine.get_response_text(tag, context)}")
    if tag == "order_status":
        order_number = input("Please enter your order number: ")
        track_order(order_number)
    elif tag == "update_address":
        update_address_cli()
    elif tag == "create_order":
        create_order_cli()
    elif tag == "cancel_order":
        cancel_order_cli()
    elif tag == "admin_login":
        return admin_login_cli()
    elif tag == "update_order_status":
        update_order_status_cli(current_user)
    elif tag in PRODUCT_QUESTION_TAGS:
        show_products_cli()

    return current_user


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

    customer_name = input("Enter customer name: ").strip()
    customer_email = input("Enter customer email: ").strip()
    customer_address = input("Enter customer address: ").strip()
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
        not customer_name
        or not customer_email
        or not customer_address
        or quantity < 1
    ):
        print("Customer name, email, address, and quantity are required.")
        return

    try:
        unit_price = float(product["price"])
        total_price = unit_price * quantity
        ok, message = create_order(
            customer_email=customer_email,
            customer_address=customer_address,
            customer_name=customer_name,
            status="Processing",
            current_location="Warehouse",
            expected_delivery_date=expected_delivery_date or None,
            product_id=product["product_id"],
            product_name=product["name"],
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price,
        )
        if ok:
            print(message)
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


def admin_login_cli():
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    if not username or not password:
        print(f"{bot_name}: Username and password are required.")
        return None

    user = authenticate_user(username, password)
    if not user or user.get("role") != "admin":
        print(f"{bot_name}: Admin login failed.")
        return None

    print(f"{bot_name}: Admin login successful. Welcome, {user.get('full_name') or username}.")
    return user


def admin_logout_cli(current_user):
    if not current_user:
        print(f"{bot_name}: No admin is logged in.")
        return None

    print(f"{bot_name}: Admin logged out.")
    return None


def update_order_status_cli(current_user):
    if not current_user or current_user.get("role") != "admin":
        print(f"{bot_name}: Only an admin can update order status. Type 'admin login' first.")
        return

    order_number = input("Enter order number: ").strip()
    status = input("Enter new status (Processing, Shipped, Delivered, Cancelled): ").strip()
    current_location = input("Enter current location, or leave blank to keep existing: ").strip()

    if not order_number or not status:
        print(f"{bot_name}: Order number and status are required.")
        return

    if update_order_status(order_number, status, current_location or None):
        print(f"{bot_name}: Order status updated successfully.")
    else:
        print(f"{bot_name}: Order not found.")


if __name__ == "__main__":
    try:
        init_db()
        seed_from_csv("orders.csv")
    except Exception as e:
        print(f"Error initializing database: {e}")

    try:
        engine = ChatbotEngine.from_files("data.pth", "intents.json")
    except Exception as e:
        print(f"Error loading chatbot model: {e}")
        raise SystemExit

    bot_name = "Lyla"
    context = None
    current_user = None

    print(
        "Hello! I am Lyla from CoffeeMugs. What do you need? "
        "(type 'quit', 'exit', or 'bye' to exit)"
    )

    while True:
        sentence = get_user_input()

        if handle_exit_commands(sentence, bot_name) or handle_special_cases(sentence, bot_name):
            break

        if is_admin_login_request(sentence):
            tag, prob = "admin_login", 1.0
        elif is_admin_logout_request(sentence):
            current_user = admin_logout_cli(current_user)
            continue
        elif is_update_status_request(sentence):
            tag, prob = "update_order_status", 1.0
        elif is_cancel_order_request(sentence):
            tag, prob = "cancel_order", 1.0
        elif is_create_order_request(sentence):
            tag, prob = "create_order", 1.0
        else:
            tag, prob = engine.predict(sentence)
        current_user = get_response(tag, prob, engine, bot_name, current_user, context)
