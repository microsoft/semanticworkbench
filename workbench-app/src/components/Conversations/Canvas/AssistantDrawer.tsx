import { makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { Assistant } from '../../../models/Assistant';
import { Conversation } from '../../../models/Conversation';
import { AssistantCanvasList } from './AssistantCanvasList';
import { CanvasDrawer } from './CanvasDrawer';

const useClasses = makeStyles({
    drawer: {
        height: '100%',
        backgroundImage: `linear-gradient(to right, ${tokens.colorNeutralBackground1}, ${tokens.colorBrandBackground2})`,
    },
    drawerOpenInline: {
        width: 'calc(200vw - 300px)',
    },
    drawerOpenOverlay: {
        width: '100%',
    },
});

interface AssistantDrawerProps {
    open: boolean;
    mode: 'inline' | 'overlay';
    conversation: Conversation;
    conversationAssistants: Assistant[];
    selectedAssistant?: Assistant;
}

export const AssistantDrawer: React.FC<AssistantDrawerProps> = (props) => {
    const { open, mode, conversation, conversationAssistants, selectedAssistant } = props;
    const classes = useClasses();

    return (
        <CanvasDrawer
            openClassName={mode === 'inline' ? classes.drawerOpenInline : classes.drawerOpenOverlay}
            className={classes.drawer}
            open={open}
            mode={mode}
            side="right"
            title="Assistants"
        >
            {selectedAssistant ? (
                <AssistantCanvasList
                    selectedAssistant={selectedAssistant}
                    conversation={conversation}
                    conversationAssistants={conversationAssistants}
                />
            ) : (
                'No assistant selected.'
            )}
        </CanvasDrawer>
    );
};
