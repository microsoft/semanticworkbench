// Copyright (c) Microsoft. All rights reserved.
import type { Middleware, MiddlewareAPI } from '@reduxjs/toolkit';
import { isRejectedWithValue } from '@reduxjs/toolkit';
import { addError } from '../features/app/appSlice';

import debug from 'debug';
import { Constants } from '../../Constants';
import { store } from './store';

const log = debug(Constants.debug.root).extend('rtk-query-error-logger');

// Middleware for all RTK Query actions
export const rtkQueryErrorLogger: Middleware = (_api: MiddlewareAPI) => (next) => (action) => {
    // Check if the action is a rejected action with a value
    if (isRejectedWithValue(action)) {
        // Set the title for the error message, displayed as a prefix to the error message
        const title = 'Service error';

        // Set the message for the error message, displayed as the error details
        let message = '';

        // Check if the action payload contains a 'data.detail' property
        if ('data' in action.payload && 'detail' in action.payload.data) {
            // Check if the 'detail' property is a string
            if (typeof action.payload.data.detail === 'string') {
                // Set the message to the 'detail' property
                message = (action.payload.data as { detail: string }).detail;
            } else {
                // Set the message to the 'detail' property as a stringified JSON object
                message = JSON.stringify(action.payload.data.detail);
            }
        } else if ('message' in action.payload) {
            message = action.payload.message;
        } else if ('error' in action.payload && 'status' in action.payload) {
            message = action.payload.status;

            // Additional error handling for specific error types
            if (action.payload.status === 'FETCH_ERROR') {
                message = `Error connecting to Semantic Workbench service, ensure service is running`;
                // Check if the url contains a GitHub Codespaces hostname
                if (action.meta.baseQueryMeta.request.url.includes('app.github.dev')) {
                    // Append a message to the error message to indicate it may be due
                    // to the port not being forwarded correctly
                    message = `${message} and port is visible`;
                }
            }
        }

        // Dispatch the error to the store to cause the error message to be displayed
        // in the header area of the Semantic Workbench UI
        store.dispatch(addError({ title, message }));

        // Additionally, log the error to the console for debugging purposes
        log(title, action.payload);
    }

    // Continue with the next action
    return next(action);
};
