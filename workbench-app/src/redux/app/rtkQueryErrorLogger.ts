// Copyright (c) Microsoft. All rights reserved.
import type { Middleware, MiddlewareAPI } from '@reduxjs/toolkit';
import { isRejectedWithValue } from '@reduxjs/toolkit';
import { addError } from '../features/app/appSlice';

import debug from 'debug';
import { Constants } from '../../Constants';
import { Utility } from '../../libs/Utility';
import { store } from './store';

const log = debug(Constants.debug.root).extend('rtk-query-error-logger');

// Middleware for all RTK Query actions
export const rtkQueryErrorLogger: Middleware = (_api: MiddlewareAPI) => (next) => (action) => {
    // Check if the action is a rejected action with a value
    if (isRejectedWithValue(action)) {
        // Set the title for the error message, displayed as a prefix to the error message
        const title = 'Service error';

        // Set the message for the error message, displayed as the error details
        const message = Utility.errorToMessageString(action);

        // Dispatch the error to the store to cause the error message to be displayed
        // in the header area of the Semantic Workbench UI
        store.dispatch(addError({ title, message }));

        // Additionally, log the error to the console for debugging purposes
        log(title, action.payload);
    }

    // Continue with the next action
    return next(action);
};
