import debug from 'debug';
import React from 'react';
import { Constants } from '../Constants';
import { ConversationCanvasState } from '../models/ConversationCanvasState';
import { useAppDispatch, useAppSelector } from '../redux/app/hooks';
import { setConversationCanvasState } from '../redux/features/app/appSlice';

const log = debug(Constants.debug.root).extend('useCanvasController');

export const useCanvasController = () => {
    const { conversationCanvasState } = useAppSelector((state) => state.app);
    const [isTransitioning, setIsTransitioning] = React.useState(false);
    const dispatch = useAppDispatch();

    const waitForCloseDelayMs = 400;
    const enableDelayMs = 200;

    const transitionToState = React.useCallback(
        async (targetCanvasState: Partial<ConversationCanvasState>, skipAnimations: boolean = false) => {
            // indicate that we are transitioning so that we can disable the canvas
            // controls or prevent multiple transitions
            setIsTransitioning(true);

            if (!conversationCanvasState) {
                // open the canvas with the new mode
                log('current state not set, opening canvas with new mode', targetCanvasState.mode);
                dispatch(
                    setConversationCanvasState({ open: true, mode: targetCanvasState.mode, ...targetCanvasState }),
                );
                // ensure that we are not claiming to be transitioning
                setIsTransitioning(false);
                return;
            }

            if (targetCanvasState.open === false) {
                if (!conversationCanvasState.open) {
                    return;
                }

                if (skipAnimations) {
                    log('canvas closing with no transition');

                    // close the canvas
                    dispatch(setConversationCanvasState({ open: false }));

                    // ensure that we are not claiming to be transitioning
                    setIsTransitioning(false);
                } else {
                    log(`canvas closing with transition of ${waitForCloseDelayMs}ms`);

                    // indicate that we are transitioning so that we can disable the canvas
                    setIsTransitioning(true);

                    // close the canvas
                    dispatch(setConversationCanvasState({ open: false }));

                    // wait for the canvas to close before indicating that we are no longer transitioning
                    await new Promise((resolve) => setTimeout(resolve, waitForCloseDelayMs));
                    log('canvas closed');

                    // indicate that we are no longer transitioning
                    setIsTransitioning(false);
                }
            }

            if (targetCanvasState.open === true) {
                if (conversationCanvasState.open && conversationCanvasState.mode === targetCanvasState.mode) {
                    log('canvas already open with mode', targetCanvasState.mode);
                    setIsTransitioning(false);
                    return;
                }

                if (skipAnimations) {
                    log('canvas opening with no transition');

                    // open the canvas with the new mode
                    dispatch(
                        setConversationCanvasState({ open: true, mode: targetCanvasState.mode, ...targetCanvasState }),
                    );

                    // ensure that we are not claiming to be transitioning
                    setIsTransitioning(false);
                } else {
                    log(`canvas opening with transition of ${enableDelayMs}ms`);

                    // indicate that we are transitioning so that we can disable the canvas
                    setIsTransitioning(true);

                    // close the canvas if it is open to avoid weird animations
                    if (conversationCanvasState.open) {
                        // close the canvas
                        dispatch(setConversationCanvasState({ open: false }));

                        // wait for the canvas to close before changing the mode
                        await new Promise((resolve) => setTimeout(resolve, waitForCloseDelayMs));
                    }

                    // open the canvas with the new mode
                    dispatch(
                        setConversationCanvasState({ open: true, mode: targetCanvasState.mode, ...targetCanvasState }),
                    );

                    // wait for the canvas to open before indicating that we are no longer transitioning
                    setTimeout(() => {
                        setIsTransitioning(false);
                        log('canvas opened');
                    }, enableDelayMs);
                }
            }
        },
        [dispatch, conversationCanvasState],
    );

    return { conversationCanvasState, isTransitioning, transitionToState: transitionToState };
};
