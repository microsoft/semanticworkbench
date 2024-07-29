// Copyright (c) Microsoft. All rights reserved.

import { MessageBar, MessageBarBody } from '@fluentui/react-components';
import React from 'react';
import { isRouteErrorResponse, useRouteError } from 'react-router-dom';
import { AppView } from '../components/App/AppView';
import { useSiteUtility } from '../libs/useSiteUtility';

export const ErrorPage: React.FC = () => {
    const error = useRouteError();
    const siteUtility = useSiteUtility();

    siteUtility.setDocumentTitle('Error');

    let errorMessage: string;

    if (isRouteErrorResponse(error)) {
        // error is type `ErrorResponse`
        errorMessage = error.data || error.statusText;
    } else if (error instanceof Error) {
        // error is type `Error`
        errorMessage = error.message;
    } else if (typeof error === 'string') {
        // error is type `string`
        errorMessage = error;
    } else {
        // error is type `unknown`
        errorMessage = 'Unknown error';
    }

    return (
        <AppView title="Error">
            <MessageBar intent="error" layout="multiline">
                <MessageBarBody>{errorMessage}</MessageBarBody>
            </MessageBar>
        </AppView>
    );
};
