import { makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { Assistant } from '../../../models/Assistant';
import { Conversation } from '../../../models/Conversation';
import { AssistantCanvasList } from '../../Conversations/Canvas/AssistantCanvasList';
import { CanvasDrawer } from './CanvasDrawer';

const useClasses = makeStyles({
    drawer: {
        backgroundImage: `linear-gradient(to right, ${tokens.colorNeutralBackground1}, ${tokens.colorBrandBackground2})`,
    },
    drawerOpenInline: {
        width: 'calc(100vw - 500px)',
    },
    drawerOpenOverlay: {
        width: '100%',
    },
    noContent: {
        padding: tokens.spacingHorizontalM,
    },
});

interface AssistantDrawerProps {
    open: boolean;
    mode: 'inline' | 'overlay';
    conversation: Conversation;
    conversationAssistants?: Assistant[];
    selectedAssistant?: Assistant;
}

export const AssistantDrawer: React.FC<AssistantDrawerProps> = (props) => {
    const { open, mode, conversation, conversationAssistants, selectedAssistant } = props;
    const classes = useClasses();

    let title = '';
    if (!conversationAssistants || conversationAssistants.length === 0 || conversationAssistants.length > 1) {
        title = 'Assistants';
    } else {
        title = conversationAssistants[0].name;
    }

    const canvasContent =
        conversationAssistants && conversationAssistants.length > 0 ? (
            <AssistantCanvasList
                selectedAssistant={selectedAssistant}
                conversation={conversation}
                conversationAssistants={conversationAssistants}
            />
        ) : (
            <div className={classes.noContent}>No assistants participating in conversation.</div>
        );

    return (
        <CanvasDrawer
            openClassName={mode === 'inline' ? classes.drawerOpenInline : classes.drawerOpenOverlay}
            className={classes.drawer}
            open={open}
            mode={mode}
            side="right"
            title={title}
        >
            {canvasContent}
        </CanvasDrawer>
    );
};
