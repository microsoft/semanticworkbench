// Copyright (c) Microsoft. All rights reserved.

import { useMsal } from '@azure/msal-react';
import { Button, Label, MessageBar } from '@fluentui/react-components';
import debug from 'debug';
import React from 'react';
import { Constants } from '../Constants';
import { AppView } from '../components/App/AppView';
import { AuthHelper } from '../libs/AuthHelper';
import { useSiteUtility } from '../libs/useSiteUtility';

const log = debug(Constants.debug.root).extend('login');

export const Login: React.FC = () => {
    const { instance } = useMsal();
    const siteUtility = useSiteUtility();
    const [errorMessage, setErrorMessage] = React.useState<string>();

    siteUtility.setDocumentTitle('Login');

    const handleSignIn = () => {
        void (async () => {
            try {
                await AuthHelper.loginAsync(instance);
            } catch (error) {
                log(error);
                setErrorMessage((error as Error).message);
            }
        })();
    };

    return (
        <AppView title="Login" actions={{ items: [], replaceExisting: true, hideProfileSettings: true }}>
            <div>
                <Button appearance="primary" onClick={handleSignIn}>
                    Sign In
                </Button>
            </div>
            <Label>
                Note: Semantic Workbench can be deployed as a multi-user application, requiring user sign-in even when running locally as a single-user instance.
                By default, it uses Microsoft accounts and a sample app registration for quick setup.
                You can modify the configuration in the code by editing `Constants.ts` and `middleware.py`.
            </Label>
            {errorMessage && (
                <MessageBar intent="error" layout="multiline">
                    {errorMessage}
                </MessageBar>
            )}
        </AppView>
    );
};
