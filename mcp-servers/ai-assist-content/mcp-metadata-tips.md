# Metadata Specification in FastMCP Tools

FastMCP (the Python framework for **Model Context Protocol**) makes it easy to enrich tool definitions with metadata so that MCP clients (and the LLMs they host) can understand and use your tools effectively. According to the MCP spec, each tool is defined by a **name**, a **description**, and an **input schema** for its parameters ([Tools – Model Context Protocol Specification](https://spec.modelcontextprotocol.io/specification/2024-11-05/server/tools/#:~:text=,JSON%20Schema%20defining%20expected%20parameters)). Below, we explore how to provide rich descriptions for tools and parameters, what extra metadata can improve LLM usability, and best practices to ensure compatibility and discoverability.

## Defining Tool Descriptions and Parameter Metadata

**Tool Description:** In FastMCP, the simplest way to document a tool’s purpose is by using the function’s docstring. When you decorate a Python function with `@mcp.tool()`, FastMCP will capture the docstring as the tool’s **description**. This human-readable description is included in the tool listing that MCP clients retrieve. For example, a function defined as: 

```python
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b
``` 

would register a tool named “add” with the description “Add two numbers” ([GitHub - modelcontextprotocol/python-sdk: The official Python SDK for Model Context Protocol servers and clients](https://github.com/modelcontextprotocol/python-sdk#:~:text=,return%20a%20%2B%20b)). The MCP client’s `tools/list` response would include this description along with the tool name ([Tools – Model Context Protocol Specification](https://spec.modelcontextprotocol.io/specification/2024-11-05/server/tools/#:~:text=,)). Make sure the docstring clearly describes what the tool does in one or two sentences.

**Parameter Definitions:** FastMCP uses Python type hints (and Pydantic under the hood) to build a JSON Schema for your tool’s input parameters. Each parameter becomes a property in the tool’s **`inputSchema`**. By default, FastMCP infers the JSON Schema `type` (e.g. string, number, object, etc.) from the Python type hints. It also marks parameters as **required** unless you provide a default value. For instance, a tool with signature `def calculate_sum(a: int, b: int) -> int:` will have an inputSchema requiring both `a` and `b` of type number ([Hackteam - Build Your First MCP Server with TypeScript](https://hackteam.io/blog/build-your-first-mcp-server-with-typescript-in-under-10-minutes/#:~:text=description%3A%20,b)). If you give a parameter a default (e.g. `count: int = 10`), it will appear with a **`default`** value in the schema and be omitted from the “required” list ([Introducing Model Context Protocol (MCP) | Glama](https://glama.ai/blog/2024-11-25-model-context-protocol-quickstart#:~:text=inputSchema%3A%20%7B%20type%3A%20,%7D%2C)).

**Parameter Descriptions:** To enrich parameter metadata, you can use **Pydantic’s `Field`** annotations or type metadata. FastMCP supports Pydantic’s `Field()` to add JSON Schema metadata like descriptions, titles, constraints, etc. For example, you can define: 

```python
from typing import Annotated
from pydantic import Field

@mcp.tool()
def search(query: Annotated[str, Field(max_length=400, description="Search query (up to 400 chars)")],
           count: Annotated[int, Field(ge=1, le=20, description="Number of results (1-20)", default=10)] = 10) -> str:
    """Performs a web search ..."""
    ...
``` 

In this case, the `query` parameter is annotated with a max length and description, and `count` has a range, a default, and a description. These annotations will be reflected in the tool’s inputSchema. Pydantic uses the `description` argument of `Field` to populate the JSON Schema’s **description** for that field ([JSON Schema - Pydantic](https://docs.pydantic.dev/latest/concepts/json_schema/#:~:text=JSON%20Schema%20,The%20description%20of%20the%20field)). The resulting schema might include something like: 

```json
"properties": {
  "query": { "type": "string", "maxLength": 400, "description": "Search query (up to 400 chars)" },
  "count": { "type": "number", "minimum": 1, "maximum": 20, "default": 10, "description": "Number of results (1-20)" }
},
"required": ["query"]
``` 

Each parameter now has a human-friendly explanation and even validation info that the MCP client can pass along to the LLM or use for its own input validation. This way, when the client (or the LLM through the client) inspects the tool, it sees not just the parameter names and types, but also what they mean.

## Additional Metadata for LLM-Friendly Tools

Beyond basic descriptions and types, you can include **additional metadata fields** in the input schema to enhance how the LLM uses the tool:

- **Default Values:** As noted, providing default values in function signatures makes parameters optional. The JSON schema will include a `default` field for those parameters ([Introducing Model Context Protocol (MCP) | Glama](https://glama.ai/blog/2024-11-25-model-context-protocol-quickstart#:~:text=inputSchema%3A%20%7B%20type%3A%20,%7D%2C)). LLMs can see that a parameter is optional and may omit it or use the default behavior if appropriate.

- **Value Constraints:** Any constraints you add (min/max, length limits, regex patterns, enumerated choices) will be part of the schema. For example, if a parameter must be one of a few options (using `Literal` or `Enum` types), the schema will include an **`enum`** list of allowed values. These constraints help the LLM avoid invalid tool calls. While the LLM might not **guarantee** to always honor them, having them in metadata guides the model’s choices. For instance, a parameter defined with `Field(regex="^[0-9]{5}$", description="ZIP code (5 digits)")` would tell the client and model that the input should be a 5-digit ZIP code.

- **Title and Formatting:** JSON Schema supports a `title` for each field, which Pydantic auto-generates (usually capitalizing the field name) ([GitHub - kimtth/mcp-aoai-web-browsing: A minimal Model Context Protocol ️ server/client‍with Azure OpenAI and  web browser control via Playwright.](https://github.com/kimtth/mcp-aoai-web-browsing#:~:text=,30000%2C%20%27title%27%3A%20%27timeout%27%2C%20%27type%27%3A%20%27string)). Titles are optional short labels (e.g., “Url” for a field `url`). They might not significantly affect an LLM’s behavior, but they can be useful for UI displays in clients. The **description** is more important for the model, as it provides semantic context.

- **Examples (if supported):** Although not automatically generated by FastMCP, JSON Schema allows an `examples` field for parameters. If you manually extend the schema or use a Pydantic `Field(example=...)` (supported in Pydantic v2+), you could provide sample values. Examples can illustrate typical usage to both developers and possibly the model (some hosts might relay that info to the LLM). This is less common, but it’s another way to enrich metadata.

- **Tool Output Metadata:** MCP doesn’t require specifying an output schema in the tool definition – the tool result is provided at runtime. However, you can still hint at the output in the **tool description** (e.g., “returns the current weather as text”). This informs the LLM what to expect. The tool result itself can contain structured content (text or images), but since image rendering is disabled in this context, outputs will generally be text content ([Tools – Model Context Protocol Specification](https://spec.modelcontextprotocol.io/specification/2024-11-05/server/tools/#:~:text=,false)).

By providing these metadata fields, you make the tool more **self-documenting**. LLMs integrated via MCP get a function schema very similar to OpenAI’s function calling or Anthropic’s tool use format ([Introducing Model Context Protocol (MCP) | Glama](https://glama.ai/blog/2024-11-25-model-context-protocol-quickstart#:~:text=As%20far%20as%20I%20can,API%20or%20OpenAI%20Function%20Calling)), which they are trained to understand. In fact, one example shows an MCP tool definition that closely mirrors an OpenAI function spec (with types, descriptions, and defaults) ([Introducing Model Context Protocol (MCP) | Glama](https://glama.ai/blog/2024-11-25-model-context-protocol-quickstart#:~:text=%7B%20name%3A%20,max%209%2C%20default%200)). This alignment means the model can leverage its familiarity with JSON Schema to choose and use your tools correctly.

## Best Practices for Metadata Structure and Discoverability

To optimize compatibility across clients and ensure your tools are easily discoverable by an AI assistant, follow these best practices:

- **Use Clear, Descriptive Names:** Tool names should be unique and indicative of their action or domain. For instance, `get_weather` or `calculate_bmi` are preferable to generic names. A tool’s name is how the model refers to it, so make it concise and avoid ambiguity ([Tools – Model Context Protocol Specification](https://spec.modelcontextprotocol.io/specification/2024-11-05/server/tools/#:~:text=,)). Snake_case is commonly used in examples, but consistency is key.

- **Write Helpful Descriptions:** The tool description should be **model-oriented**. Describe the functionality and purpose in a way that helps the LLM decide when to use it. Include context or usage hints if appropriate. For example, a web search tool’s description might say it’s for “general queries, news, and online content... Supports pagination and freshness controls” ([Introducing Model Context Protocol (MCP) | Glama](https://glama.ai/blog/2024-11-25-model-context-protocol-quickstart#:~:text=%7B%20name%3A%20,max%209%2C%20default%200)). Such details guide the model on when this tool is relevant. However, keep descriptions factual and not excessively long (a few sentences is usually enough).

- **Document Parameters Thoroughly:** Each parameter’s name should reflect its meaning, and the schema description should specify what the model or user should provide. Mention units, format, or expected range if applicable (e.g. “height in meters”). This reduces confusion. In our earlier example, `location` had the description “City name or zip code” ([Tools – Model Context Protocol Specification](https://spec.modelcontextprotocol.io/specification/2024-11-05/server/tools/#:~:text=,%7D)) – making it clear what format the model should use. If a parameter is an optional filter or mode, say so in the description.

- **Leverage JSON Schema Standards:** Use standard JSON Schema keywords (through Pydantic or the SDK) to enforce and communicate constraints. Fields like `minimum`, `maximum`, `maxLength`, or `pattern` are machine-interpretable and also hint to the model the valid input range. For instance, specifying a number is 1-20 not only appears in the description but could also be encoded as `"minimum": 1, "maximum": 20` in the schema ([Introducing Model Context Protocol (MCP) | Glama](https://glama.ai/blog/2024-11-25-model-context-protocol-quickstart#:~:text=inputSchema%3A%20%7B%20type%3A%20,%7D%2C)). Standard fields ensure **compatibility** – any MCP client or intermediary can read them and potentially validate input before calling your tool.

- **Defaults and Optionals:** Provide default values for parameters that have a common default behavior. This way the model knows it can omit them if it doesn’t need to customize those. The schema’s `default` field and the absence of that param in `required` signal optionality clearly ([Introducing Model Context Protocol (MCP) | Glama](https://glama.ai/blog/2024-11-25-model-context-protocol-quickstart#:~:text=inputSchema%3A%20%7B%20type%3A%20,%7D%2C)). The model might then call the tool with only the essential arguments, simplifying its decisions.

- **Avoid Non-Standard Metadata:** Stick to the schema structure defined by MCP (which mirrors common function-calling schemas). Introducing custom fields not in the JSON Schema spec might cause clients to ignore them or, worse, misinterpret them. For maximum compatibility, use the intended fields (name, description, inputSchema properties) and standard JSON Schema annotations. All MCP clients are expected to handle these, since they are part of the protocol.

- **Human Readability and Consistency:** While the primary consumer of this metadata is the LLM and the client software, ensure the metadata is also easily readable by humans (developers or end users in a UI). This means using natural language in descriptions and consistent formatting. Many MCP hosts (like Claude Desktop or others) might display tool descriptions to the user or log them for developers. Clear metadata helps everyone understand the tool’s role.

- **Discovery and Updates:** FastMCP servers can dynamically add or remove tools. If your toolset changes at runtime, use the protocol’s `tools/listChanged` notification capability so clients know to refresh the list ([Tools – Model Context Protocol Specification](https://spec.modelcontextprotocol.io/specification/2024-11-05/server/tools/#:~:text=Servers%20that%20support%20tools%20MUST,capability)) ([Tools – Model Context Protocol Specification](https://spec.modelcontextprotocol.io/specification/2024-11-05/server/tools/#:~:text=List%20Changed%20Notification)). This ensures new tools (with their metadata) become discoverable, and removed tools aren’t attempted. From a metadata perspective, design your tool list such that each tool remains individually clear; don’t rely on contextual knowledge of other tools to explain one tool. Each tool’s metadata should stand on its own, since the model might consider them in isolation.

Following these practices will make your MCP server’s tools **robustly self-describing**. A well-structured inputSchema and description help the language model choose the right tool at the right time, much like how an API documentation helps a developer. In short, invest time in metadata as much as in functionality – it’s crucial for the **usability** of your tools in an AI-driven environment.

## References and Examples

To learn more or see this in action, check out the official MCP documentation and example projects:

- **Model Context Protocol Spec – Tools:** The MCP specification outlines the required schema for tools (name, description, inputSchema) and shows an example tool JSON listing ([Tools – Model Context Protocol Specification](https://spec.modelcontextprotocol.io/specification/2024-11-05/server/tools/#:~:text=,City%20name%20or%20zip%20code)). It confirms that **metadata** like descriptions are part of the standard tool definition.

- **FastMCP GitHub (Python):** The FastMCP README and examples demonstrate creating tools with decorators and docstrings ([GitHub - modelcontextprotocol/python-sdk: The official Python SDK for Model Context Protocol servers and clients](https://github.com/modelcontextprotocol/python-sdk#:~:text=,return%20a%20%2B%20b)). The code examples align with the spec (e.g., a tool to “Add two numbers” with its parameters). Advanced usage shows that you can use Pydantic models or fields for complex schemas (e.g. nested objects or validations) ([GitHub - jlowin/fastmcp: The fast, Pythonic way to build Model Context Protocol servers ](https://github.com/jlowin/fastmcp#:~:text=%40mcp,%2B%20extra_names)).

- **Community Examples:** For a real-world illustration, see the *Brave Web Search* tool example ([Introducing Model Context Protocol (MCP) | Glama](https://glama.ai/blog/2024-11-25-model-context-protocol-quickstart#:~:text=%7B%20name%3A%20,max%209%2C%20default%200)). Its metadata includes a rich description (purpose and usage notes) and an inputSchema with multiple parameters, each with type, description, and defaults ([Introducing Model Context Protocol (MCP) | Glama](https://glama.ai/blog/2024-11-25-model-context-protocol-quickstart#:~:text=inputSchema%3A%20%7B%20type%3A%20,%7D%2C)). This example highlights how to communicate tool capabilities to the LLM. Another example is a Playwright-based browsing tool, where the developer’s docstring “Navigate to a URL.” became the tool description, and the function signature generated an inputSchema with fields like `url` and `timeout` (with default) ([GitHub - kimtth/mcp-aoai-web-browsing: A minimal Model Context Protocol ️ server/client‍with Azure OpenAI and  web browser control via Playwright.](https://github.com/kimtth/mcp-aoai-web-browsing#:~:text=,30000%2C%20%27title%27%3A%20%27timeout%27%2C%20%27type%27%3A%20%27string)).

By using FastMCP’s features to specify metadata, you ensure that MCP clients (and the LLMs behind them) have a rich, structured understanding of your tools. This leads to more accurate and confident tool usage, making your LLM-powered application more effective and reliable. Always remember: well-described tools are as important as well-implemented tools in an AI context ([Introducing Model Context Protocol (MCP) | Glama](https://glama.ai/blog/2024-11-25-model-context-protocol-quickstart#:~:text=As%20far%20as%20I%20can,API%20or%20OpenAI%20Function%20Calling)).
