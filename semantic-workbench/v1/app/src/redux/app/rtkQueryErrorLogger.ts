// Copyright (c) Microsoft. All rights reserved.
import type { Middleware, MiddlewareAPI } from '@reduxjs/toolkit';
import { isRejectedWithValue } from '@reduxjs/toolkit';
import { addError } from '../features/app/appSlice';

import debug from 'debug';
import { Constants } from '../../Constants';
import { store } from './store';

const log = debug(Constants.debug.root).extend('rtk-query-error-logger');

export const rtkQueryErrorLogger: Middleware = (_api: MiddlewareAPI) => (next) => (action) => {
    if (isRejectedWithValue(action)) {
        const title = 'Service error';
        const message =
            'data' in action.payload
                ? typeof action.payload.data.detail === 'string'
                    ? (action.payload.data as { detail: string }).detail
                    : JSON.stringify(action.payload.data.detail)
                : action.payload.message;

        store.dispatch(addError({ title, message }));
        log(title, action.payload);
    }
    return next(action);
};
