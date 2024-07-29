// Copyright (c) Microsoft. All rights reserved.

import { makeStyles } from '@fluentui/react-components';
import React from 'react';
import Markdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import remarkGfm from 'remark-gfm';
import { CodeContentRenderer } from './CodeContentRenderer';
import { MermaidContentRenderer } from './MermaidContentRenderer';
import { MusicABCContentRenderer } from './MusicABCContentRenderer';

const useClasses = makeStyles({
    root: {
        // when this is first child of another griffel component
        '& :first-child': {
            marginTop: 0,
        },
        // when this is last child of another griffel component
        '& :last-child': {
            marginBottom: 0,
        },
    },
});

interface MarkdownContentRendererProps {
    content: string;
}

export const MarkdownContentRenderer: React.FC<MarkdownContentRendererProps> = (props) => {
    const { content } = props;
    const classes = useClasses();

    let cleanedContent = content;
    // strip ```markdown & ``` from the beginning and end of the content if exists
    if (content.startsWith('```markdown') && content.endsWith('```')) {
        cleanedContent = content.substring(11, content.length - 3);
    }

    return (
        <Markdown
            className={classes.root}
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeRaw]}
            components={{
                code(props) {
                    // TODO: determine if we should fix these eslint-disable lines
                    // eslint-disable-next-line react/prop-types
                    const { children, className, node, ...rest } = props;
                    const match = /language-(\w+)/.exec(className || '');

                    if (match) {
                        const language = match[1];
                        const content = String(children).replace(/\n$/, '');

                        if (language === 'mermaid') {
                            return <MermaidContentRenderer content={content} clickToZoom />;
                        }

                        if (language === 'abc') {
                            return <MusicABCContentRenderer content={content} />;
                        }

                        return <CodeContentRenderer content={content} language={language} />;
                    }

                    // no language specified, just render the code
                    return (
                        // eslint-disable-next-line react/jsx-props-no-spreading
                        <code {...rest} className={className}>
                            {children}
                        </code>
                    );
                },
            }}
        >
            {cleanedContent}
        </Markdown>
    );
};
