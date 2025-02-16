export {};

// Allow static build of React code to access env vars
// SEE https://create-react-app.dev/docs/title-and-meta-tags/#injecting-data-from-the-server-into-the-page
declare global {
    interface Window {
        VITE_SEMANTIC_WORKBENCH_SERVICE_URL?: string;
    }
}
