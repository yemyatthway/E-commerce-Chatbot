import tkinter as tk
from tkinter import font
from tkinter import simpledialog

from chatbot_features import (
    category_prediction_message,
    market_basket_message,
    product_popularity_message,
    recommendation_message,
)
from chatbot_engine import (
    CONFIDENCE_THRESHOLD,
    PRODUCT_QUESTION_TAGS,
    ChatbotEngine,
    is_admin_login_request,
    is_admin_logout_request,
    is_cancel_order_request,
    is_category_prediction_request,
    is_create_order_request,
    is_market_basket_request,
    is_product_popularity_request,
    is_recommendation_request,
    is_update_status_request,
)
from db import (
    authenticate_user,
    create_order,
    delete_order,
    fetch_customer_address,
    fetch_order_info,
    init_db,
    seed_from_csv,
    update_address,
    update_order_status,
    verify_customer_email,
)
from product_catalog import (
    format_product,
    format_product_list,
    get_product_by_id,
    load_products,
)


class ChatGUI:
    def __init__(self, master):
        self.master = master
        master.title("E-commerce Chatbot")
        master.geometry("520x680")
        master.minsize(460, 560)
        master.configure(bg="#101827")
        master.option_add("*Font", "Helvetica 11")
        master.columnconfigure(0, weight=1)
        master.rowconfigure(1, weight=1)

        self.bot_name = "bot4urLIF3"
        self.current_user = None
        self.viewed_product_ids = set()
        self.cart_product_ids = []
        self.setup_styles()
        self.build_header()
        self.build_chat_area()
        self.build_input_area()

        self.engine = ChatbotEngine.from_files("data.pth", "intents.json")
        self.setup_database()
        self.display_message(
            self.bot_name,
            "Hi, I am bot4urLIF3. How can I help you today?",
        )

    def setup_styles(self):
        self.colors = {
            "app_bg": "#101827",
            "header_bg": "#162033",
            "panel": "#0b1220",
            "panel_border": "#263349",
            "text": "#e5edf8",
            "muted": "#91a3ba",
            "bot": "#6ea8fe",
            "user": "#5eead4",
            "bot_bubble": "#17233a",
            "user_bubble": "#123b3a",
            "button": "#3b82f6",
            "button_active": "#2563eb",
            "entry_bg": "#111c2f",
        }
        self.fonts = {
            "title": font.Font(family="Helvetica", size=18, weight="bold"),
            "subtitle": font.Font(family="Helvetica", size=10),
            "body": font.Font(family="Helvetica", size=12),
            "message": font.Font(family="Helvetica", size=12),
            "sender": font.Font(family="Helvetica", size=11, weight="bold"),
            "button": font.Font(family="Helvetica", size=11, weight="bold"),
        }

    def build_header(self):
        header = tk.Frame(self.master, bg=self.colors["header_bg"])
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 10))
        header.columnconfigure(0, weight=1)

        title = tk.Label(
            header,
            text="E-commerce Chatbot",
            bg=self.colors["header_bg"],
            fg=self.colors["text"],
            font=self.fonts["title"],
            anchor="w",
        )
        title.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 0))

        subtitle = tk.Label(
            header,
            text="Customer support assistant",
            bg=self.colors["header_bg"],
            fg=self.colors["muted"],
            font=self.fonts["subtitle"],
            anchor="w",
        )
        subtitle.grid(row=1, column=0, sticky="w", padx=16, pady=(3, 14))

        status = tk.Label(
            header,
            text="Online",
            bg=self.colors["header_bg"],
            fg="#86efac",
            font=self.fonts["subtitle"],
        )
        status.grid(row=0, column=1, rowspan=2, sticky="e", padx=16)

    def build_chat_area(self):
        chat_shell = tk.Frame(
            self.master,
            bg=self.colors["panel"],
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.colors["panel_border"],
            highlightcolor=self.colors["bot"],
        )
        chat_shell.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 12))
        chat_shell.columnconfigure(0, weight=1)
        chat_shell.rowconfigure(0, weight=1)

        self.chat_canvas = tk.Canvas(
            chat_shell,
            bg=self.colors["panel"],
            bd=0,
            highlightthickness=0,
        )
        self.chat_canvas.grid(row=0, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(
            chat_shell,
            orient=tk.VERTICAL,
            command=self.chat_canvas.yview,
            relief=tk.FLAT,
            borderwidth=0,
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        scrollbar.configure(
            bg=self.colors["panel"],
            activebackground=self.colors["panel_border"],
            troughcolor=self.colors["panel"],
        )
        self.chat_canvas.configure(yscrollcommand=scrollbar.set)

        self.messages_frame = tk.Frame(self.chat_canvas, bg=self.colors["panel"])
        self.messages_window = self.chat_canvas.create_window(
            0,
            0,
            window=self.messages_frame,
            anchor="nw",
        )
        self.chat_canvas.bind("<Configure>", self.resize_chat_content)
        self.messages_frame.bind("<Configure>", self.update_chat_scroll_region)
        self.bind_mousewheel(self.chat_canvas)
        self.bind_mousewheel(self.messages_frame)

    def resize_chat_content(self, event):
        self.chat_canvas.itemconfigure(self.messages_window, width=event.width)
        self.draw_chat_background(event.width, event.height)

    def update_chat_scroll_region(self, _event=None):
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))

    def draw_chat_background(self, width, height):
        self.chat_canvas.delete("chat_bg")
        for x in range(-height, width, 96):
            self.chat_canvas.create_line(
                x,
                height,
                x + height,
                0,
                fill="#111c2f",
                width=1,
                tags="chat_bg",
            )
        for x in range(28, width, 96):
            for y in range(28, height, 96):
                self.chat_canvas.create_oval(
                    x,
                    y,
                    x + 2,
                    y + 2,
                    fill="#1c2b45",
                    outline="",
                    tags="chat_bg",
                )
        self.chat_canvas.tag_lower("chat_bg")

    def bind_mousewheel(self, widget):
        widget.bind("<MouseWheel>", self.on_chat_mousewheel)
        widget.bind("<Button-4>", self.on_chat_mousewheel)
        widget.bind("<Button-5>", self.on_chat_mousewheel)

    def on_chat_mousewheel(self, event):
        if getattr(event, "num", None) == 4:
            self.chat_canvas.yview_scroll(-1, "units")
        elif getattr(event, "num", None) == 5:
            self.chat_canvas.yview_scroll(1, "units")
        else:
            direction = -1 if event.delta > 0 else 1
            self.chat_canvas.yview_scroll(direction, "units")

    def build_input_area(self):
        input_frame = tk.Frame(self.master, bg=self.colors["app_bg"])
        input_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 16))
        input_frame.columnconfigure(0, weight=1)

        self.input_field = tk.Entry(
            input_frame,
            bg=self.colors["entry_bg"],
            fg=self.colors["text"],
            insertbackground=self.colors["bot"],
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=self.colors["panel_border"],
            highlightcolor=self.colors["bot"],
            font=self.fonts["body"],
        )
        self.input_field.grid(row=0, column=0, sticky="ew", padx=(0, 10), ipady=11)
        self.input_field.bind("<Return>", self.send_message)

        self.send_button = tk.Label(
            input_frame,
            text="Send",
            bg=self.colors["button"],
            fg="#ffffff",
            cursor="hand2",
            font=self.fonts["button"],
            padx=22,
            pady=12,
        )
        self.send_button.grid(row=0, column=1)
        self.send_button.bind("<Button-1>", self.send_message)
        self.send_button.bind("<Enter>", self.on_send_hover)
        self.send_button.bind("<Leave>", self.on_send_leave)

    def on_send_hover(self, _event=None):
        self.send_button.configure(bg=self.colors["button_active"])

    def on_send_leave(self, _event=None):
        self.send_button.configure(bg=self.colors["button"])

    def setup_database(self):
        try:
            init_db()
            seed_from_csv("orders.csv")
        except Exception as e:
            print(f"Error initializing database: {e}")

    def send_message(self, event=None):
        user_input = self.input_field.get().strip()
        if not user_input:
            return
        self.input_field.delete(0, tk.END)
        self.display_message("You", user_input)
        self.generate_bot_response(user_input)

    def generate_bot_response(self, user_input):
        if is_admin_login_request(user_input):
            self.admin_login_gui()
            return
        if is_admin_logout_request(user_input):
            self.admin_logout()
            return
        if is_update_status_request(user_input):
            self.update_order_status_gui()
            return
        if is_cancel_order_request(user_input):
            self.get_response("cancel_order", 1.0)
            return
        if is_create_order_request(user_input):
            self.get_response("create_order", 1.0)
            return
        if is_recommendation_request(user_input):
            self.show_recommendations_gui(user_input)
            return
        if is_market_basket_request(user_input):
            self.show_market_basket_gui()
            return
        if is_product_popularity_request(user_input):
            self.show_product_popularity_gui()
            return
        if is_category_prediction_request(user_input):
            self.show_category_prediction_gui(user_input)
            return

        tag, prob = self.engine.predict(user_input)
        self.get_response(tag, prob, user_input)

    def is_admin(self):
        return self.current_user and self.current_user.get("role") == "admin"

    def get_response(self, tag, prob, user_input=None):
        if prob <= CONFIDENCE_THRESHOLD:
            self.display_message(
                self.bot_name,
                "I do not understand, please rephrase your question so I can better assist you.",
            )
            return

        if tag == "recommendations":
            self.show_recommendations_gui(user_input or "")
            return

        self.display_message(self.bot_name, self.engine.get_response_text(tag))
        if tag == "order_status":
            self.track_order_gui()
        elif tag == "update_address":
            self.update_address_gui()
        elif tag == "create_order":
            self.create_order_gui()
        elif tag == "cancel_order":
            self.cancel_order_gui()
        elif tag == "admin_login":
            self.admin_login_gui()
        elif tag == "update_order_status":
            self.update_order_status_gui()
        elif tag in PRODUCT_QUESTION_TAGS:
            self.show_products_gui()

    def display_message(self, sender, message):
        is_user = sender == "You"
        row = tk.Frame(self.messages_frame, bg=self.colors["panel"])
        row.pack(fill=tk.X, padx=18, pady=(14, 4))

        content = tk.Frame(row, bg=self.colors["panel"])
        content.pack(anchor="e" if is_user else "w")

        sender_label = tk.Label(
            content,
            text=sender,
            bg=self.colors["panel"],
            fg=self.colors["user"] if is_user else self.colors["bot"],
            font=self.fonts["sender"],
        )
        sender_label.pack(anchor="e" if is_user else "w", pady=(0, 4))

        bubble = tk.Label(
            content,
            text=message,
            bg=self.colors["user_bubble"] if is_user else self.colors["bot_bubble"],
            fg=self.colors["text"],
            font=self.fonts["message"],
            justify=tk.LEFT,
            anchor="w",
            padx=14,
            pady=10,
            wraplength=380,
        )
        bubble.pack(anchor="e" if is_user else "w")

        self.bind_mousewheel(row)
        self.bind_mousewheel(content)
        self.bind_mousewheel(sender_label)
        self.bind_mousewheel(bubble)
        self.master.after(20, self.scroll_chat_to_bottom)

    def scroll_chat_to_bottom(self):
        self.update_chat_scroll_region()
        self.chat_canvas.yview_moveto(1.0)

    def track_order_gui(self):
        order_number = simpledialog.askstring("Track Order", "Please enter your order number:")
        if order_number:
            order_info = fetch_order_info(order_number)
            if order_info:
                message = (
                    f"Order Number: {order_info['order_number']}\n"
                    f"Status: {order_info['status']}\n"
                    f"Current Location: {order_info['current_location']}\n"
                    f"Destination Address: {order_info['customer_address']}\n"
                    f"Expected Delivery Date: {order_info['expected_delivery_date']}\n"
                    f"Product: {order_info.get('product_name') or 'N/A'}\n"
                    f"Quantity: {order_info.get('quantity') or 'N/A'}\n"
                    f"Total Price: {order_info.get('total_price') or 'N/A'}\n"
                )
                self.display_message(self.bot_name, message)
            else:
                self.display_message(self.bot_name, "Order not found.")
        else:
            self.display_message(self.bot_name, "Order number cannot be empty.")

    def update_address_gui(self):
        order_number = simpledialog.askstring(
            "Update Address",
            "Please enter your order number:",
        )
        email = simpledialog.askstring(
            "Update Address",
            "Please provide your email for verification:",
        )
        if order_number and email:
            if verify_customer_email(order_number, email):
                current_address = fetch_customer_address(email)
                new_address = simpledialog.askstring(
                    "Update Address",
                    f"Your current address is {current_address}. Please enter your new address:",
                )
                if new_address:
                    confirmation = simpledialog.askstring(
                        "Update Address",
                        (
                            f"You entered the following address: {new_address}. "
                            "Are you sure this is your new address? (yes/no):"
                        ),
                    )
                    if confirmation.lower() == "yes":
                        update_address(order_number, new_address)
                        self.display_message(self.bot_name, "Your address has been updated.")
                    else:
                        self.display_message(self.bot_name, "Address update cancelled.")
            else:
                self.display_message(self.bot_name, "Email verification failed.")
        else:
            self.display_message(self.bot_name, "Order number and email cannot be empty.")

    def show_products_gui(self):
        products = load_products()
        self.viewed_product_ids.update(product["product_id"] for product in products)
        self.display_message(
            self.bot_name,
            "Available products:\n" + format_product_list(products),
        )

    def show_recommendations_gui(self, user_input):
        self.display_message(
            self.bot_name,
            recommendation_message(
                user_input,
                self.viewed_product_ids,
                self.cart_product_ids,
            ),
        )

    def show_product_popularity_gui(self):
        self.display_message(
            self.bot_name,
            product_popularity_message(),
        )

    def show_market_basket_gui(self):
        self.display_message(
            self.bot_name,
            market_basket_message(),
        )

    def show_category_prediction_gui(self, user_input):
        self.display_message(
            self.bot_name,
            category_prediction_message(user_input),
        )

    def select_product_gui(self):
        products = load_products()
        if not products:
            self.display_message(self.bot_name, "No products are available right now.")
            return None

        self.viewed_product_ids.update(product["product_id"] for product in products)
        self.display_message(
            self.bot_name,
            "Available products:\n" + format_product_list(products),
        )
        product_id = simpledialog.askstring(
            "Create Order",
            "Enter the product ID for this order:",
        )
        product = get_product_by_id(product_id)
        if not product:
            self.display_message(self.bot_name, "Product not found.")
            return None
        self.viewed_product_ids.add(product["product_id"])
        return product

    def admin_login_gui(self):
        username = simpledialog.askstring("Admin Login", "Username:")
        password = simpledialog.askstring("Admin Login", "Password:", show="*")

        if not username or not password:
            self.display_message(self.bot_name, "Username and password are required.")
            return

        user = authenticate_user(username, password)
        if not user or user.get("role") != "admin":
            self.display_message(self.bot_name, "Admin login failed.")
            return

        self.current_user = user
        self.display_message(
            self.bot_name,
            f"Admin login successful. Welcome, {user.get('full_name') or username}.",
        )

    def admin_logout(self):
        if not self.current_user:
            self.display_message(self.bot_name, "No admin is logged in.")
            return
        self.current_user = None
        self.display_message(self.bot_name, "Admin logged out.")

    def update_order_status_gui(self):
        if not self.is_admin():
            self.display_message(
                self.bot_name,
                "Only an admin can update order status. Type 'admin login' first.",
            )
            return

        order_number = simpledialog.askstring(
            "Update Order Status",
            "Enter order number:",
        )
        status = simpledialog.askstring(
            "Update Order Status",
            "Enter new status (Processing, Shipped, Delivered, Cancelled):",
        )
        current_location = simpledialog.askstring(
            "Update Order Status",
            "Enter current location, or leave blank to keep existing:",
        )

        if not order_number or not status:
            self.display_message(self.bot_name, "Order number and status are required.")
            return

        if update_order_status(order_number, status, current_location or None):
            self.display_message(self.bot_name, "Order status updated successfully.")
        else:
            self.display_message(self.bot_name, "Order not found.")

    def create_order_gui(self, selected_product=None):
        product = selected_product or self.select_product_gui()
        if not product:
            return

        customer_name = simpledialog.askstring("Create Order", "Enter customer name:")
        customer_email = simpledialog.askstring("Create Order", "Enter customer email:")
        customer_address = simpledialog.askstring("Create Order", "Enter customer address:")
        quantity = simpledialog.askinteger(
            "Create Order",
            "Enter quantity:",
            minvalue=1,
            initialvalue=1,
        )
        expected_delivery_date = simpledialog.askstring(
            "Create Order",
            "Enter expected delivery date (dd/mm/yyyy) or leave blank:",
        )

        if (
            not customer_name
            or not customer_email
            or not customer_address
            or not quantity
        ):
            self.display_message(
                self.bot_name,
                "Customer name, email, address, and quantity are required.",
            )
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
                expected_delivery_date=expected_delivery_date,
                product_id=product["product_id"],
                product_name=product["name"],
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
            )
            if ok:
                self.cart_product_ids.append(product["product_id"])
                self.display_message(
                    self.bot_name,
                    (
                        f"{message}\n"
                        f"Product: {format_product(product)}\n"
                        f"Quantity: {quantity}\n"
                        f"Total: ${total_price:.2f}"
                    ),
                )
            else:
                self.display_message(self.bot_name, message)
        except Exception as e:
            self.display_message(self.bot_name, f"Failed to create order: {e}")

    def cancel_order_gui(self):
        order_number = simpledialog.askstring(
            "Cancel Order",
            "Please enter the order number to cancel:",
        )
        email = simpledialog.askstring(
            "Cancel Order",
            "Please provide your email for verification:",
        )

        if not order_number or not email:
            self.display_message(self.bot_name, "Order number and email are required.")
            return

        if not verify_customer_email(order_number, email):
            self.display_message(self.bot_name, "Email verification failed.")
            return

        confirmation = simpledialog.askstring(
            "Cancel Order",
            f"Are you sure you want to cancel order {order_number}? (yes/no):",
        )
        if not confirmation or confirmation.lower() != "yes":
            self.display_message(self.bot_name, "Order cancellation cancelled.")
            return

        if delete_order(order_number):
            self.display_message(
                self.bot_name,
                "Your order has been cancelled and deleted from the database.",
            )
        else:
            self.display_message(self.bot_name, "Order not found.")


if __name__ == "__main__":
    root = tk.Tk()
    chat_gui = ChatGUI(root)
    root.mainloop()
