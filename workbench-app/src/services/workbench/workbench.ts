// Copyright (c) Microsoft. All rights reserved.

import { generateUuid } from '@azure/ms-rest-js';
import { InteractionRequiredAuthError } from '@azure/msal-browser';
import { BaseQueryFn, FetchArgs, FetchBaseQueryError, createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { AuthHelper } from '../../libs/AuthHelper';
import { getEnvironment } from '../../libs/useEnvironment';
import { getMsalInstance } from '../../main';
import { RootState } from '../../redux/app/store';

const onAuthFailure = () => {
    // If authentication fails, we need to reload the current page, after
    // which the user will be redirected to the login page.
    window.location.reload();
};

const dynamicBaseQuery: BaseQueryFn<string | FetchArgs, unknown, FetchBaseQueryError> = async (
    args,
    workbenchApi,
    extraOptions,
) => {
    const { environmentId } = (workbenchApi.getState() as RootState).settings;
    const environment = getEnvironment(environmentId);

    const prepareHeaders = async (headers: Headers) => {
        const msalInstance = await getMsalInstance();
        const account = msalInstance.getActiveAccount();
        if (!account) {
            onAuthFailure();
            throw new Error('No active account');
        }

        const response = await msalInstance
            .acquireTokenSilent({
                ...AuthHelper.loginRequest,
                account,
            })
            .catch(async (error) => {
                if (error instanceof InteractionRequiredAuthError) {
                    return await AuthHelper.loginAsync(msalInstance);
                }
                onAuthFailure();
                throw error;
            });
        if (!response) {
            onAuthFailure();
            throw new Error('Could not acquire token');
        }

        headers.set('Authorization', `Bearer ${response.accessToken}`);
        headers.set('X-Request-ID', generateUuid().replace(/-/g, '').toLowerCase());
        return headers;
    };

    const rawBaseQuery = fetchBaseQuery({ baseUrl: environment.url, prepareHeaders });

    return rawBaseQuery(args, workbenchApi, extraOptions);
};

export const workbenchApi = createApi({
    reducerPath: 'workbenchApi',
    baseQuery: dynamicBaseQuery,
    tagTypes: [
        'AssistantServiceRegistration',
        'AssistantServiceInfo',
        'Assistant',
        'Conversation',
        'ConversationShare',
        'Config',
        'State',
    ],
    endpoints: () => ({}),
});
