"""
Database initialization and index creation script.
Run this after starting MongoDB to create necessary indexes.
"""
import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to MongoDB
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'scalemart')

client = MongoClient(mongo_url)
db = client[db_name]

print(f"🔗 Connected to MongoDB: {mongo_url}")
print(f"📊 Database: {db_name}")
print("\n🔧 Creating indexes...\n")

# Users collection indexes
print("👤 Users collection:")
db.users.create_index([("email", ASCENDING)], unique=True, name="email_unique_idx")
print("  ✅ Created unique index on 'email'")

# Orders collection indexes
print("\n📦 Orders collection:")
db.orders.create_index([("user_id", ASCENDING)], name="user_id_idx")
print("  ✅ Created index on 'user_id' (for order history queries)")

db.orders.create_index([("created_at", DESCENDING)], name="created_at_idx")
print("  ✅ Created index on 'created_at' (for time-based queries)")

db.orders.create_index([("status", ASCENDING), ("created_at", DESCENDING)], name="status_created_idx")
print("  ✅ Created compound index on 'status' + 'created_at' (for admin stats)")

db.orders.create_index([("product_id", ASCENDING)], name="product_id_idx")
print("  ✅ Created index on 'product_id' (for product analytics)")

# List all indexes
print("\n📋 All indexes created:")
print("\nUsers collection indexes:")
for index in db.users.list_indexes():
    print(f"  - {index['name']}: {index['key']}")

print("\nOrders collection indexes:")
for index in db.orders.list_indexes():
    print(f"  - {index['name']}: {index['key']}")

print("\n✅ Database initialization complete!")
client.close()
