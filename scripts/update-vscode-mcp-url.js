#!/usr/bin/env node

/**
 * This script updates the VSCode MCP server URL in the assistant configuration files.
 * It reads the configuration files from ~/assistants/<assistant-project>/.data/assistants/<assistant_instance_id>/config.json
 * and updates the VSCode MCP server URL with the value from the global variable.
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

// Get the VSCode MCP server URL
const getVSCodeMcpServerUrl = () => {
  // Check if we're in a Node.js environment with access to the global variable
  if (typeof global !== 'undefined' && global.__VSCODE_MCP_SERVER_URL) {
    return global.__VSCODE_MCP_SERVER_URL;
  }
  
  // Try to connect to the VSCode MCP server directly
  try {
    // We can't do a synchronous HTTP request in Node.js easily,
    // so we'll just return the known URL if the server is likely running
    const http = require('http');
    const knownUrl = 'http://127.0.0.1:6010/sse';
    
    // Check if the port is in use (this is a simple check)
    const net = require('net');
    const socket = new net.Socket();
    
    let isPortInUse = false;
    
    // Try to connect to the port
    socket.on('connect', () => {
      isPortInUse = true;
      socket.destroy();
    });
    
    socket.on('error', (err) => {
      if (err.code === 'ECONNREFUSED') {
        isPortInUse = false;
      }
      socket.destroy();
    });
    
    socket.connect(6010, '127.0.0.1');
    
    // Use a synchronous approach for simplicity
    let connected = false;
    try {
      // Try to connect to the port
      const { execSync } = require('child_process');
      const result = execSync('nc -z 127.0.0.1 6010 2>/dev/null || echo "failed"').toString().trim();
      connected = result !== 'failed';
    } catch (error) {
      console.error('Error checking port:', error);
      connected = false;
    }
    
    if (connected) {
      console.log('Port 6010 is in use, assuming VSCode MCP server is running');
      return knownUrl;
    }
  } catch (error) {
    console.error('Error checking if VSCode MCP server is running:', error);
  }
  
  // If we can't determine if the server is running, use a hardcoded URL
  // This is a fallback for testing
  return 'http://127.0.0.1:6010/sse';
};

// Update the VSCode MCP server URL in the assistant configuration
const updateVSCodeMcpServerUrl = (config) => {
  // Get the dynamic VSCode MCP server URL
  const dynamicUrl = getVSCodeMcpServerUrl();
  
  if (!dynamicUrl) {
    console.log('VSCode MCP server URL not found. No changes made.');
    return config;
  }
  
  // Make a deep copy of the configuration to avoid modifying the original
  const updatedConfig = JSON.parse(JSON.stringify(config));
  
  // Check if the configuration has the extensions_config.tools.mcp_servers property
  if (
    updatedConfig?.extensions_config?.tools?.mcp_servers &&
    Array.isArray(updatedConfig.extensions_config.tools.mcp_servers)
  ) {
    // Find the VSCode MCP server in the configuration
    const vscodeServerIndex = updatedConfig.extensions_config.tools.mcp_servers.findIndex(
      (server) => server.key === 'vscode'
    );
    
    if (vscodeServerIndex !== -1) {
      // Update the command with the dynamic URL
      const oldUrl = updatedConfig.extensions_config.tools.mcp_servers[vscodeServerIndex].command;
      updatedConfig.extensions_config.tools.mcp_servers[vscodeServerIndex].command = dynamicUrl;
      console.log(`Updated VSCode MCP server URL from ${oldUrl} to ${dynamicUrl}`);
    } else {
      console.log('VSCode MCP server not found in configuration. No changes made.');
    }
  } else {
    console.log('MCP servers configuration not found. No changes made.');
  }
  
  return updatedConfig;
};

// Find all assistant configuration files
const findAssistantConfigFiles = () => {
  const configFiles = [];
  const searchPaths = [
    // Standard location
    path.join(os.homedir(), 'assistants'),
    // Workspace location
    '/workspaces/semanticworkbench/assistants'
  ];
  
  for (const basePath of searchPaths) {
    // Check if the directory exists
    if (!fs.existsSync(basePath)) {
      console.log(`Directory not found: ${basePath}`);
      continue;
    }
    
    console.log(`Searching for assistant configurations in: ${basePath}`);
    
    // Get all assistant projects
    const assistantProjects = fs.readdirSync(basePath);
    
    for (const project of assistantProjects) {
      const projectDir = path.join(basePath, project);
      
      // Skip if not a directory
      if (!fs.statSync(projectDir).isDirectory()) {
        continue;
      }
      
      console.log(`Checking project: ${project}`);
      
      // Check for config.json directly in the project directory
      const directConfigFile = path.join(projectDir, 'config.json');
      if (fs.existsSync(directConfigFile)) {
        console.log(`Found config file: ${directConfigFile}`);
        configFiles.push(directConfigFile);
      }
      
      // Check in .data/assistants directory
      const dataDir = path.join(projectDir, '.data', 'assistants');
      if (fs.existsSync(dataDir)) {
        // Get all assistant instance IDs
        const assistantIds = fs.readdirSync(dataDir);
        
        for (const id of assistantIds) {
          const idDir = path.join(dataDir, id);
          
          // Skip if not a directory
          if (!fs.statSync(idDir).isDirectory()) {
            continue;
          }
          
          const configFile = path.join(idDir, 'config.json');
          
          // Check if the config file exists
          if (fs.existsSync(configFile)) {
            console.log(`Found config file: ${configFile}`);
            configFiles.push(configFile);
          }
        }
      }
    }
  }
  
  return configFiles;
};

// Update all assistant configuration files
const updateAllAssistantConfigFiles = () => {
  const configFiles = findAssistantConfigFiles();
  
  if (configFiles.length === 0) {
    console.log('No assistant configuration files found.');
    return;
  }
  
  console.log(`Found ${configFiles.length} assistant configuration files.`);
  
  for (const file of configFiles) {
    try {
      // Read the configuration file
      const config = JSON.parse(fs.readFileSync(file, 'utf8'));
      
      // Update the VSCode MCP server URL
      const updatedConfig = updateVSCodeMcpServerUrl(config);
      
      // Write the updated configuration file
      fs.writeFileSync(file, JSON.stringify(updatedConfig, null, 2));
      
      console.log(`Updated configuration file: ${file}`);
    } catch (error) {
      console.error(`Error updating configuration file ${file}:`, error);
    }
  }
};

// Check if the global variable is set
console.log('Current VSCode MCP server URL:', getVSCodeMcpServerUrl() || 'Not set');

// Run the script
updateAllAssistantConfigFiles();
