import debug from 'debug';
import React from 'react';
import { Constants } from '../Constants';
import { InteractCanvasState } from '../models/InteractCanvasState';
import { useAppDispatch, useAppSelector } from '../redux/app/hooks';
import { setInteractCanvasState } from '../redux/features/app/appSlice';

const log = debug(Constants.debug.root).extend('useCanvasController');

export const useInteractCanvasController = () => {
    const { interactCanvasState } = useAppSelector((state) => state.app);
    const [isTransitioning, setIsTransitioning] = React.useState(false);
    const dispatch = useAppDispatch();

    const closingTransitionDelayMs = 400;
    const openingTransitionDelayMs = 200;

    const chooseTransitionType = React.useCallback(
        (currentCanvasState: InteractCanvasState, fullTargetCanvasState: InteractCanvasState) => {
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
        dispatch(setInteractCanvasState({ open: false }));

        // wait for the canvas to close before indicating that we are no longer transitioning
        await new Promise((resolve) => setTimeout(resolve, closingTransitionDelayMs));
        log('canvas closed');
    }, [dispatch]);

    const transitionCloseToOpen = React.useCallback(
        async (fullTargetCanvasState: InteractCanvasState) => {
            log(`canvas opening with transition of ${openingTransitionDelayMs}ms`);

            // open the canvas with the new mode
            dispatch(setInteractCanvasState(fullTargetCanvasState));

            // wait for the canvas to open before indicating that we are no longer transitioning
            await new Promise((resolve) => setTimeout(resolve, openingTransitionDelayMs));

            log(`canvas opened with mode ${fullTargetCanvasState.mode}`);

            if (fullTargetCanvasState.mode === 'assistant') {
                log(
                    `assistant state: ${fullTargetCanvasState.assistantStateId} [${fullTargetCanvasState.assistantId}]`,
                );
            }
        },
        [dispatch],
    );

    const transitionOpenToNewMode = React.useCallback(
        async (fullTargetCanvasState: InteractCanvasState) => {
            log('canvas changing mode while open');
            await transitionOpenToClose();
            await transitionCloseToOpen(fullTargetCanvasState);
        },
        [transitionCloseToOpen, transitionOpenToClose],
    );

    const setState = React.useCallback(
        (targetCanvasState: Partial<InteractCanvasState>) => {
            dispatch(setInteractCanvasState({ ...interactCanvasState, ...targetCanvasState }));
        },
        [dispatch, interactCanvasState],
    );

    const transitionToState = React.useCallback(
        async (targetCanvasState: Partial<InteractCanvasState>) => {
            if (!interactCanvasState) {
                // this should not happen, but just in case we have no state, set it and return
                dispatch(setInteractCanvasState({ ...targetCanvasState }));
                // ensure that we are not claiming to be transitioning
                setIsTransitioning(false);
                return;
            }

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
            const transitionType = chooseTransitionType(interactCanvasState, {
                ...interactCanvasState,
                ...targetCanvasState,
            });

            // perform the transition
            switch (transitionType) {
                case 'open':
                    await transitionOpenToClose();
                    await transitionCloseToOpen({ ...interactCanvasState, ...targetCanvasState });
                    break;
                case 'close':
                    await transitionOpenToClose();
                    break;
                case 'mode':
                    await transitionOpenToNewMode({ ...interactCanvasState, ...targetCanvasState });
                    break;
                case 'none':
                    // no transition needed, just update the state
                    dispatch(setInteractCanvasState({ ...interactCanvasState, ...targetCanvasState }));
                    setIsTransitioning(false);
                    break;
            }

            // ensure that we are not claiming to be transitioning anymore
            setIsTransitioning(false);
        },
        [
            chooseTransitionType,
            dispatch,
            interactCanvasState,
            transitionCloseToOpen,
            transitionOpenToClose,
            transitionOpenToNewMode,
        ],
    );

    return { interactCanvasState, isTransitioning, setState, transitionToState };
};
