import { makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { Assistant } from '../../../models/Assistant';
import { Conversation } from '../../../models/Conversation';
import { ConversationFile } from '../../../models/ConversationFile';
import { ConversationParticipant } from '../../../models/ConversationParticipant';
import { CanvasDrawer } from './CanvasDrawer';
import { ConversationCanvas } from './ConversationCanvas';

const useClasses = makeStyles({
    drawer: {
        height: '100%',
        backgroundImage: `linear-gradient(to right, ${tokens.colorNeutralBackground1}, ${tokens.colorBrandBackground2})`,
    },
    drawerOpenInline: {
        width: 'min(50vw, 500px)',
    },
    drawerOpenOverlay: {
        width: '100%',
    },
});

interface ConversationDrawerProps {
    open: boolean;
    mode: 'inline' | 'overlay';
    readOnly: boolean;
    conversation: Conversation;
    conversationParticipants: ConversationParticipant[];
    conversationFiles: ConversationFile[];
    conversationAssistants: Assistant[];
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
        conversationAssistants,
        preventAssistantModifyOnParticipantIds,
    } = props;
    const classes = useClasses();

    return (
        <CanvasDrawer
            openClassName={mode === 'inline' ? classes.drawerOpenInline : classes.drawerOpenOverlay}
            className={classes.drawer}
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
                conversationAssistants={conversationAssistants}
                preventAssistantModifyOnParticipantIds={preventAssistantModifyOnParticipantIds}
            />
        </CanvasDrawer>
    );
};
