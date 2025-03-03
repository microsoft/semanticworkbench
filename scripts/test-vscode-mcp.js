/**
 * This script tests the VSCode MCP server by connecting to it and executing a command.
 * It can be used to verify that the server is running and that the dynamic URL feature is working.
 * 
 * Usage:
 *   node test-vscode-mcp.js
 */

const { getMcpServerUrl } = require('../workbench-app/src/services/workbench');
const { ClientSession } = require('@modelcontextprotocol/sdk/client');
const { sse_client } = require('@modelcontextprotocol/sdk/client/sse');

/**
 * Test the VSCode MCP server by connecting to it and listing available tools
 */
async function testVscodeMcpServer() {
  const url = getMcpServerUrl();
  console.log(`Testing VSCode MCP server at: ${url}`);

  try {
    // Connect to the server using the SSE transport
    console.log('Connecting to server...');
    const [readStream, writeStream] = await sse_client(url);
    
    // Create a client session
    console.log('Creating client session...');
    const session = new ClientSession(readStream, writeStream);
    
    // Initialize the session
    console.log('Initializing session...');
    await session.initialize();
    
    // List tools to verify connectivity
    console.log('Listing tools...');
    const toolsResult = await session.list_tools();
    console.log(`Found ${toolsResult.tools.length} tools available on the server:`);
    toolsResult.tools.forEach(tool => {
      console.log(`- ${tool.name}: ${tool.description}`);
    });
    
    // Execute a simple VS Code command
    console.log('\nExecuting a test command (vscode.getVersion)...');
    const result = await session.call_tool({
      name: 'execute_vscode_command',
      arguments: {
        command: 'vscode.getVersion'
      }
    });
    
    console.log('Command result:');
    console.log(result.content[0].text);
    
    // Close the session
    await session.close();
    console.log('\nTest completed successfully! The VSCode MCP server is working properly.');
  } catch (error) {
    console.error('Error testing VSCode MCP server:', error);
    process.exit(1);
  }
}

// Run the test
testVscodeMcpServer().catch(console.error);