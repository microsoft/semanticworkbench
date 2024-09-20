// Copyright (c) Microsoft. All rights reserved.

import {
    DrawerHeader,
    DrawerHeaderTitle,
    InlineDrawer,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { Assistant } from '../../../models/Assistant';
import { Conversation } from '../../../models/Conversation';
import { ConversationFile } from '../../../models/ConversationFile';
import { ConversationParticipant } from '../../../models/ConversationParticipant';
import { useAppSelector } from '../../../redux/app/hooks';
import { AssistantCanvasList } from './AssistantCanvasList';
import { ConversationCanvas } from './ConversationCanvas';

const useClasses = makeStyles({
    drawer: {
        height: '100%',
    },
    drawerContent: {
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'auto',
        ...shorthands.padding(0, tokens.spacingHorizontalM, tokens.spacingVerticalM),
        boxSizing: 'border-box',
        '::-webkit-scrollbar-track': {
            backgroundColor: tokens.colorNeutralBackground1,
        },
        '::-webkit-scrollbar-thumb': {
            backgroundColor: tokens.colorNeutralStencil1Alpha,
        },
    },
});

interface GeneralCanvasProps {
    conversationAssistants: Assistant[];
    conversationParticipants: ConversationParticipant[];
    conversationFiles: ConversationFile[];
    conversation: Conversation;
    preventAssistantModifyOnParticipantIds?: string[];
}

export const GeneralCanvas: React.FC<GeneralCanvasProps> = (props) => {
    const {
        conversationAssistants,
        conversationParticipants,
        conversationFiles,
        conversation,
        preventAssistantModifyOnParticipantIds,
    } = props;
    const classes = useClasses();
    const { open, mode } = useAppSelector((state) => state.app).canvasState || {};

    return (
        <>
            <InlineDrawer
                className={classes.drawer}
                open={open && mode === 'conversation'}
                position="end"
                size="medium"
            >
                <DrawerHeader>
                    <DrawerHeaderTitle>Conversation</DrawerHeaderTitle>
                </DrawerHeader>
                <div className={classes.drawerContent}>
                    <ConversationCanvas
                        conversation={conversation}
                        conversationParticipants={conversationParticipants}
                        conversationFiles={conversationFiles}
                        conversationAssistants={conversationAssistants}
                        preventAssistantModifyOnParticipantIds={preventAssistantModifyOnParticipantIds}
                    />
                </div>
            </InlineDrawer>
            <InlineDrawer className={classes.drawer} open={open && mode === 'assistant'} position="end" size="large">
                <DrawerHeader>
                    <DrawerHeaderTitle>Assistants</DrawerHeaderTitle>
                </DrawerHeader>
                <div className={classes.drawerContent}>
                    <AssistantCanvasList conversation={conversation} conversationAssistants={conversationAssistants} />
                </div>
            </InlineDrawer>
        </>
    );
};
