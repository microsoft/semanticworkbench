// Copyright (c) Microsoft. All rights reserved.

import { EndSessionRequest, IPublicClientApplication, LogLevel, RedirectRequest } from '@azure/msal-browser';
import debug from 'debug';
import { Constants } from '../Constants';

const log = debug(Constants.debug.root).extend('auth-helper');

const getMsalConfig = () => {
    const envClientId: string | undefined = import.meta.env.VITE_SEMANTIC_WORKBENCH_CLIENT_ID;
    const envAuthority: string | undefined = import.meta.env.VITE_SEMANTIC_WORKBENCH_AUTHORITY;
    const clientId = envClientId || Constants.msal.auth.clientId;
    const authority = envAuthority || Constants.msal.auth.authority;

    log(`Using clientId: ${clientId} (from env: ${!!envClientId})`);
    log(`Using authority: ${authority} (from env: ${!!envAuthority})`);

    return {
        auth: {
            ...Constants.msal.auth,
            clientId,
            authority,
            redirectUri: window.origin,
        },
        cache: Constants.msal.cache,
        system: {
            loggerOptions: {
                loggerCallback: (level: any, message: any, containsPii: any) => {
                    if (containsPii) {
                        return;
                    }
                    switch (level) {
                        case LogLevel.Error:
                            log('error:', message);
                            return;
                        // case LogLevel.Info:
                        //     log('info:', message);
                        //     return;
                        // case LogLevel.Verbose:
                        //     log('verbose:', message);
                        //     return;
                        case LogLevel.Warning:
                            log('warn:', message);
                    }
                },
            },
        },
    };
};

const loginRequest: RedirectRequest = {
    scopes: Constants.msal.msGraphScopes,
    // extraScopesToConsent: Constants.msal.skScopes,
};

const logoutRequest: EndSessionRequest = {
    postLogoutRedirectUri: window.origin,
};

const loginAsync = async (instance: IPublicClientApplication) => {
    if (Constants.msal.method === 'redirect') {
        await instance.loginRedirect(loginRequest);
        return undefined;
    } else {
        return await instance.loginPopup(loginRequest);
    }
};

const logoutAsync = async (instance: IPublicClientApplication) => {
    if (Constants.msal.method === 'popup') {
        void instance.logoutPopup(logoutRequest);
    }
    if (Constants.msal.method === 'redirect') {
        void instance.logoutRedirect(logoutRequest);
    }
};

export const AuthHelper = {
    getMsalConfig,
    loginRequest,
    logoutRequest,
    loginAsync,
    logoutAsync,
};
