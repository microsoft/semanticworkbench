// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { CodeContentRenderer } from './CodeContentRenderer';
import { HtmlContentRenderer } from './HtmlContentRenderer';
import { JsonSchemaContentRenderer } from './JsonSchemaContentRenderer';
import { MarkdownContentRenderer } from './MarkdownContentRenderer';

interface ContentRenderProps {
    content: string;
    contentType?: string;
    metadata?: Record<string, unknown>;
    onSubmit?: (data: string) => Promise<void>;
}

export const ContentRenderer: React.FC<ContentRenderProps> = (props) => {
    const { content, contentType, metadata, onSubmit } = props;

    if (contentType === 'application/json') {
        if (metadata?.json_schema) {
            return <JsonSchemaContentRenderer content={content} metadata={metadata} onSubmit={onSubmit} />;
        }
        return <CodeContentRenderer content={content} language="json" />;
    }

    if (content.includes('```html')) {
        return <HtmlContentRenderer content={content} displayNonHtmlContent />;
    }

    // Default to markdown
    return <MarkdownContentRenderer content={content} />;
};
