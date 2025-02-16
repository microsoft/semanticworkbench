// Copyright (c) Microsoft. All rights reserved.

import { Button, makeStyles, tokens } from '@fluentui/react-components';
import { BookInformation24Regular, ChatSettingsRegular, Dismiss24Regular } from '@fluentui/react-icons';
import { EventSourceMessage } from '@microsoft/fetch-event-source';
import React from 'react';
import { useChatCanvasController } from '../../../libs/useChatCanvasController';
import { useEnvironment } from '../../../libs/useEnvironment';
import { useAppSelector } from '../../../redux/app/hooks';
import { workbenchConversationEvents } from '../../../routes/FrontDoor';
import { TooltipWrapper } from '../../App/TooltipWrapper';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'row',
        gap: tokens.spacingHorizontalM,
    },
});

interface ChatControlsProps {
    conversationId: string;
}

export const ChatControls: React.FC<ChatControlsProps> = (props) => {
    const { conversationId } = props;
    const classes = useClasses();
    const chatCanvasState = useAppSelector((state) => state.chatCanvas);
    const environment = useEnvironment();
    const chatCanvasController = useChatCanvasController();

    React.useEffect(() => {
        const handleFocusEvent = async (event: EventSourceMessage) => {
            const { data } = JSON.parse(event.data);
            chatCanvasController.transitionToState({
                open: true,
                mode: 'assistant',
                selectedAssistantId: data['assistant_id'],
                selectedAssistantStateId: data['state_id'],
            });
        };

        workbenchConversationEvents.addEventListener('assistant.state.focus', handleFocusEvent);

        return () => {
            workbenchConversationEvents.removeEventListener('assistant.state.focus', handleFocusEvent);
        };
    }, [environment, conversationId, chatCanvasController]);

    const handleActivateConversation = () => {
        chatCanvasController.transitionToState({ open: true, mode: 'conversation' });
    };

    const handleActivateAssistant = () => {
        chatCanvasController.transitionToState({ open: true, mode: 'assistant' });
    };

    const handleDismiss = async () => {
        chatCanvasController.transitionToState({ open: false });
    };

    const conversationActive = chatCanvasState.mode === 'conversation' && chatCanvasState.open;
    const assistantActive = chatCanvasState.mode === 'assistant' && chatCanvasState.open;

    return (
        <div className={classes.root}>
            <TooltipWrapper content="Open conversation canvas">
                <Button
                    disabled={conversationActive || chatCanvasController.isTransitioning}
                    icon={<ChatSettingsRegular />}
                    onClick={handleActivateConversation}
                />
            </TooltipWrapper>
            <TooltipWrapper content="Open assistant canvas">
                <Button
                    disabled={assistantActive || chatCanvasController.isTransitioning}
                    icon={<BookInformation24Regular />}
                    onClick={handleActivateAssistant}
                />
            </TooltipWrapper>
            {conversationActive || assistantActive ? (
                <TooltipWrapper content="Close canvas">
                    <Button icon={<Dismiss24Regular />} onClick={handleDismiss} />
                </TooltipWrapper>
            ) : null}
        </div>
    );
};
