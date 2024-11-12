import { Link, Popover, PopoverSurface, PopoverTrigger, Toaster } from '@fluentui/react-components';
import debug from 'debug';
import React from 'react';
import { Outlet } from 'react-router-dom';
import { Constants } from './Constants';
import useDragAndDrop from './libs/useDragAndDrop';
import { useKeySequence } from './libs/useKeySequence';
import { useNotify } from './libs/useNotify';
import { useAppDispatch, useAppSelector } from './redux/app/hooks';
import { setIsDraggingOverBody, toggleDevMode } from './redux/features/app/appSlice';

const log = debug(Constants.debug.root).extend('Root');

export const Root: React.FC = () => {
    const isDraggingOverBody = useAppSelector((state) => state.app.isDraggingOverBody);
    const dispatch = useAppDispatch();
    useKeySequence(
        [
            'ArrowUp',
            'ArrowUp',
            'ArrowDown',
            'ArrowDown',
            'ArrowLeft',
            'ArrowRight',
            'ArrowLeft',
            'ArrowRight',
            'b',
            'a',
            'Enter',
        ],
        () => dispatch(toggleDevMode()),
    );
    const { notifyError } = useNotify();

    const globalErrorHandler = React.useCallback(
        (event: PromiseRejectionEvent) => {
            log('Unhandled promise rejection', event.reason);
            notifyError({
                id: ['unhandledrejection', event.reason.message, event.reason.stack].join(':'),
                title: 'Unhandled error',
                message: event.reason.message,
                additionalActions: [
                    <Popover key="popover">
                        <PopoverTrigger disableButtonEnhancement>
                            <Link>More info</Link>
                        </PopoverTrigger>
                        <PopoverSurface>
                            <pre>{event.reason.stack}</pre>
                        </PopoverSurface>
                    </Popover>,
                ],
            });
        },
        [notifyError],
    );

    React.useEffect(() => {
        // add a global error handler to catch unhandled promise rejections
        window.addEventListener('unhandledrejection', globalErrorHandler);

        return () => {
            window.removeEventListener('unhandledrejection', globalErrorHandler);
        };
    }, [globalErrorHandler]);

    // ignore file drop events at the document level as this prevents the browser from
    // opening the file in the window if the drop event is not handled or the user misses
    const ignoreFileDrop = true;
    const isDraggingOver = useDragAndDrop(document.body, log, ignoreFileDrop);

    React.useEffect(() => {
        if (isDraggingOver !== isDraggingOverBody) {
            dispatch(setIsDraggingOverBody(isDraggingOver));
        }
    }, [isDraggingOver, isDraggingOverBody, dispatch]);

    return (
        <>
            <Outlet />
            <Toaster toasterId={Constants.app.globalToasterId} pauseOnHover pauseOnWindowBlur />
        </>
    );
};
