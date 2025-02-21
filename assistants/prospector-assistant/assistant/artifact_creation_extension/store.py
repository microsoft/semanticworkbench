from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import yaml
from semantic_workbench_assistant.assistant_app.context import ConversationContext, storage_directory_for_context
from semantic_workbench_assistant.assistant_app.protocol import (
    AssistantConversationInspectorStateDataModel,
    ReadOnlyAssistantConversationInspectorStateProvider,
)

from .document import Document, DocumentHeader


class DocumentStore:
    def __init__(self, store_path: Path):
        store_path.mkdir(parents=True, exist_ok=True)
        self.store_path = store_path

    def _path_for(self, id: str) -> Path:
        return self.store_path / f"{id}.json"

    def write(self, document: Document) -> None:
        path = self._path_for(document.metadata.document_id)
        path.write_text(document.model_dump_json(indent=2))

    def read(self, id: str) -> Document:
        path = self._path_for(id)
        try:
            return Document.model_validate_json(path.read_text())
        except FileNotFoundError:
            raise ValueError(f"Document not found: {id}")

    @contextmanager
    def checkout(self, id: str) -> Iterator[Document]:
        document = self.read(id=id)
        yield document
        self.write(document)

    def delete(self, id: str) -> None:
        path = self._path_for(id)
        path.unlink(missing_ok=True)

    def list_documents(self) -> list[DocumentHeader]:
        documents = []
        for path in self.store_path.glob("*.json"):
            document = Document.model_validate_json(path.read_text())
            documents.append(DocumentHeader(document_id=document.metadata.document_id, title=document.title))

        return sorted(documents, key=lambda document: document.title.lower())


def for_context(context: ConversationContext) -> DocumentStore:
    doc_store_root = storage_directory_for_context(context) / "document_store"
    return DocumentStore(doc_store_root)


def project_to_yaml(state: dict | list[dict]) -> str:
    """
    Project the state to a yaml code block.
    """
    state_as_yaml = yaml.dump(state, sort_keys=False)
    return f"```yaml\n{state_as_yaml}\n```"


class DocumentWorkspaceInspector(ReadOnlyAssistantConversationInspectorStateProvider):
    @property
    def display_name(self) -> str:
        return "Document Workspace"

    @property
    def description(self) -> str:
        return "Documents in the workspace."

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        store = for_context(context)
        documents: list[dict] = []
        for header in store.list_documents():
            doc = store.read(header.document_id)
            documents.append(doc.model_dump(mode="json"))
        projected = project_to_yaml(documents)
        return AssistantConversationInspectorStateDataModel(data={"content": projected})


class AllDocumentsInspector(ReadOnlyAssistantConversationInspectorStateProvider):
    @property
    def display_name(self) -> str:
        return "Documents"

    @property
    def description(self) -> str:
        return "All documents."

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        store = for_context(context)
        headers = store.list_documents()
        if not headers:
            return AssistantConversationInspectorStateDataModel(data={"content": "No active document."})

        toc: list[str] = []
        content: list[str] = []

        headers = store.list_documents()
        for header in headers:
            doc = store.read(header.document_id)
            toc.append(f"- [{doc.title}](#{doc.title.lower().replace(' ', '-')})")
            content.append(project_document_to_markdown(doc))

        tocs = "\n".join(toc)
        contents = "\n".join(content)
        projection = f"```markdown\nDocuments:\n\n{tocs}\n\n{contents}\n```"

        return AssistantConversationInspectorStateDataModel(data={"content": projection})


def project_document_to_markdown(doc: Document) -> str:
    """
    Project the document to a markdown code block.
    """
    markdown = f"# {doc.title}\n\n***{doc.metadata.purpose}***\n\n"
    for section in doc.sections:
        markdown += f"{'#' * section.heading_level} {section.section_number} {section.title}\n\n***{section.metadata.purpose}***\n\n{section.content}\n\n"
        markdown += "-" * 3 + "\n\n"

    return markdown
