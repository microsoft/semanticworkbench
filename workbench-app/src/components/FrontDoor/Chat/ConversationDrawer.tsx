import { makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { Conversation } from '../../../models/Conversation';
import { ConversationFile } from '../../../models/ConversationFile';
import { ConversationParticipant } from '../../../models/ConversationParticipant';
import { ConversationCanvas } from '../../Conversations/Canvas/ConversationCanvas';
import { DrawerControl } from './DrawerControl';

const useClasses = makeStyles({
    drawerTitle: {
        marginTop: tokens.spacingVerticalXL,
    },
    // drawerOpenInline: {
    //     width: 'min(50vw, 400px)',
    // },
    // drawerOpenOverlay: {
    //     width: '100%',
    // },
});

interface ConversationDrawerProps {
    open: boolean;
    mode: 'inline' | 'overlay';
    readOnly: boolean;
    conversation: Conversation;
    conversationParticipants: ConversationParticipant[];
    conversationFiles: ConversationFile[];
    preventAssistantModifyOnParticipantIds?: string[];
}

export const ConversationDrawer: React.FC<ConversationDrawerProps> = (props) => {
    const {
        open,
        mode,
        readOnly,
        conversation,
        conversationParticipants,
        conversationFiles,
        preventAssistantModifyOnParticipantIds,
    } = props;
    const classes = useClasses();

    return (
        <DrawerControl
            classNames={{
                title: classes.drawerTitle,
            }}
            size="small"
            open={open}
            mode={mode}
            side="right"
            title="Conversation"
        >
            <ConversationCanvas
                readOnly={readOnly}
                conversation={conversation}
                conversationParticipants={conversationParticipants}
                conversationFiles={conversationFiles}
                preventAssistantModifyOnParticipantIds={preventAssistantModifyOnParticipantIds}
            />
        </DrawerControl>
    );
};
