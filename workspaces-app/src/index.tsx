// Importing necessary dependencies
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

// Creating a root element to render the app
const root = document.getElementById("root");

if (root) {
  // Creating a root container for React 18
  const reactRoot = ReactDOM.createRoot(root);

  // Check if React.StrictMode should be disabled
  const disableStrictMode = import.meta.env.VITE_DISABLE_STRICT_MODE === 'true';

  // Log the environment and StrictMode status
  console.log(`Starting app [strict mode: ${disableStrictMode ? 'disabled' : 'enabled'}]`);

  // Rendering the App component with or without StrictMode
  reactRoot.render(disableStrictMode ? <App /> : <React.StrictMode><App /></React.StrictMode>);
} else {
  console.error("Failed to find the root element. Make sure there is an element with id 'root' in your HTML.");
}