import logging
import uuid
from typing import AsyncContextManager, Awaitable, Callable

from semantic_workbench_api_model.workbench_model import (
    ConversationShare,
    ConversationShareList,
    ConversationShareRedemption,
    ConversationShareRedemptionList,
    NewConversationShare,
)
from sqlmodel import and_, col, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .. import auth, db, query
from ..event import ConversationEventQueueItem
from . import convert, exceptions
from . import user as user_

logger = logging.getLogger(__name__)


class ConversationShareController:
    def __init__(
        self,
        get_session: Callable[[], AsyncContextManager[AsyncSession]],
        notify_event: Callable[[ConversationEventQueueItem], Awaitable],
    ) -> None:
        self._get_session = get_session
        self._notify_event = notify_event

    async def create_conversation_share(
        self,
        new_conversation_share: NewConversationShare,
        user_principal: auth.UserPrincipal,
    ) -> ConversationShare:
        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    query.select_conversations_for(principal=user_principal, include_all_owned=True).where(
                        db.Conversation.conversation_id == new_conversation_share.conversation_id
                    )
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.InvalidArgumentError("Conversation not found")

            conversation_share = db.ConversationShare(
                conversation_id=new_conversation_share.conversation_id,
                owner_id=user_principal.user_id,
                label=new_conversation_share.label,
                conversation_permission=new_conversation_share.conversation_permission,
                meta_data=new_conversation_share.metadata,
            )

            session.add(conversation_share)
            await session.commit()

            await session.refresh(conversation_share)

        return convert.conversation_share_from_db(conversation_share)

    async def create_conversation_share_with_owner(
        self,
        new_conversation_share: NewConversationShare,
        owner_id: str,
    ) -> ConversationShare:
        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    select(db.Conversation).where(
                        db.Conversation.conversation_id == new_conversation_share.conversation_id
                    )
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.InvalidArgumentError("Conversation not found")

            conversation_share = db.ConversationShare(
                conversation_id=new_conversation_share.conversation_id,
                owner_id=owner_id,
                label=new_conversation_share.label,
                conversation_permission=new_conversation_share.conversation_permission,
                meta_data=new_conversation_share.metadata,
            )

            session.add(conversation_share)
            await session.commit()

            await session.refresh(conversation_share)

        return convert.conversation_share_from_db(conversation_share)

    async def get_conversation_shares(
        self,
        user_principal: auth.UserPrincipal,
        conversation_id: uuid.UUID | None,
        include_unredeemable: bool,
    ) -> ConversationShareList:
        async with self._get_session() as session:
            query = select(db.ConversationShare).where(
                and_(
                    db.ConversationShare.owner_id == user_principal.user_id,
                    or_(include_unredeemable is True, col(db.ConversationShare.is_redeemable).is_(True)),
                )
            )
            if conversation_id is not None:
                query = query.where(db.ConversationShare.conversation_id == conversation_id)

            conversation_shares = await session.exec(query)

            return convert.conversation_share_list_from_db(conversation_shares)

    async def get_conversation_share(
        self,
        user_principal: auth.UserPrincipal,
        conversation_share_id: uuid.UUID,
    ) -> ConversationShare:
        async with self._get_session() as session:
            conversation_share = (
                await session.exec(
                    select(db.ConversationShare)
                    .where(db.ConversationShare.conversation_share_id == conversation_share_id)
                    .where(
                        or_(
                            db.ConversationShare.owner_id == user_principal.user_id,
                            col(db.ConversationShare.is_redeemable).is_(True),
                        )
                    )
                )
            ).one_or_none()

            if conversation_share is None:
                raise exceptions.NotFoundError()

            return convert.conversation_share_from_db(conversation_share)

    async def delete_conversation_share(
        self,
        user_principal: auth.UserPrincipal,
        conversation_share_id: uuid.UUID,
    ) -> None:
        async with self._get_session() as session:
            conversation_share = (
                await session.exec(
                    select(db.ConversationShare)
                    .where(
                        db.ConversationShare.owner_id == user_principal.user_id,
                        db.ConversationShare.conversation_share_id == conversation_share_id,
                        col(db.ConversationShare.is_redeemable).is_(True),
                    )
                    .with_for_update()
                )
            ).one_or_none()

            if conversation_share is None:
                raise exceptions.NotFoundError()

            await session.delete(conversation_share)
            await session.commit()

    async def redeem_conversation_share(
        self,
        user_principal: auth.UserPrincipal,
        conversation_share_id: uuid.UUID,
    ) -> ConversationShareRedemption:
        async with self._get_session() as session:
            await user_.add_or_update_user_from(session=session, user_principal=user_principal)

            # any user can redeem a "redeemable" share, if they have the ID
            conversation_share = (
                await session.exec(
                    select(db.ConversationShare).where(
                        db.ConversationShare.conversation_share_id == conversation_share_id,
                        col(db.ConversationShare.is_redeemable).is_(True),
                    )
                )
            ).one_or_none()
            if conversation_share is None:
                raise exceptions.NotFoundError()

            new_participant = False
            participant = (
                await session.exec(
                    select(db.UserParticipant)
                    .where(db.UserParticipant.conversation_id == conversation_share.conversation_id)
                    .where(db.UserParticipant.user_id == user_principal.user_id)
                    .with_for_update()
                )
            ).one_or_none()
            new_participant = participant is None or not participant.active_participant

            if participant is None:
                participant = db.UserParticipant(
                    conversation_id=conversation_share.conversation_id,
                    user_id=user_principal.user_id,
                    conversation_permission=conversation_share.conversation_permission,
                )

            if not participant.active_participant:
                participant.active_participant = True

            if (
                new_participant
                or
                # only re-assign permission for existing participants if it's a promotion
                (participant.conversation_permission == "read" and conversation_share.conversation_permission != "read")
            ):
                participant.conversation_permission = conversation_share.conversation_permission

            session.add(participant)

            redemption = db.ConversationShareRedemption(
                conversation_share_id=conversation_share_id,
                conversation_id=conversation_share.conversation_id,
                redeemed_by_user_id=user_principal.user_id,
                conversation_permission=participant.conversation_permission,
                new_participant=new_participant,
            )
            session.add(redemption)

            await session.commit()

            await session.refresh(redemption)

            return convert.conversation_share_redemption_from_db(redemption)

    async def get_redemptions_for_share(
        self,
        user_principal: auth.UserPrincipal,
        conversation_share_id: uuid.UUID,
    ) -> ConversationShareRedemptionList:
        async with self._get_session() as session:
            redemptions = await session.exec(
                select(db.ConversationShareRedemption)
                .join(db.ConversationShare)
                .where(
                    db.ConversationShareRedemption.conversation_share_id == conversation_share_id,
                    db.ConversationShare.owner_id == user_principal.user_id,
                )
            )

            return convert.conversation_share_redemption_list_from_db(redemptions)

    async def get_redemptions_for_user(
        self,
        user_principal: auth.UserPrincipal,
    ) -> ConversationShareRedemptionList:
        async with self._get_session() as session:
            redemptions = await session.exec(
                select(db.ConversationShareRedemption).where(
                    db.ConversationShareRedemption.redeemed_by_user_id == user_principal.user_id,
                )
            )

            return convert.conversation_share_redemption_list_from_db(redemptions)
