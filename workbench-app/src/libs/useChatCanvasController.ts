import debug from 'debug';
import React from 'react';
import { Constants } from '../Constants';
import { useAppDispatch, useAppSelector } from '../redux/app/hooks';
import { setChatCanvasOpen, setChatCanvasState } from '../redux/features/chatCanvas/chatCanvasSlice';
import { ChatCanvasState } from '../redux/features/chatCanvas/ChatCanvasState';

const log = debug(Constants.debug.root).extend('useCanvasController');

export const useChatCanvasController = () => {
    const chatCanvasState = useAppSelector((state) => state.chatCanvas);
    const [isTransitioning, setIsTransitioning] = React.useState(false);
    const dispatch = useAppDispatch();

    const closingTransitionDelayMs = 400;
    const openingTransitionDelayMs = 200;

    const chooseTransitionType = React.useCallback(
        (currentCanvasState: ChatCanvasState, fullTargetCanvasState: ChatCanvasState) => {
            if (!currentCanvasState.open && fullTargetCanvasState.open) {
                return 'open';
            }
            if (currentCanvasState.open && !fullTargetCanvasState.open) {
                return 'close';
            }
            if (currentCanvasState.mode !== fullTargetCanvasState.mode) {
                return 'mode';
            }
            return 'none';
        },
        [],
    );

    const transitionOpenToClose = React.useCallback(async () => {
        log(`canvas closing with transition of ${closingTransitionDelayMs}ms`);

        // close the canvas
        dispatch(setChatCanvasOpen(false));

        // wait for the canvas to close before indicating that we are no longer transitioning
        await new Promise((resolve) => setTimeout(resolve, closingTransitionDelayMs));
        log('canvas closed');
    }, [dispatch]);

    const transitionCloseToOpen = React.useCallback(
        async (fullTargetCanvasState: ChatCanvasState) => {
            log(`canvas opening with transition of ${openingTransitionDelayMs}ms`);

            // open the canvas with the new mode
            dispatch(setChatCanvasState(fullTargetCanvasState));

            // wait for the canvas to open before indicating that we are no longer transitioning
            await new Promise((resolve) => setTimeout(resolve, openingTransitionDelayMs));

            log(`canvas opened with mode ${fullTargetCanvasState.mode}`);

            if (fullTargetCanvasState.mode === 'assistant') {
                log(
                    `assistant state: ${fullTargetCanvasState.selectedAssistantStateId} [assistant: ${fullTargetCanvasState.selectedAssistantId}]`,
                );
            }
        },
        [dispatch],
    );

    const transitionOpenToNewMode = React.useCallback(
        async (fullTargetCanvasState: ChatCanvasState) => {
            log('canvas changing mode while open');
            await transitionOpenToClose();
            await transitionCloseToOpen(fullTargetCanvasState);
        },
        [transitionCloseToOpen, transitionOpenToClose],
    );

    const setState = React.useCallback(
        (targetCanvasState: Partial<ChatCanvasState>) => {
            dispatch(setChatCanvasState({ ...chatCanvasState, ...targetCanvasState }));
        },
        [dispatch, chatCanvasState],
    );

    const transitionToState = React.useCallback(
        async (targetCanvasState: Partial<ChatCanvasState>) => {
            //
            // we should always set the isTransitioning state to true before we start any transitions
            // so that we can disable various UX elements that should not be interacted with
            // while the canvas is transitioning
            //
            // possible transitions:
            //
            // 1. open -> close:
            //   - update state to close the canvas
            //   - wait for the close delay
            //   - set isTransitioning to false
            //
            // 2. close -> open with mode selection
            //   - update state to open directly to the desired mode
            //   - wait for the open delay
            //   - set isTransitioning to false
            //
            // 3. mode change while open
            //   - close the canvas without any other state changes first
            //   - wait for the close delay
            //   - update state to open directly to the desired mode
            //   - wait for the open delay
            //   - set isTransitioning to false
            //

            // indicate that we are transitioning so that we can disable the canvas
            setIsTransitioning(true);

            // determine the type of transition that we need to perform
            const transitionType = chooseTransitionType(chatCanvasState, {
                ...chatCanvasState,
                ...targetCanvasState,
            });

            // perform the transition
            switch (transitionType) {
                case 'open':
                    await transitionOpenToClose();
                    await transitionCloseToOpen({ ...chatCanvasState, ...targetCanvasState });
                    break;
                case 'close':
                    await transitionOpenToClose();
                    break;
                case 'mode':
                    await transitionOpenToNewMode({ ...chatCanvasState, ...targetCanvasState });
                    break;
                case 'none':
                    // no transition needed, just update the state
                    dispatch(setChatCanvasState({ ...chatCanvasState, ...targetCanvasState }));
                    setIsTransitioning(false);
                    break;
            }

            // ensure that we are not claiming to be transitioning anymore
            setIsTransitioning(false);
        },
        [
            chooseTransitionType,
            dispatch,
            chatCanvasState,
            transitionCloseToOpen,
            transitionOpenToClose,
            transitionOpenToNewMode,
        ],
    );

    return { chatCanvasState, isTransitioning, setState, transitionToState };
};
