from analytics import (
    format_market_basket_analysis,
    format_product_popularity,
    market_basket_analysis,
    product_popularity,
)
from category_predictor import format_category_prediction, predict_category
from product_catalog import format_recommendation_list, recommend_products


def recommendation_message(user_input, viewed_product_ids=None, cart_product_ids=None):
    recommendations = recommend_products(
        query=user_input,
        viewed_product_ids=viewed_product_ids,
        cart_product_ids=cart_product_ids,
    )
    return format_recommendation_list(recommendations)


def product_popularity_message():
    return format_product_popularity(product_popularity())


def market_basket_message():
    return format_market_basket_analysis(market_basket_analysis())


def category_prediction_message(user_input):
    return format_category_prediction(predict_category(user_input))
