import asyncio
from app.core.database import db
from app.core.models import StudentProfile
from app.services.user_service import save_profile, get_profile

async def main():
    print("🔄 Connecting to Database...")
    # 1. Manually trigger the connection
    db.connect()

    # 2. Define a dummy user
    test_user_id = "student_001"
    dummy_profile = StudentProfile(
        student_id=test_user_id,
        weak_topics=["Photosynthesis", "Cellular Respiration"],
        mastered_topics=["Mitosis"]
    )

    # 3. Save the user to MongoDB
    print(f"💾 Saving profile for {test_user_id}...")
    await save_profile(dummy_profile)
    print("✅ Save successful!")

    # 4. Read the user back to confirm
    print(f"🔎 Reading back profile for {test_user_id}...")
    fetched_profile = await get_profile(test_user_id)
    
    if fetched_profile:
        print(f"🎉 Success! Found user in DB:")
        print(f"   - Weak Topics: {fetched_profile.weak_topics}")
        print(f"   - Mastered: {fetched_profile.mastered_topics}")
    else:
        print("❌ Error: Could not find the user we just saved.")

    # 5. Close connection
    db.close()

if __name__ == "__main__":
    asyncio.run(main())