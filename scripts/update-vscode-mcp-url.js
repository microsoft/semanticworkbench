/**
 * This script updates the VSCode MCP server URL in the Semantic Workbench.
 * It can be called with a URL parameter to set the URL, or with 'reset' to restore the default.
 * 
 * Usage:
 *   node update-vscode-mcp-url.js http://127.0.0.1:6010/sse  # Set URL
 *   node update-vscode-mcp-url.js reset                      # Reset to default
 */

// Path to the workbench app
const path = require('path');
const fs = require('fs');

// Get the URL from command line arguments
const args = process.argv.slice(2);
const url = args[0];

if (!url) {
  console.error('Error: No URL or command specified');
  console.error('Usage: node update-vscode-mcp-url.js <url|reset>');
  process.exit(1);
}

// Function to update the URL in the workbench app
function updateMcpServerUrl() {
  try {
    // Import the workbench app
    const workbenchAppPath = path.resolve(__dirname, '..', 'workbench-app');
    
    // Check if we're resetting the URL
    if (url === 'reset') {
      console.log('Resetting VSCode MCP server URL to default');
      // Execute the resetMcpServerUrl function from the workbench app
      const { resetMcpServerUrl } = require(path.join(workbenchAppPath, 'src', 'services', 'workbench'));
      resetMcpServerUrl();
      console.log('VSCode MCP server URL reset to default');
      return;
    }
    
    // Otherwise, set the URL
    console.log(`Setting VSCode MCP server URL to: ${url}`);
    // Execute the setMcpServerUrl function from the workbench app
    const { setMcpServerUrl } = require(path.join(workbenchAppPath, 'src', 'services', 'workbench'));
    setMcpServerUrl(url);
    console.log(`VSCode MCP server URL set to: ${url}`);
  } catch (error) {
    console.error(`Error updating VSCode MCP server URL: ${error.message}`);
    if (error.stack) {
      console.error(error.stack);
    }
    process.exit(1);
  }
}

// Run the update function
updateMcpServerUrl();