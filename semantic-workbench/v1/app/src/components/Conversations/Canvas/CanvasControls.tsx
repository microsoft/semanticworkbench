// Copyright (c) Microsoft. All rights reserved.

import { Button, makeStyles, shorthands, tokens, Tooltip } from '@fluentui/react-components';
import { Bot24Regular, Chat24Regular, Dismiss24Regular } from '@fluentui/react-icons';
import { EventSourceMessage } from '@microsoft/fetch-event-source';
import React from 'react';
import { useCanvasController } from '../../../libs/useCanvasController';
import { useEnvironment } from '../../../libs/useEnvironment';
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
    const { conversationCanvasState } = useAppSelector((state) => state.app);
    const environment = useEnvironment();
    const canvasController = useCanvasController();

    React.useEffect(() => {
        var workbenchEventSource: WorkbenchEventSource | undefined;

        const handleFocusEvent = async (event: EventSourceMessage) => {
            const { data } = JSON.parse(event.data);
            canvasController.transitionToState({
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
    }, [environment, conversationId, canvasController]);

    const handleActivateConversation = () => {
        canvasController.transitionToState({ open: true, mode: 'conversation' });
    };

    const handleActivateAssistant = () => {
        canvasController.transitionToState({ open: true, mode: 'assistant' });
    };

    const handleDismiss = async () => {
        canvasController.transitionToState({ open: false });
    };

    return (
        <div className={classes.root}>
            {(conversationCanvasState?.mode !== 'conversation' || !conversationCanvasState?.open) && (
                <Tooltip content="Open conversation canvas" relationship="label">
                    <Button
                        disabled={canvasController.isTransitioning}
                        icon={<Chat24Regular />}
                        onClick={handleActivateConversation}
                    />
                </Tooltip>
            )}
            {conversationCanvasState?.open && (
                <Tooltip content="Close canvas" relationship="label">
                    <Button
                        disabled={canvasController.isTransitioning}
                        icon={<Dismiss24Regular />}
                        onClick={handleDismiss}
                    />
                </Tooltip>
            )}
            {(conversationCanvasState?.mode !== 'assistant' || !conversationCanvasState?.open) && (
                <Tooltip content="Open assistant canvas" relationship="label">
                    <Button
                        disabled={canvasController.isTransitioning}
                        icon={<Bot24Regular />}
                        onClick={handleActivateAssistant}
                    />
                </Tooltip>
            )}
        </div>
    );
};
