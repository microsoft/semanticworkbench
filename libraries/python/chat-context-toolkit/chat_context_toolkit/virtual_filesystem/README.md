# Virtual File System (for chat completions)

## The problem

How to expose files of various types and from various sources to an LLM model via chat-completion, so that it
can read them, (optionally) write to them, and reason over them effectively?

Files can be numerous and large. How can they be visible to the model without exceeding the tokem limit?

## Some not-so-great solutions

- Include all files, including their contents, in a system or user message

  - This does not scale as the number of files grows, or the size of the files grows.

- Provide various tools for the model to interact with files from various sources
  - This is better as files can be retrieved selectively.
  - The more tools however, the more likely the model will do something undesirable or unexpected.
  - For example, if the model is given a tool for each source to list files and read files,
    it may use the wrong tool.

## A better solution

Leverage the training that vendors are doing to make LLMs effective at coding scenarios - specifically, training
on reasoning over file systems and managing files.

- Present all files in a single, virtual file system that the model can interact with.
- Provide tools for the model to list files, search files, and read files.
- Optionally:
  - Allow developers to provide tools for writing files.
  - Allow developers to provide a constrained list of the most relevant files in the system message (to skip the search step for these files).

The virtual file system provides a file-system abstraction for use with OpenAI LLM models through chat-completions.
The file system is presented to the model via chat-completion tools, and optionally, system messages. The file listings and
their contents are backed by one or more developer-provided FileSources, which themselves can be backed by arbitrary storage
systems (e.g., local file system, cloud storage, databases, in memory).

FileSources are mounted at specified paths in the virtual file system. The LLM can then interact with the file
system using tools like `ls`, `grep`, and `view` to list files, search files by content, and view file contents.

# Development tools

## Python

This project uses `uv` for python executable and dependency management. To create a virtual environment _and_ install dependencies, run:

```bash
uv sync  --all-extras --all-groups --frozen
```

To run python scripts in the created virtual environment, use:

```bash
uv run python <script.py>
```

## Tests

This project uses `pytest` for testing. To run tests, use:

```bash
uv run pytest
```
