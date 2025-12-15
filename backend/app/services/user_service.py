from app.core.database import db
from app.core.models import StudentProfile

async def get_profile(student_id: str) -> StudentProfile:
    # 1. Get the collection
    collection = db.get_db()["profiles"]
    
    # 2. Find the document
    data = await collection.find_one({"student_id": student_id})
    
    # 3. Convert MongoDB document back to Pydantic model
    if data:
        return StudentProfile(**data)
    return None

async def save_profile(profile: StudentProfile):
    collection = db.get_db()["profiles"]
    
    # 4. Upsert (Update if exists, Insert if new)
    await collection.update_one(
        {"student_id": profile.student_id},
        {"$set": profile.model_dump()}, # Convert Pydantic to Dict
        upsert=True
    )
    return True