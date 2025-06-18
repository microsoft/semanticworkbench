// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { Link } from 'react-router-dom';

import { Conversation } from '../../../models/Conversation';
import { ConversationMessage } from '../../../models/ConversationMessage';

import { makeStyles, tokens } from '@fluentui/react-components';
import { ContentRenderer } from './ContentRenderer';
import { ContentSafetyNotice } from './ContentSafetyNotice';

interface InteractMessageProps {
    conversation: Conversation;
    message: ConversationMessage;
}

const useClasses = makeStyles({
    help: {
        backgroundColor: '#e3ecef',
        padding: tokens.spacingVerticalS,
        borderRadius: tokens.borderRadiusMedium,
        marginTop: tokens.spacingVerticalL,
        fontColor: '#707a7d',
        '& h3': {
            marginTop: 0,
            marginBottom: 0,
            fontSize: tokens.fontSizeBase200,
            fontWeight: tokens.fontWeightSemibold,
        },
        '& p': {
            marginTop: 0,
            marginBottom: 0,
            fontSize: tokens.fontSizeBase200,
            lineHeight: tokens.lineHeightBase300,
            fontStyle: 'italic',
        },
    },
});

export const MessageBody: React.FC<InteractMessageProps> = (props) => {
    const { conversation, message } = props;
    const classes = useClasses();
    const body = (
        <>
            <ContentSafetyNotice contentSafety={message.metadata?.['content_safety']} />
            <ContentRenderer conversation={conversation} message={message} />
            {message.metadata?.['help'] && (
                <div className={classes.help}>
                    <h3>Next step?</h3>
                    <p>{message.metadata['help']}</p>
                </div>
            )}
        </>
    );

    if (message.metadata?.href) {
        return <Link to={message.metadata.href}>{body}</Link>;
    }
    return body;
};
