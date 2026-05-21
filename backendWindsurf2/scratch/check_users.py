import asyncio
import os
import sys

# Add the current directory to sys.path
sys.path.append(os.getcwd())

# Import all models to avoid relationship errors
from models.user import User
from models.quiz import Quiz
from models.question import Question
from models.answer import Answer
from models.note import Note
from models.grading import GradingSession

from database import AsyncSessionLocal
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(select(User.email, User.hashed_password, User.is_oauth_user, User.full_name))
            users = result.all()
            print("--- Database Users ---")
            for email, hashed, is_oauth, name in users:
                print(f"Email: {email} | Name: {name} | OAuth: {is_oauth} | Password Set: {bool(hashed)}")
            print("----------------------")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
