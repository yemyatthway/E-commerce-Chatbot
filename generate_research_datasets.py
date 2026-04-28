import csv
import random
from datetime import date, timedelta


random.seed(108)


PRODUCTS = [
    ("P001", "Classic Red Mug", "Coffee Mug", "Red", "350ml", "Ceramic", 12.99, 48, "Durable everyday ceramic mug in red"),
    ("P002", "Classic White Mug", "Coffee Mug", "White", "350ml", "Ceramic", 11.99, 62, "Minimal white ceramic mug for coffee or tea"),
    ("P003", "Classic Blue Mug", "Coffee Mug", "Blue", "350ml", "Ceramic", 12.99, 55, "Blue ceramic mug with dishwasher-safe finish"),
    ("P004", "Large Travel Mug", "Travel Mug", "Black", "500ml", "Stainless Steel", 18.99, 35, "Insulated travel mug for hot drinks"),
    ("P005", "Gift Mug Set", "Gift Set", "Mixed", "3 x 350ml", "Ceramic", 34.99, 28, "Three-piece mug gift set with red white and blue mugs"),
    ("P006", "Matte Black Mug", "Coffee Mug", "Black", "400ml", "Ceramic", 14.99, 41, "Modern matte ceramic mug for coffee and tea"),
    ("P007", "Pastel Pink Mug", "Coffee Mug", "Pink", "300ml", "Ceramic", 13.49, 34, "Small pastel ceramic mug with smooth finish"),
    ("P008", "Office Grey Mug", "Coffee Mug", "Grey", "350ml", "Ceramic", 10.99, 57, "Neutral office mug for daily use"),
    ("P009", "Glass Latte Mug", "Latte Mug", "Clear", "450ml", "Glass", 15.99, 27, "Clear glass mug for latte and layered coffee"),
    ("P010", "Espresso Cup Pair", "Espresso Cup", "White", "2 x 90ml", "Porcelain", 16.99, 30, "Pair of porcelain espresso cups"),
    ("P011", "Thermal Steel Mug", "Travel Mug", "Silver", "480ml", "Stainless Steel", 19.99, 32, "Thermal steel mug with spill-resistant lid"),
    ("P012", "Commuter Mug", "Travel Mug", "Navy", "520ml", "Stainless Steel", 21.99, 26, "Large commuter mug for hot drinks on the go"),
    ("P013", "Eco Bamboo Mug", "Eco Mug", "Beige", "400ml", "Bamboo Fiber", 17.49, 24, "Reusable bamboo fiber mug with eco-friendly material"),
    ("P014", "Reusable Glass Cup", "Eco Mug", "Clear", "360ml", "Glass", 14.49, 38, "Reusable glass cup for hot and cold drinks"),
    ("P015", "Holiday Gift Mug Set", "Gift Set", "Mixed", "4 x 300ml", "Ceramic", 39.99, 18, "Seasonal gift set with four decorated mugs"),
    ("P016", "Minimal Cream Mug", "Coffee Mug", "Cream", "350ml", "Ceramic", 12.49, 44, "Simple cream ceramic mug for home use"),
    ("P017", "Forest Green Mug", "Coffee Mug", "Green", "380ml", "Ceramic", 13.99, 36, "Green ceramic mug inspired by outdoor colors"),
    ("P018", "Speckled Stone Mug", "Coffee Mug", "Stone", "400ml", "Stoneware", 15.49, 29, "Speckled stoneware mug with handmade style finish"),
    ("P019", "Copper Travel Tumbler", "Travel Mug", "Copper", "500ml", "Stainless Steel", 22.49, 21, "Metallic insulated tumbler for commuting"),
    ("P020", "Kids Small Mug", "Coffee Mug", "Yellow", "250ml", "Ceramic", 9.99, 40, "Small bright mug suitable for children"),
    ("P021", "Double Wall Glass Mug", "Latte Mug", "Clear", "320ml", "Glass", 18.49, 25, "Double wall glass mug that keeps drinks warm"),
    ("P022", "Corporate Logo Mug", "Custom Mug", "White", "350ml", "Ceramic", 13.99, 50, "White ceramic mug suitable for custom logo printing"),
    ("P023", "Photo Print Mug", "Custom Mug", "White", "350ml", "Ceramic", 15.99, 46, "Personalized mug for photo printing"),
    ("P024", "Name Engraved Mug", "Custom Mug", "Black", "400ml", "Ceramic", 16.49, 31, "Custom mug with name engraving option"),
    ("P025", "Premium Porcelain Mug", "Coffee Mug", "White", "360ml", "Porcelain", 18.99, 33, "Premium porcelain mug for formal settings"),
    ("P026", "Stackable Espresso Set", "Espresso Cup", "Mixed", "6 x 80ml", "Porcelain", 29.99, 19, "Stackable espresso cups for kitchen storage"),
    ("P027", "Camping Enamel Mug", "Outdoor Mug", "Blue", "420ml", "Enamel", 12.49, 37, "Lightweight enamel mug for camping"),
    ("P028", "Mountain Enamel Mug", "Outdoor Mug", "Green", "420ml", "Enamel", 12.99, 35, "Outdoor enamel mug with mountain design"),
    ("P029", "Smart Temperature Mug", "Smart Mug", "Black", "400ml", "Stainless Steel", 54.99, 12, "Smart mug with temperature control"),
    ("P030", "Heated Desk Mug", "Smart Mug", "Grey", "380ml", "Stainless Steel", 49.99, 14, "Desk mug with heating base compatibility"),
    ("P031", "Floral Gift Mug", "Gift Set", "Pink", "350ml", "Ceramic", 19.99, 23, "Gift-ready floral ceramic mug"),
    ("P032", "Birthday Mug Box", "Gift Set", "Mixed", "2 x 350ml", "Ceramic", 27.99, 20, "Birthday themed mug gift box"),
    ("P033", "Large Soup Mug", "Soup Mug", "Red", "600ml", "Ceramic", 16.99, 26, "Large handled mug suitable for soup"),
    ("P034", "Breakfast Bowl Mug", "Soup Mug", "White", "650ml", "Ceramic", 17.49, 24, "Wide mug for breakfast or soup"),
    ("P035", "Reusable Coffee Cup", "Eco Mug", "Green", "360ml", "Recycled Plastic", 11.99, 52, "Lightweight reusable coffee cup"),
    ("P036", "Cork Grip Eco Cup", "Eco Mug", "Brown", "380ml", "Bamboo Fiber", 16.49, 30, "Eco cup with cork grip sleeve"),
    ("P037", "Luxury Gold Mug", "Coffee Mug", "Gold", "330ml", "Porcelain", 24.99, 16, "Gold accented porcelain mug"),
    ("P038", "Marble Ceramic Mug", "Coffee Mug", "White", "380ml", "Ceramic", 17.99, 28, "Marble pattern ceramic mug"),
    ("P039", "Tall Latte Glass", "Latte Mug", "Clear", "500ml", "Glass", 16.99, 29, "Tall glass mug for latte and iced coffee"),
    ("P040", "Reusable Straw Cup", "Eco Mug", "Clear", "600ml", "Glass", 18.49, 22, "Glass cup with reusable straw and lid"),
    ("P041", "Mini Espresso Cup", "Espresso Cup", "Black", "70ml", "Porcelain", 8.99, 43, "Small black espresso cup"),
    ("P042", "Color Espresso Set", "Espresso Cup", "Mixed", "4 x 90ml", "Porcelain", 24.49, 21, "Colorful espresso cup set"),
    ("P043", "Slim Travel Cup", "Travel Mug", "White", "450ml", "Stainless Steel", 20.49, 27, "Slim insulated travel cup"),
    ("P044", "Grip Travel Mug", "Travel Mug", "Red", "520ml", "Stainless Steel", 23.99, 18, "Large travel mug with grip texture"),
    ("P045", "Student Budget Mug", "Coffee Mug", "Blue", "320ml", "Ceramic", 7.99, 70, "Affordable ceramic mug for students"),
    ("P046", "Teacher Gift Mug", "Gift Set", "White", "350ml", "Ceramic", 18.99, 26, "Gift mug for teachers with message print"),
    ("P047", "Office Starter Pack", "Gift Set", "Mixed", "6 x 350ml", "Ceramic", 59.99, 11, "Bulk office mug starter pack"),
    ("P048", "Cafe Style Cappuccino Cup", "Latte Mug", "White", "280ml", "Porcelain", 13.99, 34, "Cafe style cup for cappuccino"),
    ("P049", "Insulated Camping Mug", "Outdoor Mug", "Black", "450ml", "Stainless Steel", 17.49, 25, "Insulated outdoor mug for camping"),
    ("P050", "Adventure Enamel Set", "Outdoor Mug", "Mixed", "4 x 420ml", "Enamel", 36.99, 17, "Outdoor enamel mug set for groups"),
    ("P051", "Ceramic Tea Mug", "Tea Mug", "Green", "450ml", "Ceramic", 14.99, 32, "Large ceramic mug for tea"),
    ("P052", "Infuser Tea Mug", "Tea Mug", "White", "420ml", "Ceramic", 19.49, 20, "Tea mug with removable infuser"),
    ("P053", "Glass Tea Cup", "Tea Mug", "Clear", "350ml", "Glass", 13.49, 36, "Clear glass cup for tea"),
    ("P054", "Personalized Couple Mug Set", "Custom Mug", "Mixed", "2 x 350ml", "Ceramic", 31.99, 18, "Personalized couple mug set"),
    ("P055", "Photo Travel Mug", "Custom Mug", "Silver", "470ml", "Stainless Steel", 27.99, 15, "Travel mug with photo customization"),
    ("P056", "Smart App Mug", "Smart Mug", "Silver", "410ml", "Stainless Steel", 64.99, 10, "Smart mug controlled by mobile app"),
    ("P057", "Minimal Black Espresso Pair", "Espresso Cup", "Black", "2 x 90ml", "Porcelain", 18.49, 24, "Pair of minimalist black espresso cups"),
    ("P058", "Rustic Stoneware Mug", "Coffee Mug", "Brown", "420ml", "Stoneware", 16.99, 27, "Rustic stoneware mug with warm finish"),
    ("P059", "Large Office Mug", "Coffee Mug", "Navy", "500ml", "Ceramic", 15.99, 39, "Large ceramic mug for long work sessions"),
    ("P060", "Compact Travel Cup", "Travel Mug", "Grey", "350ml", "Stainless Steel", 16.49, 33, "Compact travel cup for small bags"),
]


CITY_ROUTE = [
    "Shanghai",
    "Beijing",
    "Guangzhou",
    "Shenzhen",
    "Hangzhou",
    "Chengdu",
    "Wuhan",
    "Mandalay",
]


def write_products():
    with open("products.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "product_id",
            "name",
            "category",
            "color",
            "size",
            "material",
            "price",
            "stock",
            "description",
        ])
        writer.writerows(PRODUCTS)


def product_weights():
    weights = {}
    for product_id, name, category, *_ in PRODUCTS:
        base = {
            "Coffee Mug": 10,
            "Travel Mug": 7,
            "Gift Set": 5,
            "Eco Mug": 5,
            "Latte Mug": 4,
            "Espresso Cup": 4,
            "Custom Mug": 4,
            "Outdoor Mug": 3,
            "Tea Mug": 3,
            "Smart Mug": 2,
            "Soup Mug": 2,
        }.get(category, 2)
        if product_id in {"P001", "P002", "P003", "P004", "P005"}:
            base += 8
        weights[product_id] = base
    return weights


def choose_product(category_preference=None):
    product_by_id = {row[0]: row for row in PRODUCTS}
    weights = product_weights()
    if category_preference:
        for product in PRODUCTS:
            if product[2] == category_preference:
                weights[product[0]] += 8
    product_ids = list(weights)
    selected = random.choices(product_ids, weights=[weights[pid] for pid in product_ids], k=1)[0]
    return product_by_id[selected]


def write_orders():
    customers = [
        (f"U{index:03d}", f"Customer {index}", f"customer{index:03d}@example.com")
        for index in range(1, 81)
    ]
    category_preferences = [
        "Coffee Mug",
        "Travel Mug",
        "Gift Set",
        "Eco Mug",
        "Latte Mug",
        "Espresso Cup",
        "Custom Mug",
        "Outdoor Mug",
        "Tea Mug",
        "Smart Mug",
    ]
    product_by_id = {row[0]: row for row in PRODUCTS}
    start_date = date(2026, 1, 10)
    statuses = ["Delivered", "Shipped", "Processing", "Pending", "Cancelled"]
    status_weights = [45, 24, 17, 10, 4]
    order_rows = []
    order_number = 1

    for customer_index, (user_id, name, email) in enumerate(customers):
        preference = category_preferences[customer_index % len(category_preferences)]
        order_count = random.randint(2, 6)
        for _ in range(order_count):
            basket_size = random.choices([1, 2, 3, 4], weights=[35, 40, 18, 7], k=1)[0]
            basket = []
            if random.random() < 0.18:
                basket = [product_by_id["P001"], product_by_id["P002"], product_by_id["P003"]]
            elif random.random() < 0.15:
                basket = [product_by_id["P004"], product_by_id["P011"]]
            elif random.random() < 0.12:
                basket = [product_by_id["P005"], product_by_id["P031"]]
            while len(basket) < basket_size:
                product = choose_product(preference)
                if product not in basket:
                    basket.append(product)

            status = random.choices(statuses, weights=status_weights, k=1)[0]
            current_location = random.choice(CITY_ROUTE)
            address = random.choice(CITY_ROUTE)
            expected_date = start_date + timedelta(days=random.randint(2, 90))
            if status == "Cancelled":
                expected_delivery = "N/A"
            else:
                expected_delivery = expected_date.strftime("%d/%m/%Y")

            for product in basket:
                product_id, product_name, _, _, _, _, price, *_ = product
                quantity = random.choices([1, 2, 3, 4], weights=[55, 28, 12, 5], k=1)[0]
                total = round(price * quantity, 2)
                order_rows.append([
                    f"O_N{order_number:03d}",
                    status,
                    current_location,
                    expected_delivery,
                    address,
                    name,
                    email,
                    product_id,
                    product_name,
                    quantity,
                    f"{price:.2f}",
                    f"{total:.2f}",
                ])
                order_number += 1

    with open("orders.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "order_number",
            "status",
            "current_location",
            "expected_delivery_date",
            "customer_address",
            "customer_name",
            "customer_email",
            "product_id",
            "product_name",
            "quantity",
            "unit_price",
            "total_price",
        ])
        writer.writerows(order_rows)


def write_user_interactions():
    product_ids = [row[0] for row in PRODUCTS]
    rows = []
    start = date(2026, 1, 1)
    actions = ["view", "cart", "purchase", "review"]
    action_weights = [48, 22, 22, 8]
    for index in range(1, 701):
        user_id = f"U{random.randint(1, 80):03d}"
        product_id = random.choice(product_ids)
        action = random.choices(actions, weights=action_weights, k=1)[0]
        rating = ""
        if action in {"purchase", "review"}:
            rating = random.choices([3, 4, 5], weights=[14, 38, 48], k=1)[0]
        timestamp = start + timedelta(days=random.randint(0, 115))
        rows.append([user_id, product_id, action, rating, timestamp.isoformat()])

    with open("user_interactions.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["user_id", "product_id", "action", "rating", "timestamp"])
        writer.writerows(rows)


def write_survey():
    comments = [
        "Responses were clear and recommendations were useful",
        "Product suggestions were relevant",
        "Analytics answers were easy to understand",
        "Order and product features worked well",
        "Recommendation feature could include more products",
        "The chatbot was fast and easy to use",
        "Market basket results helped explain related products",
        "The product category prediction was understandable",
    ]
    with open("evaluation_survey.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "respondent_id",
            "chatbot_accuracy",
            "rating_recommendations",
            "rating_speed",
            "rating_overall",
            "comments",
        ])
        for index in range(1, 31):
            writer.writerow([
                f"S{index:03d}",
                random.choices([3, 4, 5], weights=[8, 44, 48], k=1)[0],
                random.choices([3, 4, 5], weights=[12, 46, 42], k=1)[0],
                random.choices([3, 4, 5], weights=[5, 35, 60], k=1)[0],
                random.choices([3, 4, 5], weights=[8, 42, 50], k=1)[0],
                random.choice(comments),
            ])


if __name__ == "__main__":
    write_products()
    write_orders()
    write_user_interactions()
    write_survey()
    print("Generated products.csv, orders.csv, user_interactions.csv, and evaluation_survey.csv")
