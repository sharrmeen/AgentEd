import os

from pymongo import MongoClient

# Connect to MongoDB (supports Atlas URI via env)
mongo_uri = os.getenv("MONGODB_URI")
if not mongo_uri:
	raise RuntimeError("MONGODB_URI is required")
client = MongoClient(mongo_uri)

# Create or switch to a test database
db = client["test_database"]

# Create or switch to a collection
collection = db["test_collection"]

# Insert a test document
test_doc = {"name": "Test User", "email": "test@example.com"}
insert_result = collection.insert_one(test_doc)

print(f"Inserted document with ID: {insert_result.inserted_id}")

# Retrieve and print the document
retrieved_doc = collection.find_one({"name": "Test User"})
print("Retrieved document:", retrieved_doc)

# Close the connection
client.close()
