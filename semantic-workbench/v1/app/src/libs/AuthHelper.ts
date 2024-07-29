// Copyright (c) Microsoft. All rights reserved.

import {
    Configuration,
    EndSessionRequest,
    IPublicClientApplication,
    LogLevel,
    RedirectRequest,
} from '@azure/msal-browser';
import debug from 'debug';
import { Constants } from '../Constants';

const log = debug(Constants.debug.root).extend('auth-helper');

const msalConfig: Configuration = {
    auth: {
        ...Constants.msal.auth,
        redirectUri: window.origin,
    },
    cache: Constants.msal.cache,
    system: {
        loggerOptions: {
            loggerCallback: (level, message, containsPii) => {
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
    msalConfig,
    loginRequest,
    logoutRequest,
    loginAsync,
    logoutAsync,
};
