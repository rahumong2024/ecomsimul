from locust import User, task, between, events
import pymongo
import random

# Connection string and database setup
CONNECTION_STRING = "mongodb+srv://rahulverma:09Ph2007@ajfa02.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000"
client = pymongo.MongoClient(CONNECTION_STRING)
db = client['Ecommerce']

# Helper functions
def get_random_product_id():
    product = db.Products.aggregate([{"$sample": {"size": 1}}]).next()
    return product['_id']

def get_random_user_id():
    user = db.Users.aggregate([{"$sample": {"size": 1}}]).next()
    return user['_id']

class MongoUser(User):
    wait_time = between(1, 3)  # Users wait 1 to 3 seconds between tasks

    @task(10)
    def view_products(self):
        # Simulate viewing 10 to 20 products by performing read operations
        for _ in range(random.randint(10, 20)):
            product_id = get_random_product_id()
            db.Products.find_one({'_id': product_id})

    @task(5)
    def add_to_cart(self):
        # Simulate adding items to the cart 5 times per session
        user_id = get_random_user_id()
        for _ in range(5):
            product_id = get_random_product_id()
            db.Carts.update_one({'user_id': user_id}, {'$addToSet': {'items': {'product_id': product_id, 'quantity': 1}}}, upsert=True)

    @task(1)
    def place_order(self):
        # Simulate placing an order
        user_id = get_random_user_id()
        items = [{'product_id': get_random_product_id(), 'quantity': random.randint(1, 3)} for _ in range(2)]
        db.Orders.insert_one({
            'user_id': user_id,
            'items': items,
            'order_date': '2024-04-25'
        })

    @task(1)
    def update_account_details(self):
        # Simulate user updating their account details
        user_id = get_random_user_id()
        new_email = f'user{random.randint(1000, 9999)}@example.com'
        db.Users.update_one({'_id': user_id}, {'$set': {'email': new_email}})

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("Starting test, preparing the environment.")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("Test completed, cleaning up the environment.")

if __name__ == "__main__":
    # Importing necessary modules for running the Locust web UI
    from locust import web
    from locust.env import Environment
    from locust.stats import stats_printer, stats_history
    import gevent

    # Set up Environment and Runner
    env = Environment(user_classes=[MongoUser])
    env.create_local_runner()

    # Start the web interface
    web_ui = web.WebUI(env, host="0.0.0.0", port=8011)

    # Start a greenlet that periodically outputs the current stats
    gevent.spawn(stats_printer(env.stats))

    # Start a greenlet that saves current stats to history
    gevent.spawn(stats_history, env.runner)

    # Start the test
    env.runner.start(user_count=1000, spawn_rate=10)  # Specify number of users and spawn rate
    gevent.spawn_later(60, lambda: env.runner.quit())  # Stop after 60 seconds

    # Wait for the greenlets
    env.runner.greenlet.join()

    # Start the web UI
    web_ui.start()
