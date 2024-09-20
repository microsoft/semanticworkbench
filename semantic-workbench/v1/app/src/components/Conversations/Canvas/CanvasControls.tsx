// Copyright (c) Microsoft. All rights reserved.

import { Button, makeStyles, shorthands, tokens, Tooltip } from '@fluentui/react-components';
import { Bot24Regular, Chat24Regular, Dismiss24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useAppDispatch, useAppSelector } from '../../../redux/app/hooks';
import { setCanvasState } from '../../../redux/features/app/appSlice';

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

export const CanvasControls: React.FC = () => {
    const classes = useClasses();
    const { canvasState } = useAppSelector((state) => state.app);
    const [disabled, setDisabled] = React.useState(false);
    const dispatch = useAppDispatch();

    const waitForCloseDelayMs = 400;
    const enableDelayMs = 200;

    const setCanvasMode = async (mode: 'conversation' | 'assistant') => {
        // Disable the canvas controls while changing the mode
        setDisabled(true);

        if (canvasState?.open) {
            // Close the canvas before changing the mode
            dispatch(setCanvasState({ open: false }));

            // Wait for the canvas to close before changing the mode
            await new Promise((resolve) => setTimeout(resolve, waitForCloseDelayMs));
        }

        // Restore the canvas controls after a delay
        setTimeout(() => setDisabled(false), enableDelayMs);

        // Open the canvas with the new mode
        dispatch(setCanvasState({ open: true, mode }));
    };

    const handleActivateConversation = () => {
        if (canvasState?.mode === 'conversation' && canvasState?.open) {
            return;
        }
        setCanvasMode('conversation');
    };

    const handleActivateAssistant = () => {
        if (canvasState?.mode === 'assistant' && canvasState?.open) {
            return;
        }
        setCanvasMode('assistant');
    };

    const handleDismiss = async () => {
        if (!canvasState?.open) {
            return;
        }

        // Disable the canvas controls while closing the canvas
        setDisabled(true);

        // Close the canvas
        dispatch(setCanvasState({ open: false }));

        // Wait for the canvas to close before changing the mode
        await new Promise((resolve) => setTimeout(resolve, waitForCloseDelayMs));

        // Restore the canvas controls after the delay
        setDisabled(false);
    };

    return (
        <div className={classes.root}>
            {(canvasState?.mode !== 'conversation' || !canvasState?.open) && (
                <Tooltip content="Open conversation canvas" relationship="label">
                    <Button disabled={disabled} icon={<Chat24Regular />} onClick={handleActivateConversation} />
                </Tooltip>
            )}
            {canvasState?.open && (
                <Tooltip content="Close canvas" relationship="label">
                    <Button disabled={disabled} icon={<Dismiss24Regular />} onClick={handleDismiss} />
                </Tooltip>
            )}
            {(canvasState?.mode !== 'assistant' || !canvasState?.open) && (
                <Tooltip content="Open assistant canvas" relationship="label">
                    <Button disabled={disabled} icon={<Bot24Regular />} onClick={handleActivateAssistant} />
                </Tooltip>
            )}
        </div>
    );
};
