from pymongo import MongoClient

# Connect to MongoDB (default port 27017)
client = MongoClient("mongodb://localhost:27017/")

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
