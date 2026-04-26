from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


async def get_or_create_user_by_telegram(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    full_name: str | None,
) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
        )
        session.add(user)
        await session.flush()
    else:
        user.username = username
        if (not user.full_name) and full_name:
            user.full_name = full_name
    return user
