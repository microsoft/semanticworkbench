# Document Assistant

## Overview

The Document Assistant is an AI assistant focused on document creation and editing within the Semantic Workbench.
It provides a seamless environment for creating, editing, and managing Markdown documents with side-by-side editing capabilities, guided assistance, and integration with external tools.

## Key Features

- **Side-by-side document editing**: Work on your documents with a split view showing both the editor and conversation, enabling real-time collaboration and feedback with the assistant.
- **Document management**: Create, view, and edit multiple Markdown documents within the same workspace.
- **Generated UI elements**: Get visual guidance through dynamically generated UI components that help organize your document workflow.
- **Autonomous tool execution**: The assistant can perform document-related tasks on your behalf, freeing you to focus on content creation.
- **MCP server integration**: Connects with Model Context Protocol (MCP) servers for extended functionality, particularly the filesystem-edit servers which enables the Markdown editing capability described at the beginning.
- **Local-only Office integration**: Optional integration with Microsoft Office applications through MCP (when enabled).

## How to Use the Document Assistant

### Getting Started

1. **Create a new conversation** in the Semantic Workbench and add the Document Assistant.
2. **Create a new document** by asking the assistant to create one for you. Example: "Create a new document about project requirements."
3. **Edit existing documents** by mentioning the document you want to work on. The document will be put into focus in the side panel editor.

### Document Management

- **Switch between documents**: Use the Documents tab in the inspector panel to see all available documents and switch between them.
- **Edit document content**: Make changes directly in the document editor panel, or ask the assistant to make specific edits for you.
- **Upload files**: Upload Markdown files to add them as context to your assistant.

### Advanced Features

- **Format documents**: Ask the assistant to format your document, create sections, add lists, tables, or other Markdown elements.
- **Collaborative editing**: The document locking mechanism ensures that only one editing operation happens at a time, preventing conflicts.
- **Document transformations**: Request content transformations like summarization, expansion, or style changes.

## Integration with Other Tools

When configured, the Document Assistant can work with:

- **MCP filesystem-edit server**: For advanced document editing capabilities.
- **Office integration**: When enabled, allows working with Microsoft Office documents.
- **Additional MCP servers**: Can be enabled for search, research, and other extended features.

## Tips for Effective Use

1. **Be specific in your requests**: Clearly state what changes you want to make to documents.
2. **Use the document editor for quick edits**: Make direct changes in the editor for smaller modifications.
3. **Ask the assistant for complex transformations**: Let the AI handle more complex document restructuring or content generation.
4. **Switch between documents as needed**: Use the Documents tab to manage multiple files in your workspace.
5. **Save often**: While documents are automatically saved, it's a good practice to confirm important changes.

## Common Use Cases

- Creating technical documentation and reports
- Drafting and editing business documents
- Organizing research notes and findings
- Creating structured content like tutorials or guides
- Collaborative document editing and review

The Document Assistant is designed to be intuitive and helpful for all users, making document creation and editing a more efficient and guided experience.
