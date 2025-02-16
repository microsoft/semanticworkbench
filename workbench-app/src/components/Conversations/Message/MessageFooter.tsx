// Copyright (c) Microsoft. All rights reserved.

import { AiGeneratedDisclaimer } from '@fluentui-copilot/react-copilot';
import { makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';

import { ConversationMessage } from '../../../models/ConversationMessage';

import { AttachmentSection } from './AttachmentSection';

const useClasses = makeStyles({
    alignForUser: {
        justifyContent: 'flex-end',
        alignItems: 'flex-end',
    },
    footer: {
        display: 'flex',
        color: tokens.colorNeutralForeground3,
        flexDirection: 'row',
        gap: tokens.spacingHorizontalS,
        alignItems: 'center',
        ...shorthands.padding(0, tokens.spacingHorizontalS),
    },
    generated: {
        width: 'fit-content',
        marginTop: tokens.spacingVerticalS,
    },
});

interface MessageFooterProps {
    message: ConversationMessage;
}

export const MessageFooter: React.FC<MessageFooterProps> = (props) => {
    const { message } = props;
    const classes = useClasses();

    const attachments = React.useMemo(() => {
        if (message.filenames && message.filenames.length > 0) {
            return <AttachmentSection filenames={message.filenames} className={classes.alignForUser} />;
        }
        return null;
    }, [message.filenames, classes.alignForUser]);

    const footerContent = React.useMemo(() => {
        if (message.metadata?.['footer_items']) {
            const footerItemsArray = Array.isArray(message.metadata['footer_items'])
                ? message.metadata['footer_items']
                : [message.metadata['footer_items']];
            return (
                <div className={classes.footer}>
                    <AiGeneratedDisclaimer className={classes.generated}>
                        AI-generated content may be incorrect
                    </AiGeneratedDisclaimer>
                    {footerItemsArray.map((item) => (
                        <AiGeneratedDisclaimer key={item} className={classes.generated}>
                            {item}
                        </AiGeneratedDisclaimer>
                    ))}
                </div>
            );
        }
        return null;
    }, [message.metadata, classes.footer, classes.generated]);

    const footer = (
        <>
            {attachments}
            {footerContent}
        </>
    );

    return footer;
};
