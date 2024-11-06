import { makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { Assistant } from '../../../models/Assistant';
import { Conversation } from '../../../models/Conversation';
import { AssistantCanvasList } from '../../Conversations/Canvas/AssistantCanvasList';
import { CanvasDrawer, CanvasDrawerOptions } from './CanvasDrawer';

const useClasses = makeStyles({
    noContent: {
        padding: tokens.spacingHorizontalM,
    },
});

interface AssistantDrawerProps {
    drawerOptions: CanvasDrawerOptions;
    conversation: Conversation;
    conversationAssistants?: Assistant[];
    selectedAssistant?: Assistant;
}

export const AssistantDrawer: React.FC<AssistantDrawerProps> = (props) => {
    const { drawerOptions, conversation, conversationAssistants, selectedAssistant } = props;
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

    const options = React.useMemo(
        () => ({
            ...drawerOptions,
            title,
            resizable: true,
        }),
        [drawerOptions, title],
    );

    return <CanvasDrawer options={options}>{canvasContent}</CanvasDrawer>;
};
