// Copyright (c) Microsoft. All rights reserved.

import { Text, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import { EventSourceMessage } from '@microsoft/fetch-event-source';
import {} from '@rjsf/core';
import debug from 'debug';
import React from 'react';
import { Constants } from '../../../Constants';
import { WorkbenchEventSource } from '../../../libs/WorkbenchEventSource';
import { useEnvironment } from '../../../libs/useEnvironment';
import { Conversation } from '../../../models/Conversation';
import { ConversationFile } from '../../../models/ConversationFile';

const log = debug(Constants.debug.root).extend('ConversationFileViewer');

const useClasses = makeStyles({
    root: {
        display: 'grid',
        gridTemplateRows: 'auto 1fr',
        height: '100%',
    },
    header: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
        ...shorthands.padding(tokens.spacingVerticalM),
    },
    body: {
        display: 'flex',
        flexDirection: 'column',
        overflow: 'auto',
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
    },
    form: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
});

interface ConversationFileViewerProps {
    conversation: Conversation;
    conversationFile: ConversationFile;
}

export const ConversationFileViewer: React.FC<ConversationFileViewerProps> = (props) => {
    const { conversation, conversationFile } = props;
    const classes = useClasses();

    const environment = useEnvironment();

    React.useEffect(() => {
        var workbenchEventSource: WorkbenchEventSource | undefined;

        const handleEvent = (event: EventSourceMessage) => {
            const { data } = JSON.parse(event.data);
            if (conversation.id !== data['conversation_id']) return;
            log('Received event', data);
        };

        (async () => {
            workbenchEventSource = await WorkbenchEventSource.createOrUpdate(environment.url, conversation.id);
            workbenchEventSource.addEventListener('conversation.file.updated', handleEvent);
        })();

        return () => {
            workbenchEventSource?.removeEventListener('assistant.state.updated', handleEvent);
        };
    }, [conversation.id, environment.url]);

    return (
        <div className={classes.root}>
            <div className={classes.header}>
                <Text>{conversationFile.name}</Text>
            </div>
            <div className={classes.body}></div>
        </div>
    );
};
