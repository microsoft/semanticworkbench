// Copyright (c) Microsoft. All rights reserved.

import React from 'react';

interface HtmlContentRendererProps {
    content: string;
}

export const HtmlContentRenderer: React.FC<HtmlContentRendererProps> = (props) => {
    const { content } = props;

    // get content from within "other stuff...\n```html\n<HTML/>\n```\nmore stuff..."
    const htmlContent = content.match(/```html\n([\s\S]*?)\n```/)?.[1] || '';

    // TODO: support additional content, but maybe hide it if a metadata flag is set
    // // get the rest of the content
    // const restOfContent = content.replace(/```html\n([\s\S]*?)\n```/, '');

    return (
        <iframe
            title="HtmlContentRenderer"
            srcDoc={htmlContent}
            style={{ width: '100%', height: '100%', border: 'none' }}
        />
    );
};
