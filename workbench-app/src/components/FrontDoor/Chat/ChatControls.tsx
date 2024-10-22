// Copyright (c) Microsoft. All rights reserved.

import { Button, makeStyles, tokens, Tooltip } from '@fluentui/react-components';
import { AppsList24Regular, BookInformation24Regular, Dismiss24Regular } from '@fluentui/react-icons';
import { EventSourceMessage } from '@microsoft/fetch-event-source';
import React from 'react';
import { useEnvironment } from '../../../libs/useEnvironment';
import { useInteractCanvasController } from '../../../libs/useInteractCanvasController';
import { WorkbenchEventSource } from '../../../libs/WorkbenchEventSource';
import { useAppSelector } from '../../../redux/app/hooks';

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
    const { interactCanvasState } = useAppSelector((state) => state.app);
    const environment = useEnvironment();
    const interactCanvasController = useInteractCanvasController();

    React.useEffect(() => {
        var workbenchEventSource: WorkbenchEventSource | undefined;

        const handleFocusEvent = async (event: EventSourceMessage) => {
            const { data } = JSON.parse(event.data);
            interactCanvasController.transitionToState({
                open: true,
                mode: 'assistant',
                assistantId: data['assistant_id'],
                assistantStateId: data['state_id'],
            });
        };

        (async () => {
            workbenchEventSource = await WorkbenchEventSource.createOrUpdate(environment.url, conversationId);
            workbenchEventSource.addEventListener('assistant.state.focus', handleFocusEvent);
        })();

        return () => {
            workbenchEventSource?.removeEventListener('assistant.state.focus', handleFocusEvent);
        };
    }, [environment, conversationId, interactCanvasController]);

    const handleActivateConversation = () => {
        interactCanvasController.transitionToState({ open: true, mode: 'conversation' });
    };

    const handleActivateAssistant = () => {
        interactCanvasController.transitionToState({ open: true, mode: 'assistant' });
    };

    const handleDismiss = async () => {
        interactCanvasController.transitionToState({ open: false });
    };

    const conversationActive = interactCanvasState?.mode === 'conversation' && interactCanvasState?.open;
    const assistantActive = interactCanvasState?.mode === 'assistant' && interactCanvasState?.open;

    return (
        <div className={classes.root}>
            <Tooltip content="Open conversation canvas" relationship="label">
                <Button
                    disabled={conversationActive || interactCanvasController.isTransitioning}
                    icon={<AppsList24Regular />}
                    onClick={handleActivateConversation}
                />
            </Tooltip>
            <Tooltip content="Open assistant canvas" relationship="label">
                <Button
                    disabled={assistantActive || interactCanvasController.isTransitioning}
                    icon={<BookInformation24Regular />}
                    onClick={handleActivateAssistant}
                />
            </Tooltip>
            {conversationActive || assistantActive ? (
                <Tooltip content="Close canvas" relationship="label">
                    <Button icon={<Dismiss24Regular />} onClick={handleDismiss} />
                </Tooltip>
            ) : null}
        </div>
    );
};
