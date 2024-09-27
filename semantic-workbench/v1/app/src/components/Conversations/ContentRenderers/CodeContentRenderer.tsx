// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { stackoverflowLight as syntaxHighlighterStyle } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import { CopyButton } from '../../App/CopyButton';

const useClasses = makeStyles({
    root: {
        position: 'relative',
    },
    copy: {
        position: 'absolute',
        right: tokens.spacingHorizontalXS,
        top: tokens.spacingVerticalXS,
    },
});

interface CodeContentRendererProps {
    content: string;
    language: string;
}

export const CodeContentRenderer: React.FC<CodeContentRendererProps> = (props) => {
    const { content, language } = props;
    const classes = useClasses();

    return (
        <div className={classes.root}>
            <div className={classes.copy}>
                <CopyButton data={content}></CopyButton>
            </div>
            <SyntaxHighlighter
                PreTag="div"
                language={language}
                style={syntaxHighlighterStyle}
                wrapLongLines
                // eslint-disable-next-line react/no-children-prop
                children={content}
            />
        </div>
    );
};
