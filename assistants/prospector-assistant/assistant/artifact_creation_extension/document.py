import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class SectionMetadata(BaseModel):
    purpose: str = ""
    """Describes the intent of the section."""

    # These are for humans
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    """Timestamp for when the section was created."""
    last_modified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    """Timestamp for the last modification."""


class Section(BaseModel):
    """
    Represents a section in a document, with a heading level, section number, title and content.

    Sections are the basic building blocks of a document. They are ordered within a document. They
    have a heading level of 1-N.
    """

    heading_level: int
    """The level of the section in the hierarchy. Top-level sections are level 1, and nested sections are level 2 and beyond."""
    section_number: str
    """The number of the section in a heirarchical format. For example, 1.1.1. Section numbers are unique within the document."""

    title: str
    """The title of the section."""
    content: str = ""
    """Content of the section, supporting Markdown for formatting."""

    metadata: SectionMetadata = SectionMetadata()
    """Metadata describing the section."""


class DocumentMetadata(BaseModel):
    """
    Metadata for a document, including title, purpose, audience, version, author, contributors,
    and timestamps for creation and last modification.
    """

    document_id: str = Field(default_factory=lambda: uuid.uuid4().hex[0:8])

    purpose: str = ""
    """Describes the intent of the document"""
    audience: str = ""
    """Describes the intended audience for the document"""

    # Value of this is still to be determined
    other_guidelines: str = ""
    """
    Describes any other guidelines or standards, stylistic, structure, etc.,
    that the document should follow (tone, style, length)
    """

    # Value of this is still to be determined
    supporting_documents: list[str] = Field(default_factory=list)
    """List of document titles for supporting documents."""

    # These are for humans
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    """Timestamp for when the document was created."""
    last_modified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    """Timestamp for the last modification."""


class Document(BaseModel):
    """
    Represents a complete document, including metadata, sections, and references to supporting documents.
    """

    title: str = ""
    """Title of the document. Doubles as a unique identifier for the document."""

    metadata: DocumentMetadata = DocumentMetadata()
    """Metadata describing the document."""

    sections: list[Section] = Field(default_factory=list)
    """Structured content of the document."""


class DocumentHeader(BaseModel):
    document_id: str
    title: str
