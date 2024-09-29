// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, shorthands, Text, tokens } from '@fluentui/react-components';
import React from 'react';
import DynamicIframe from '../../App/DynamicIframe';
import { CodeContentRenderer } from './CodeContentRenderer';
import { MarkdownContentRenderer } from './MarkdownContentRenderer';

const useClasses = makeStyles({
    previewTitle: {
        ...shorthands.margin(tokens.spacingVerticalM, 0, 0, 0),
    },
    previewBox: {
        border: `1px solid ${tokens.colorNeutralStroke1}`,
    },
});

interface HtmlContentRendererProps {
    content: string;
    displayNonHtmlContent?: boolean;
}

export const HtmlContentRenderer: React.FC<HtmlContentRendererProps> = (props) => {
    const { content, displayNonHtmlContent } = props;
    const classes = useClasses();

    // replace all html content with the dynamic iframe
    const parts = content.split(/(```html\n[\s\S]*?\n```)/g);

    return (
        <>
            {parts.map((part, index) => {
                const htmlMatch = part.match(/```html\n([\s\S]*?)\n```/);
                if (htmlMatch) {
                    return (
                        <>
                            {displayNonHtmlContent ? (
                                <>
                                    <CodeContentRenderer key={index} content={htmlMatch[1]} language="html" />
                                    <Text className={classes.previewTitle} weight="semibold">
                                        Preview:
                                    </Text>
                                </>
                            ) : null}
                            <div className={displayNonHtmlContent ? classes.previewBox : ''}>
                                <DynamicIframe key={index} source={htmlMatch[1]} />
                            </div>
                        </>
                    );
                } else {
                    return displayNonHtmlContent ? <MarkdownContentRenderer key={index} content={part} /> : null;
                }
            })}
        </>
    );
};
