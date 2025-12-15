import os
from motor.motor_asyncio import AsyncIOMotorClient

# Connection Settings
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = "agented_db" 

class Database:
    client: AsyncIOMotorClient = None

    def connect(self):
        self.client = AsyncIOMotorClient(MONGO_URL)
        print("✅ Connected to MongoDB")

    def close(self):
        if self.client:
            self.client.close()
            print("❌ Closed MongoDB connection")


    def get_db(self):
        return self.client[DB_NAME]

# Create the instance
db = Database()