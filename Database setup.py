import pymongo
from faker import Faker
import random

# Connection string
connection_string = "mongodb+srv://rahulverma:09Ph2007@ajfa02.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000&socketTimeoutMS=60000&connectTimeoutMS=60000&directConnection=false"
client = pymongo.MongoClient(connection_string)

# Set up the database
db = client['Ecommerce']

# Faker for generating fake data
fake = Faker()

# Create collections and documents
def create_products(n):
    products = []
    for _ in range(n):
        products.append({
            "name": fake.word().capitalize(),
            "description": fake.text(),
            "price": round(random.uniform(10, 1000), 2),
            "categories": [fake.word(), fake.word()],
            "stock": random.randint(0, 100),
            "ratings": {
                "average": round(random.uniform(1, 5), 2),
                "number_of_reviews": random.randint(1, 100)
            },
            "images": [fake.image_url() for _ in range(3)]
        })
    db.Products.insert_many(products)

def create_users(n):
    users = []
    for _ in range(n):
        users.append({
            "username": fake.user_name(),
            "password": fake.password(),
            "email": fake.email(),
            "address": {
                "street": fake.street_address(),
                "city": fake.city(),
                "state": fake.state(),
                "zip": fake.zipcode()
            },
            "order_history": [],
            "wishlist": []
        })
    db.Users.insert_many(users)

def create_orders(n, user_ids, product_ids):
    orders = []
    for _ in range(n):
        orders.append({
            "user_id": random.choice(user_ids),
            "items": [{"product_id": pid, "quantity": random.randint(1, 5), "price": db.Products.find_one({'_id': pid})['price']} for pid in random.sample(product_ids, 2)],
            "total_price": sum(item['price'] * item['quantity'] for item in orders[-1]['items']),
            "status": random.choice(['shipped', 'processing', 'cancelled']),
            "shipment_tracking": fake.uuid4(),
            "order_date": fake.date_time_this_year()
        })
    db.Orders.insert_many(orders)

def create_reviews(n, user_ids, product_ids):
    reviews = []
    for _ in range(n):
        reviews.append({
            "product_id": random.choice(product_ids),
            "user_id": random.choice(user_ids),
            "rating": random.randint(1, 5),
            "text": fake.text(),
            "date": fake.date_time_this_year()
        })
    db.Reviews.insert_many(reviews)

# Generate data
num_users = 50
num_products = 100
num_orders = 200
num_reviews = 300

# Create users and products first to get their IDs
create_users(num_users)
create_products(num_products)

# Fetch IDs
user_ids = [user['_id'] for user in db.Users.find({}, {'_id': 1})]
product_ids = [product['_id'] for product in db.Products.find({}, {'_id': 1})]

# Create orders and reviews using IDs
create_orders(num_orders, user_ids, product_ids)
create_reviews(num_reviews, user_ids, product_ids)

print("Database setup complete.")
