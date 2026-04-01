import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

SEED_USERS = [
    {"email": "admin@niyog.dev", "name": "Admin", "role": UserRole.admin, "password": "admin123"},
    {"email": "hr@niyog.dev", "name": "HR Manager", "role": UserRole.hr, "password": "hr123"},
    {"email": "candidate@niyog.dev", "name": "Test Candidate", "role": UserRole.candidate, "password": "cand123"},
    {"email": "company@niyog.dev", "name": "Acme Corp", "role": UserRole.company, "password": "comp123"},
]


async def seed_users(db: AsyncSession) -> None:
    for user_data in SEED_USERS:
        result = await db.execute(select(User).where(User.email == user_data["email"]))
        if result.scalar_one_or_none() is None:
            user = User(
                email=user_data["email"],
                name=user_data["name"],
                role=user_data["role"],
                password_hash=hash_password(user_data["password"]),
            )
            db.add(user)
    await db.commit()
