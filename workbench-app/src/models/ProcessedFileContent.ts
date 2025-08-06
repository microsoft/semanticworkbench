export interface ProcessedFileContent {
    filename: string;
    content: string;
    content_type: "markdown" | "text" | "image" | "code";
    processing_status: "success" | "error" | "processing" | "not_available";
    error_message?: string;
    metadata?: {
        character_count?: number;
        line_count?: number;
        estimated_tokens?: number;
        mime_type?: string;
        data_uri_size?: number;
        image_dimensions?: {
            width: number;
            height: number;
        };
    };
}