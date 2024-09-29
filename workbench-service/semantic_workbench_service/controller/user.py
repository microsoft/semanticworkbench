from typing import AsyncContextManager, Callable

from semantic_workbench_api_model import workbench_model
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .. import auth, db
from . import convert


async def add_or_update_user_from(
    session: AsyncSession,
    user_principal: auth.UserPrincipal,
) -> None:
    is_service_user = isinstance(user_principal, auth.ServiceUserPrincipal)
    inserted = await db.insert_if_not_exists(
        session, db.User(user_id=user_principal.user_id, name=user_principal.name, service_user=is_service_user)
    )
    if inserted:
        return await session.commit()

    user = (
        await session.exec(select(db.User).where(db.User.user_id == user_principal.user_id).with_for_update())
    ).one()
    user.name = user_principal.name
    user.service_user = isinstance(user_principal, auth.ServiceUserPrincipal)
    session.add(user)
    await session.commit()


class UserController:
    def __init__(
        self,
        get_session: Callable[[], AsyncContextManager[AsyncSession]],
    ) -> None:
        self._get_session = get_session

    async def update_user(
        self,
        user_principal: auth.UserPrincipal,
        user_id: str,
        update_user: workbench_model.UpdateUser,
    ) -> workbench_model.User:
        async with self._get_session() as session:
            inserted = await db.insert_if_not_exists(
                session, db.User(user_id=user_id, name=update_user.name or user_principal.name, image=update_user.image)
            )

            user = (await session.exec(select(db.User).where(db.User.user_id == user_id).with_for_update())).one()
            if not inserted:
                updates = update_user.model_dump(exclude_unset=True)
                for field, value in updates.items():
                    setattr(user, field, value)

                session.add(user)

            await session.commit()

        return convert.user_from_db(model=user)

    async def get_users(self, user_ids: list[str]) -> workbench_model.UserList:
        async with self._get_session() as session:
            users = (await session.exec(select(db.User).where(col(db.User.user_id).in_(user_ids)))).all()

        return convert.user_list_from_db(models=users)

    async def get_user_me(self, user_principal: auth.UserPrincipal) -> workbench_model.User:
        async with self._get_session() as session:
            await add_or_update_user_from(session, user_principal=user_principal)
            user = (await session.exec(select(db.User).where(db.User.user_id == user_principal.user_id))).one()

        return convert.user_from_db(model=user)
