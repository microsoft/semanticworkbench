/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_DISABLE_STRICT_MODE?: string;
  // Add other environment variables here if needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
