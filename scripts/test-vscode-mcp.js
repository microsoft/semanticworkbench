#!/usr/bin/env node

/**
 * This script tests if the VSCode MCP server is accessible.
 */

const http = require('http');

// Try to connect to the VSCode MCP server
const url = 'http://127.0.0.1:6010/sse';
console.log(`Testing connection to ${url}...`);

const req = http.get(url, (res) => {
  console.log(`Status code: ${res.statusCode}`);
  console.log(`Headers: ${JSON.stringify(res.headers)}`);
  
  // If we get a response, the server is running
  console.log('VSCode MCP server is accessible!');
  
  // Set the global variable manually for testing
  global.__VSCODE_MCP_SERVER_URL = url;
  console.log('Set global.__VSCODE_MCP_SERVER_URL to:', global.__VSCODE_MCP_SERVER_URL);
  
  // Run the update script
  const { execSync } = require('child_process');
  try {
    console.log('Running update script...');
    const output = execSync('node /workspaces/semanticworkbench/scripts/update-vscode-mcp-url.js');
    console.log(output.toString());
  } catch (error) {
    console.error('Error running update script:', error);
  }
  
  // End the request
  req.end();
});

req.on('error', (error) => {
  console.error(`Error connecting to VSCode MCP server: ${error.message}`);
});

// Set a timeout
req.setTimeout(5000, () => {
  console.error('Connection timed out');
  req.destroy();
});
