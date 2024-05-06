from locust import HttpUser, task, between, events
import random
import pymongo

# Constants
DATABASE_NAME = 'Ecommerce'
PRODUCT_COLLECTION = 'Products'
USER_COLLECTION = 'Users'
ORDER_COLLECTION = 'Orders'
CART_COLLECTION = 'Carts'

# Database setup
client = pymongo.MongoClient("mongodb_connection_string")  # Replace with your MongoDB connection string
db = client[DATABASE_NAME]

# Helper functions
def get_random_products(n):
    products = list(db[PRODUCT_COLLECTION].aggregate([{"$sample": {"size": n}}]))
    return products

def get_random_user():
    user = db[USER_COLLECTION].aggregate([{"$sample": {"size": 1}}]).next()
    return user

class EcommerceUser(HttpUser):
    wait_time = between(1, 3)  # Users wait 1 to 3 seconds between tasks

    @task(10)
    def view_products(self):
        products = get_random_products(random.randint(10, 20))
        for product in products:
            self.client.get(f"/product/{product['_id']}", name="View Product")

    @task(5)
    def add_to_cart(self):
        user = get_random_user()
        products = get_random_products(5)
        for product in products:
            self.client.post("/cart/add", json={
                "user_id": user['_id'],
                "product_id": product['_id'],
                "quantity": 1
            }, name="Add to Cart")

    @task(1)
    def place_order(self):
        user = get_random_user()
        products = get_random_products(2)
        items = [{"product_id": product['_id'], "quantity": random.randint(1, 3)} for product in products]
        self.client.post("/order/create", json={
            "user_id": user['_id'],
            "items": items
        }, name="Place Order")

    @task(1)
    def update_account_details(self):
        user = get_random_user()
        new_email = f"{random.randint(1000, 9999)}_{user['email']}"
        self.client.patch("/user/update", json={
            "user_id": user['_id'],
            "new_email": new_email
        }, name="Update Account Details")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("Starting test, setting up database indices and preparing initial data.")
    db[PRODUCT_COLLECTION].create_index([("price", pymongo.ASCENDING)])
    db[USER_COLLECTION].create_index([("email", pymongo.DESCENDING)])

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("Test completed, cleaning up any temporary data or states if necessary.")

if __name__ == "__main__":
    import os
    os.system("locust -f this_script_name.py")  # Replace `this_script_name.py` with the actual name of this script
