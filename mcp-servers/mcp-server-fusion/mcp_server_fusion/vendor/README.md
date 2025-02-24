This directory contains vendored third-party dependencies for the Fusion MCP Add-In.

Dependencies are included here to make the add-in portable and self-contained, since Fusion 360's embedded Python environment does not resolve external dependencies automatically.

Install from project root:

```bash
# from project root directory, where requirements.txt is located
pip install -r requirements.txt --target ./mcp_server_fusion/vendor
```
