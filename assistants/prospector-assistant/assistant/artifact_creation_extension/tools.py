from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field
from semantic_workbench_assistant.assistant_app.context import ConversationContext

from ._llm import ToolArgsModel
from .document import Document, DocumentHeader, DocumentMetadata, Section, SectionMetadata
from .store import DocumentStore, for_context


class ArgsWithDocumentStore(ToolArgsModel):
    def set_context(self, context: ConversationContext) -> None:
        self._context = context

    @property
    def store(self) -> DocumentStore:
        return for_context(self._context)


class CreateDocumentArgs(ArgsWithDocumentStore):
    title: str = Field(description="Document title")
    purpose: Optional[str] = Field(description="Describes the intent of the document.")
    audience: Optional[str] = Field(description="Describes the intended audience for the document.")
    other_guidelines: Optional[str] = Field(
        description="Describes any other guidelines or standards that the document should follow."
    )


async def create_document(args: CreateDocumentArgs) -> DocumentMetadata:
    """
    Create a new document with the specified metadata.
    """
    metadata = DocumentMetadata()
    if args.purpose is not None:
        metadata.purpose = args.purpose
    if args.audience is not None:
        metadata.audience = args.audience
    if args.other_guidelines is not None:
        metadata.other_guidelines = args.other_guidelines
    document = Document(title=args.title, metadata=metadata)

    args.store.write(document)

    return document.metadata


class UpdateDocumentArgs(ArgsWithDocumentStore):
    document_id: str = Field(description="The id of the document to update.")
    title: Optional[str] = Field(description="The updated title of the document. Pass None to leave unchanged.")
    purpose: Optional[str] = Field(
        description="Describes the intent of the document. Can be left blank. Pass None to leave unchanged."
    )
    audience: Optional[str] = Field(
        description="Describes the intended audience for the document. Can be left blank. Pass None to leave unchanged."
    )
    other_guidelines: Optional[str] = Field(
        description="Describes any other guidelines or standards that the document should follow. Can be left blank. Pass None to leave unchanged."
    )


async def update_document(args: UpdateDocumentArgs) -> DocumentMetadata:
    """
    Update the metadata of an existing document.
    """
    with args.store.checkout(args.document_id) as document:
        if args.title is not None:
            document.title = args.title
        if args.purpose is not None:
            document.metadata.purpose = args.purpose
        if args.audience is not None:
            document.metadata.audience = args.audience
        if args.other_guidelines is not None:
            document.metadata.other_guidelines = args.other_guidelines

        document.metadata.last_modified_at = datetime.now(timezone.utc)

    return document.metadata


class GetDocumentArgs(ArgsWithDocumentStore):
    document_id: str = Field(description="The id of the document to retrieve.")


async def get_document(args: GetDocumentArgs) -> Document:
    """
    Retrieve a document by its id.
    """
    return args.store.read(id=args.document_id)


class RemoveDocumentArgs(ArgsWithDocumentStore):
    document_id: str = Field(description="The id of the document to remove.")


async def remove_document(args: RemoveDocumentArgs) -> Document:
    """
    Remove a document from the workspace.
    """
    document = args.store.read(id=args.document_id)
    args.store.delete(id=args.document_id)
    return document


class CreateDocumentSectionArgs(ArgsWithDocumentStore):
    document_id: str = Field(description="The id of the document to add the section to.")
    insert_before_section_number: Optional[str] = Field(
        description="The section number of the section to insert the new section ***before***."
        " Pass None to insert at the end of the document, after all existing sections, if any."
        " For example, if there are sections '1', '2', and '3', and you want to insert a section"
        " between '2' and '3'. Then the insert_before_section_number should be '3'.",
    )
    section_heading_level: int = Field(description="The heading level of the new section.")
    section_title: str = Field(description="The title of the new section.")
    section_purpose: Optional[str] = Field(description="Describes the intent of the new section.")
    section_content: str = Field(description="The content of the new section. Can be left blank.")


async def create_document_section(args: CreateDocumentSectionArgs) -> Section:
    """
    Create a new section in an existing document.
    """

    with args.store.checkout(args.document_id) as document:
        document.metadata.last_modified_at = datetime.now(timezone.utc)

        metadata = SectionMetadata()
        if args.section_purpose is not None:
            metadata.purpose = args.section_purpose

        heading_level = args.section_heading_level
        insert_at_index = len(document.sections)
        if args.insert_before_section_number is not None:
            _, insert_at_index = _find_section(args.insert_before_section_number, document)
            if insert_at_index == -1:
                raise ValueError(
                    f"Section {args.insert_before_section_number} not found in document {args.document_id}"
                )

        section = Section(
            title=args.section_title,
            content=args.section_content,
            metadata=metadata,
            section_number="will be renumbered",
            heading_level=heading_level,
        )

        document.sections.insert(insert_at_index, section)

        _renumber_sections(document.sections)

        return section


class UpdateDocumentSectionArgs(ArgsWithDocumentStore):
    document_id: str = Field(description="The id of the document containing the section to update.")
    section_number: str = Field(description="The number of the section to update.")
    section_heading_level: Optional[int] = Field(
        description="The updated heading level of the section. Pass None to leave unchanged."
    )
    section_title: Optional[str] = Field(description="The updated title of the section. Pass None to leave unchanged.")
    section_purpose: Optional[str] = Field(
        description="The updated purpose of the new section. Pass None to leave unchanged."
    )
    section_content: Optional[str] = Field(
        description="The updated content of the section. Pass None to leave unchanged."
    )


async def update_document_section(args: UpdateDocumentSectionArgs) -> Section:
    """
    Update the content of a section in an existing document.
    """
    with args.store.checkout(args.document_id) as document:
        section, _ = _find_section(args.section_number, document)
        if section is None:
            raise ValueError(f"Section {args.section_number} not found in document {args.document_id}")

        if args.section_heading_level is not None:
            section.heading_level = args.section_heading_level
        if args.section_title is not None:
            section.title = args.section_title
        if args.section_purpose is not None:
            section.metadata.purpose = args.section_purpose
        if args.section_content is not None:
            section.content = args.section_content

        document.metadata.last_modified_at = datetime.now(timezone.utc)
        _renumber_sections(document.sections)

    return section


class RemoveDocumentSectionArgs(ArgsWithDocumentStore):
    document_id: str = Field(description="The id of the document containing the section to remove.")
    section_number: str = Field(description="The section number of the section to remove.")


async def remove_document_section(args: RemoveDocumentSectionArgs) -> Section:
    """
    Remove a section from an existing document. Note that removing a section will also remove all nested sections.
    """
    with args.store.checkout(args.document_id) as document:
        section, _ = _find_section(args.section_number, document)
        if section is None:
            raise ValueError(f"Section with number {args.section_number} not found in document {args.document_id}")

        document.sections.remove(section)

        _renumber_sections(document.sections)

        document.metadata.last_modified_at = datetime.now(timezone.utc)

    return section


class DocumentList(BaseModel):
    documents: list[DocumentHeader]
    count: int = Field(description="The number of documents in the workspace.")


class ListDocumentsArgs(ArgsWithDocumentStore):
    pass


async def list_documents(args: ListDocumentsArgs) -> DocumentList:
    """
    List the titles of all documents in the workspace.
    """
    headers = args.store.list_documents()
    return DocumentList(documents=headers, count=len(headers))


def _find_section(section_number: str, document: Document) -> tuple[Section | None, int]:
    section, index = next(
        (
            (section, index)
            for index, section in enumerate(document.sections)
            if section.section_number == section_number
        ),
        (None, -1),
    )
    return section, index


def _renumber_sections(sections: list[Section]) -> None:
    """
    Renumber the sections in the list.
    """
    current_heading_level = -1
    sections_at_level = defaultdict(lambda: 0)
    current_section_number_parts: list[str] = []

    for section in sections:
        if section.heading_level == current_heading_level:
            sections_at_level[section.heading_level] += 1
            current_section_number_parts.pop()

        if section.heading_level > current_heading_level:
            current_heading_level = section.heading_level
            sections_at_level[section.heading_level] = 1

        if section.heading_level < current_heading_level:
            for i in range(current_heading_level - section.heading_level):
                sections_at_level.pop(current_heading_level + i, 0)
            current_heading_level = section.heading_level
            sections_at_level[section.heading_level] += 1
            current_section_number_parts = current_section_number_parts[: section.heading_level - 1]

        current_section_number_parts.append(str(sections_at_level[current_heading_level]))
        section.section_number = ".".join(current_section_number_parts)
