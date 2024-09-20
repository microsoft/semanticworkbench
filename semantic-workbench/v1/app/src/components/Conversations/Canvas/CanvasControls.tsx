// Copyright (c) Microsoft. All rights reserved.

import { Button, makeStyles, shorthands, tokens, Tooltip } from '@fluentui/react-components';
import { Bot24Regular, Chat24Regular, Dismiss24Regular } from '@fluentui/react-icons';
import { EventSourceMessage } from '@microsoft/fetch-event-source';
import React from 'react';
import { useEnvironment } from '../../../libs/useEnvironment';
import { useInteractCanvasController } from '../../../libs/useInteractCanvasController';
import { WorkbenchEventSource } from '../../../libs/WorkbenchEventSource';
import { useAppSelector } from '../../../redux/app/hooks';

const useClasses = makeStyles({
    root: {
        zIndex: 1000,
        position: 'absolute',
        top: 0,
        right: 0,
        display: 'flex',
        flexDirection: 'row',
        gap: tokens.spacingHorizontalM,
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
    },
});

interface CanvasControlsProps {
    conversationId: string;
}

export const CanvasControls: React.FC<CanvasControlsProps> = (props) => {
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

    return (
        <div className={classes.root}>
            {(interactCanvasState?.mode !== 'conversation' || !interactCanvasState?.open) && (
                <Tooltip content="Open conversation canvas" relationship="label">
                    <Button
                        disabled={interactCanvasController.isTransitioning}
                        icon={<Chat24Regular />}
                        onClick={handleActivateConversation}
                    />
                </Tooltip>
            )}
            {interactCanvasState?.open && (
                <Tooltip content="Close canvas" relationship="label">
                    <Button
                        disabled={interactCanvasController.isTransitioning}
                        icon={<Dismiss24Regular />}
                        onClick={handleDismiss}
                    />
                </Tooltip>
            )}
            {(interactCanvasState?.mode !== 'assistant' || !interactCanvasState?.open) && (
                <Tooltip
                    content={
                        interactCanvasState?.assistantId
                            ? 'Open assistant canvas'
                            : 'No assistants available in conversation'
                    }
                    relationship="label"
                >
                    <Button
                        disabled={interactCanvasController.isTransitioning || !interactCanvasState?.assistantId}
                        icon={<Bot24Regular />}
                        onClick={handleActivateAssistant}
                    />
                </Tooltip>
            )}
        </div>
    );
};
