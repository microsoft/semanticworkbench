import contextlib
import datetime
import logging
import pathlib
import uuid
from contextlib import asynccontextmanager
from typing import Annotated, Any, AsyncIterator
from urllib.parse import urlparse

import sqlalchemy
import sqlalchemy.event
import sqlalchemy.orm
import sqlalchemy.orm.attributes
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import Field, Relationship, Session, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from . import service_user_principals
from .config import DBSettings

# Download DB Browser for SQLite to view the database
# https://sqlitebrowser.org/dl/

logger = logging.getLogger(__name__)


def date_time_nullable():
    return Field(sa_column=sqlalchemy.Column(sqlalchemy.DateTime(timezone=True), nullable=True))


def date_time_default_to_now(index: bool | None = None):
    return Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.DateTime(timezone=True),
            nullable=False,
            index=index,
            default=lambda: datetime.datetime.now(datetime.UTC),
        ),
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
    )


class User(SQLModel, table=True):
    user_id: str = Field(primary_key=True)
    created_datetime: datetime.datetime = date_time_default_to_now()
    name: str
    image: str | None = None
    service_user: bool = False

    def _on_update(self, session: Session) -> None:
        # update UserParticipants for this user
        participants = session.exec(select(UserParticipant).where(UserParticipant.user_id == self.user_id))
        for participant in participants:
            participant.name = self.name
            participant.image = self.image
            participant.service_user = self.service_user
            session.add(participant)

        # update WorkflowUserParticipants for this user
        participants = session.exec(
            select(WorkflowUserParticipant).where(WorkflowUserParticipant.user_id == self.user_id)
        )
        for participant in participants:
            participant.name = self.name
            participant.image = self.image
            participant.service_user = self.service_user
            session.add(participant)


class AssistantServiceRegistration(SQLModel, table=True):
    assistant_service_id: str = Field(primary_key=True)
    created_by_user_id: str = Field(foreign_key="user.user_id")
    created_datetime: datetime.datetime = date_time_default_to_now()
    name: str
    description: str
    include_in_listing: bool = True
    api_key_name: str

    assistant_service_url: str = ""
    assistant_service_online_expiration_datetime: Annotated[datetime.datetime | None, date_time_nullable()] = None
    assistant_service_online: bool = False

    related_created_by_user: User = Relationship(sa_relationship_kwargs={"lazy": "selectin"})


class Assistant(SQLModel, table=True):
    assistant_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: str = Field(foreign_key="user.user_id", index=True)
    assistant_service_id: str = Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.ForeignKey(
                "assistantserviceregistration.assistant_service_id",
                name="fk_assistant_assistant_service_id_assistantserviceregistration",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
    )
    created_datetime: datetime.datetime = date_time_default_to_now()
    name: str
    image: str | None = None
    meta_data: dict[str, Any] = Field(sa_column=sqlalchemy.Column("metadata", sqlalchemy.JSON), default={})

    # this relationship is needed to enforce correct INSERT order by SQLModel
    related_owner: User = Relationship()
    related_assistant_service_registration: sqlalchemy.orm.Mapped[AssistantServiceRegistration] = Relationship(
        sa_relationship_kwargs={"lazy": "selectin"}
    )

    def _on_update(self, session: Session) -> None:
        # update AssistantParticipants for this assistant
        participants = session.exec(
            select(AssistantParticipant).where(AssistantParticipant.assistant_id == self.assistant_id)
        )
        for participant in participants:
            participant.name = self.name
            participant.image = self.image
            session.add(participant)


class Conversation(SQLModel, table=True):
    conversation_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_datetime: datetime.datetime = date_time_default_to_now()
    owner_id: str = Field(foreign_key="user.user_id")
    title: str
    meta_data: dict[str, Any] = Field(sa_column=sqlalchemy.Column("metadata", sqlalchemy.JSON), default={})

    # this relationship is needed to enforce correct INSERT order by SQLModel
    related_owner: sqlalchemy.orm.Mapped[User] = Relationship()


class AssistantParticipant(SQLModel, table=True):
    conversation_id: uuid.UUID = Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.ForeignKey(
                "conversation.conversation_id",
                name="fk_assistantparticipant_conversation_id_conversation",
                ondelete="CASCADE",
            ),
            primary_key=True,
            nullable=False,
        ),
    )
    assistant_id: uuid.UUID = Field(primary_key=True)
    name: str = ""
    image: str | None = None
    joined_datetime: datetime.datetime = date_time_default_to_now()
    status: str | None = None
    status_updated_datetime: datetime.datetime = date_time_default_to_now()
    active_participant: bool = True

    # this relationship is needed to enforce correct INSERT order by SQLModel
    related_conversation: Conversation = Relationship()

    def _on_update(self, session: Session) -> None:
        # update this participant to match the related assistant, if one exists
        assistant = session.exec(select(Assistant).where(Assistant.assistant_id == self.assistant_id)).one_or_none()
        if assistant is None:
            return

        logger.info("updating assistant participant %s to match assistant %s", self, assistant)
        sqlalchemy.orm.attributes.set_attribute(self, "name", assistant.name)
        sqlalchemy.orm.attributes.set_attribute(self, "image", assistant.image)

    def _on_insert(self, session: Session) -> None:
        # update this participant to match the related assistant, requiring one to exist
        assistant = session.exec(select(Assistant).where(Assistant.assistant_id == self.assistant_id)).one()
        sqlalchemy.orm.attributes.set_attribute(self, "name", assistant.name)
        sqlalchemy.orm.attributes.set_attribute(self, "image", assistant.image)


class UserParticipant(SQLModel, table=True):
    conversation_id: uuid.UUID = Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.ForeignKey(
                "conversation.conversation_id",
                name="fk_userparticipant_conversation_id_conversation",
                ondelete="CASCADE",
            ),
            primary_key=True,
            nullable=False,
        ),
    )
    user_id: str = Field(primary_key=True)
    name: str = ""
    image: str | None = None
    service_user: bool = False
    joined_datetime: datetime.datetime = date_time_default_to_now()
    status: str | None = None
    status_updated_datetime: datetime.datetime = date_time_default_to_now()
    active_participant: bool = True

    # this relationship is needed to enforce correct INSERT order by SQLModel
    related_conversation: Conversation = Relationship()

    def _on_update(self, session: Session) -> None:
        # update this participant to match the related user, if one exists
        user = session.exec(select(User).where(User.user_id == self.user_id)).one_or_none()
        if user is None:
            return

        sqlalchemy.orm.attributes.set_attribute(self, "name", user.name)
        sqlalchemy.orm.attributes.set_attribute(self, "image", user.image)
        sqlalchemy.orm.attributes.set_attribute(self, "service_user", user.service_user)

    def _on_insert(self, session: Session) -> None:
        # update this participant to match the related user, requiring one to exist
        user = session.exec(select(User).where(User.user_id == self.user_id)).one()

        sqlalchemy.orm.attributes.set_attribute(self, "name", user.name)
        sqlalchemy.orm.attributes.set_attribute(self, "image", user.image)
        sqlalchemy.orm.attributes.set_attribute(self, "service_user", user.service_user)


class ConversationMessage(SQLModel, table=True):
    sequence: int = Field(default=None, nullable=False, primary_key=True)
    message_id: uuid.UUID = Field(default_factory=uuid.uuid4, unique=True)
    conversation_id: uuid.UUID = Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.ForeignKey(
                "conversation.conversation_id",
                name="fk_conversationmessage_conversation_id_conversation",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
    )
    created_datetime: datetime.datetime = date_time_default_to_now()
    sender_participant_id: str
    sender_participant_role: str
    message_type: str
    content: str
    content_type: str
    meta_data: dict[str, Any] = Field(sa_column=sqlalchemy.Column("metadata", sqlalchemy.JSON), default={})
    filenames: list[str] = Field(sa_column=sqlalchemy.Column(sqlalchemy.JSON), default=[])

    # this relationship is needed to enforce correct INSERT order by SQLModel
    related_conversation: Conversation = Relationship()


class File(SQLModel, table=True):
    file_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: uuid.UUID = Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.ForeignKey(
                "conversation.conversation_id",
                name="fk_file_conversation_id_conversation",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
    )

    filename: str
    current_version: int
    created_datetime: datetime.datetime = date_time_default_to_now(index=True)

    # this relationship is needed to enforce correct INSERT order by SQLModel
    related_conversation: Conversation = Relationship()

    __table_args__ = (
        sqlalchemy.UniqueConstraint("conversation_id", "filename", name="uq_file_conversation_id_filename"),
    )

    def storage_filename_for(self, version: int) -> str:
        return f"{self.file_id.hex}:{self.filename}:{str(version).zfill(7)}"


class FileVersion(SQLModel, table=True):
    file_id: uuid.UUID = Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.ForeignKey(
                "file.file_id",
                name="fk_fileversion_file_id_file",
                ondelete="CASCADE",
            ),
            primary_key=True,
            nullable=False,
        ),
    )
    version: int = Field(primary_key=True)
    participant_id: str
    participant_role: str
    created_datetime: datetime.datetime = date_time_default_to_now(index=True)
    meta_data: dict[str, Any] = Field(sa_column=sqlalchemy.Column("metadata", sqlalchemy.JSON), default={})
    content_type: str
    file_size: int

    # this relationship is needed to enforce correct INSERT order by SQLModel
    related_file: File = Relationship()

    # spell-checker: ignore fileversion
    __table_args__ = (sqlalchemy.UniqueConstraint("file_id", "version", name="uq_fileversion_file_id_version"),)


class WorkflowDefinition(SQLModel, table=True):
    workflow_definition_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    data: dict[str, Any] = Field(sa_column=sqlalchemy.Column("data", sqlalchemy.JSON))


class WorkflowUserParticipant(SQLModel, table=True):
    workflow_definition_id: uuid.UUID = Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.ForeignKey(
                "workflowdefinition.workflow_definition_id",
                name="fk_workflowuserparticipant_workflowdefinition",
                ondelete="CASCADE",
            ),
            primary_key=True,
        ),
    )
    user_id: str = Field(primary_key=True)
    name: str = ""
    image: str | None = None
    service_user: bool = False
    active_participant: bool = True

    # this relationship is needed to enforce correct INSERT order by SQLModel
    related_workflow_definition: WorkflowDefinition = Relationship()

    def _on_update(self, session: Session) -> None:
        """Update this participant to match the related user, if one exists."""
        user = session.exec(select(User).where(User.user_id == self.user_id)).one_or_none()
        if user is None:
            return

        sqlalchemy.orm.attributes.set_attribute(self, "name", user.name)
        sqlalchemy.orm.attributes.set_attribute(self, "image", user.image)
        sqlalchemy.orm.attributes.set_attribute(self, "service_user", user.service_user)

    def _on_insert(self, session: Session) -> None:
        """Update this participant to match the related user, requiring one to exist."""
        user = session.exec(select(User).where(User.user_id == self.user_id)).one()

        sqlalchemy.orm.attributes.set_attribute(self, "name", user.name)
        sqlalchemy.orm.attributes.set_attribute(self, "image", user.image)
        sqlalchemy.orm.attributes.set_attribute(self, "service_user", user.service_user)


class WorkflowRun(SQLModel, table=True):
    workflow_run_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workflow_definition_id: uuid.UUID = Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.ForeignKey(
                "workflowdefinition.workflow_definition_id",
                name="fk_workflowrun_workflowdefinition",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
    )
    data: dict[str, Any] = Field(sa_column=sqlalchemy.Column("data", sqlalchemy.JSON))

    # this relationship is needed to enforce correct INSERT order by SQLModel
    related_workflow_definition: WorkflowDefinition = Relationship()


NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
SQLModel.metadata.naming_convention = NAMING_CONVENTION


def ensure_url_is_async(url: str) -> str:
    return url.replace("sqlite://", "sqlite+aiosqlite://").replace("postgresql://", "postgresql+asyncpg://")


@asynccontextmanager
async def create_engine(settings: DBSettings) -> AsyncIterator[AsyncEngine]:
    # ensure that the database url is using the async driver
    db_url = ensure_url_is_async(settings.url)
    parsed_url = urlparse(db_url)
    is_sqlite = parsed_url.scheme.startswith("sqlite")
    is_postgres = parsed_url.scheme.startswith("postgresql")

    url_for_log = db_url
    if parsed_url.password:
        url_for_log = url_for_log.replace(parsed_url.password, "****")
    logger.info("creating database engine for %s", url_for_log)

    if is_sqlite and "/" in parsed_url.path:
        # create parent directory for sqlite db file as a convenience
        file_path = parsed_url.path[1:]
        pathlib.Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    kw_args: dict = {"echo": settings.echosql, "future": True}
    if is_postgres:
        kw_args.update({
            "connect_args": {
                "ssl": settings.postgresql_ssl_mode,
            },
            "pool_pre_ping": True,
            "pool_size": settings.postgresql_pool_size,
        })

    engine = create_async_engine(db_url, **kw_args)

    try:
        yield engine
    finally:
        await engine.dispose()


@sqlalchemy.event.listens_for(Session, "before_flush")
def receive_before_flush(session: Session, flush_context, instances) -> None:
    for obj in session.dirty:
        if not hasattr(obj, "_on_update"):
            continue
        obj._on_update(session)

    for obj in session.new:
        if not hasattr(obj, "_on_insert"):
            continue
        obj._on_insert(session)


async def bootstrap_db(engine: AsyncEngine, settings: DBSettings) -> None:
    logger.info("bootstrapping database; migrate=%s", settings.migrate_on_startup)
    if settings.migrate_on_startup:
        await migrate_schema(engine=engine, alembic_root_path=settings.alembic_root_path)
    else:
        await create_schema(engine=engine)
    await create_default_data(engine=engine)


async def migrate_schema(engine: AsyncEngine, alembic_root_path: str) -> None:
    if "sqlite" in engine.dialect.name:
        return await create_schema(engine)

    from alembic import command, config

    logger.info("migrating database schema; alembic_root_path=%s", alembic_root_path)

    with contextlib.chdir(alembic_root_path):

        def execute_upgrade(connection) -> None:
            logger.info("running alembic upgrade to head")
            cfg = config.Config("alembic.ini")
            cfg.attributes["connection"] = connection
            command.upgrade(cfg, "head")

        def execute_check(connection) -> None:
            logger.info("running alembic check")
            cfg = config.Config("alembic.ini")
            cfg.attributes["connection"] = connection
            command.check(cfg)

        async with engine.begin() as conn:
            await conn.run_sync(execute_upgrade)
            await conn.run_sync(execute_check)


async def create_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def create_default_data(engine: AsyncEngine) -> None:
    async with create_session(engine) as session:
        workbench_user = User(
            user_id=service_user_principals.semantic_workbench.user_id,
            name=service_user_principals.semantic_workbench.name,
            service_user=True,
        )
        await insert_if_not_exists(session, workbench_user)
        await session.commit()


@asynccontextmanager
async def create_session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    session_maker = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
    )
    async with session_maker() as async_session:
        yield async_session


async def insert_if_not_exists(session: AsyncSession, model: SQLModel) -> bool:
    """
    Inserts the provided record if a row with the same primary key(s) does already exist in the table.
    Returns True if the record was inserted, False if it already existed.
    """

    # the postgresql.insert function is used to generate an INSERT statement with an ON CONFLICT DO NOTHING clause.
    # note that sqlite also supports ON CONFLICT DO NOTHING, so this works with both database types.
    statement = (
        postgresql.insert(model.__class__).values(**model.model_dump(exclude_unset=True)).on_conflict_do_nothing()
    )
    conn = await session.connection()
    result = await conn.execute(statement)
    return result.rowcount > 0
