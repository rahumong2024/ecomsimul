#!/usr/bin/env python

import gevent
gevent.monkey.patch_all()

import pymongo
from locust import User, task, between
import random
import time

# Global variables for database client and server details
_CLIENT = None
_SRV = None
_EXISTING_PRODUCT_IDS = []
_EXISTING_CUSTOMER_IDS = []

class EcommerceUser(User):
    wait_time = between(1, 5)  # Simulating realistic user interactions

    def on_start(self):
        """Initialize MongoDB client on start and fetch initial data."""
        global _CLIENT, _SRV, _EXISTING_PRODUCT_IDS, _EXISTING_CUSTOMER_IDS

        try:
            parts = self.host.split("|")
            srv, db_name = parts[0], parts[1]

            if _SRV != srv:
                self.client = pymongo.MongoClient(srv, serverSelectionTimeoutMS=5000)
                _CLIENT = self.client
                _SRV = srv
            else:
                self.client = _CLIENT

            db = self.client[db_name]
            self.coll_products = db['Products']
            self.coll_users = db['Users']
            self.coll_orders = db['Orders']

            _EXISTING_PRODUCT_IDS = [doc['_id'] for doc in self.coll_products.find({}, {'_id': 1}).limit(100)]
            _EXISTING_CUSTOMER_IDS = [doc['_id'] for doc in self.coll_users.find({}, {'_id': 1}).limit(100)]

        except Exception as e:
            self.environment.events.request.fire(request_type="Host Init Failure", name=str(e), response_time=0, response_length=0, exception=e)

    def get_time(self):
        """Get the current time for measuring execution time."""
        return time.time()

    @task(40)
    def browse_products(self):
        """Simulate browsing through product listings."""
        tic = self.get_time()
        for _ in range(random.randint(5, 15)):
            product_id = random.choice(_EXISTING_PRODUCT_IDS)
            self.coll_products.find_one({"_id": product_id}, {"name": 1, "price": 1, "description": 1, "categories": 1})
        self.environment.events.request.fire(request_type="Read", name="BrowseProducts", response_time=(self.get_time() - tic) * 1000, response_length=1)

    @task(10)
    def search_products(self):
        """Simulate searching for products with keywords."""
        tic = self.get_time()
        keywords = ["electronics", "shoes", "home decor", "gadgets", "kitchen", "fashion"]
        search_query = random.choice(keywords)
        self.coll_products.find({"$text": {"$search": search_query}})
        self.environment.events.request.fire(request_type="Search", name="SearchProducts", response_time=(self.get_time() - tic) * 1000, response_length=1)

    @task(20)
    def add_items_to_cart(self):
        """Simulate adding items to the cart."""
        tic = self.get_time()
        customer_id = random.choice(_EXISTING_CUSTOMER_IDS)
        product_id = random.choice(_EXISTING_PRODUCT_IDS)
        quantity = random.randint(1, 3)
        self.coll_users.update_one(
            {"_id": customer_id}, 
            {"$push": {"cart": {"product_id": product_id, "quantity": quantity}}}, 
            upsert=True
        )
        self.environment.events.request.fire(request_type="Update", name="AddItemsToCart", response_time=(self.get_time() - tic) * 1000, response_length=1)

    @task(15)
    def view_cart(self):
        """Simulate viewing the cart before checkout."""
        tic = self.get_time()
        customer_id = random.choice(_EXISTING_CUSTOMER_IDS)
        self.coll_users.find_one({"_id": customer_id}, {"cart": 1})
        self.environment.events.request.fire(request_type="Read", name="ViewCart", response_time=(self.get_time() - tic) * 1000, response_length=1)

    @task(8)
    def place_order(self):
        """Simulate the order placement process."""
        tic = self.get_time()
        customer_id = random.choice(_EXISTING_CUSTOMER_IDS)
        user_cart = self.coll_users.find_one({"_id": customer_id}, {"cart": 1})

        if not user_cart or "cart" not in user_cart:
            return  # If no cart exists, skip this task

        total_price = 0
        items = []
        for item in user_cart['cart']:
            product = self.coll_products.find_one({"_id": item['product_id']})
            price = product['price']
            total_price += price * item['quantity']
            items.append({
                "product_id": item['product_id'],
                "quantity": item['quantity'],
                "price": price,
                "name": product['name']
            })

        order = {
            "user_id": customer_id,
            "items": items,
            "total_price": total_price,
            "order_status": "pending",
            "order_date": time.strftime("%Y-%m-%d")
        }
        self.coll_orders.insert_one(order)

        self.coll_users.update_one({"_id": customer_id}, {"$unset": {"cart": ""}})
        self.environment.events.request.fire(request_type="Insert", name="PlaceOrder", response_time=(self.get_time() - tic) * 1000, response_length=1)

    @task(4)
    def update_account_info(self):
        """Simulate updating account information like email or password."""
        tic = self.get_time()
        customer_id = random.choice(_EXISTING_CUSTOMER_IDS)
        new_email = f"customer{random.randint(1000, 9999)}@example.com"
        new_password = f"newpassword{random.randint(1000, 9999)}"
        self.coll_users.update_one({"_id": customer_id}, {"$set": {"email": new_email, "password": new_password}})
        self.environment.events.request.fire(request_type="Update", name="UpdateAccountInfo", response_time=(self.get_time() - tic) * 1000, response_length=1)

    @task(3)
    def leave_review(self):
        """Simulate leaving a review for a purchased product."""
        tic = self.get_time()
        customer_id = random.choice(_EXISTING_CUSTOMER_IDS)
        product_id = random.choice(_EXISTING_PRODUCT_IDS)
        rating = random.randint(1, 5)
        review = {
            "user_id": customer_id,
            "product_id": product_id,
            "rating": rating,
            "comment": f"This product was {['terrible', 'bad', 'okay', 'good', 'excellent'][rating - 1]}!",
            "review_date": time.strftime("%Y-%m-%d")
        }
        self.coll_products.update_one({"_id": product_id}, {"$push": {"reviews": review}}, upsert=True)
        self.environment.events.request.fire(request_type="Update", name="LeaveReview", response_time=(self.get_time() - tic) * 1000, response_length=1)

    @task(3)
    def perform_analytics(self):
        """Simulate product recommendation analytics."""
        tic = self.get_time()
        customer_id = random.choice(_EXISTING_CUSTOMER_IDS)
        result = self.coll_orders.aggregate([
            {"$match": {"user_id": customer_id}},
            {"$unwind": "$items"},
            {"$group": {
                "_id": "$user_id",
                "top_categories": {"$addToSet": "$items.name"}
            }},
            {"$sort": {"top_categories": 1}},
            {"$limit": 5}
        ])
        list(result)
        self.environment.events.request.fire(request_type="Aggregation", name="PerformAnalytics", response_time=(self.get_time() - tic) * 1000, response_length=1)
