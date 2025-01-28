// Importing necessary dependencies
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

// Creating a root element to render the app
const root = document.getElementById("root");

if (root) {
  // Creating a root container for React 18
  const reactRoot = ReactDOM.createRoot(root);

  // Rendering the App component
  reactRoot.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
} else {
  console.error("Failed to find the root element. Make sure there is an element with id 'root' in your HTML.");
}