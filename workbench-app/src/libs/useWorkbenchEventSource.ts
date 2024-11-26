import { InteractionRequiredAuthError } from '@azure/msal-browser';
import { EventSourceMessage, EventStreamContentType, fetchEventSource } from '@microsoft/fetch-event-source';
import debug from 'debug';
import React from 'react';
import { Constants } from '../Constants';
import { getMsalInstance } from '../main';
import { AuthHelper } from './AuthHelper';
import { EventSubscriptionManager } from './EventSubscriptionManager';
import { useEnvironment } from './useEnvironment';

const log = debug(Constants.debug.root).extend('useWorkbenchEventSource');

class RetriableError extends Error {}
class FatalError extends Error {}

const useWorkbenchEventSource = (manager: EventSubscriptionManager, endpoint?: string) => {
    React.useEffect(() => {
        if (!endpoint) return;

        log(`Connecting event source: ${endpoint}`);

        const abortController = new AbortController();
        let isMounted = true;

        const startEventSource = async () => {
            if (!isMounted) return;

            const accessToken = await getAccessToken();
            const idToken = await getIdTokenAsync();

            // this promise is intentionally not awaited. it runs in the background and is cancelled when
            // the control is aborted or an error occurs.
            fetchEventSource(endpoint, {
                signal: abortController.signal,
                openWhenHidden: true,
                headers: {
                    Authorization: `Bearer ${accessToken}`,
                    'X-OpenIdToken': idToken,
                },
                async onopen(response) {
                    if (!isMounted) return;
                    if (response.ok && response.headers.get('content-type')?.includes(EventStreamContentType)) {
                        log(`Event source connected: ${response.status} ${response.statusText} [${response.url}]`);
                        return; // everything's good
                    } else if (response.status >= 400 && response.status < 500 && response.status !== 429) {
                        // client-side errors are usually non-retriable:
                        log(`Event source error: ${response.status} ${response.statusText} [${response.url}]`);
                        throw new FatalError();
                    } else {
                        log(`Event source error: ${response.status} ${response.statusText} [${response.url}]`);
                        throw new RetriableError();
                    }
                },
                onmessage(message: EventSourceMessage) {
                    if (!message.event) return;
                    if (message.event === 'FatalError') {
                        throw new FatalError();
                    }
                    manager.emit(message.event, message);
                },
                onclose() {
                    if (!isMounted) return;
                    log(`Event source closed unexpectedly: ${endpoint}`);
                    throw new RetriableError();
                },
                onerror(error) {
                    if (!isMounted) return;
                    log(`Event source error: ${error} [${endpoint}]`);
                    if (error instanceof FatalError) {
                        // fatal errors are not retried
                        throw error; // rethrow to stop the event source
                    }
                    // will retry
                },
            });
        };

        startEventSource();

        return () => {
            log(`Disconnecting event source: ${endpoint}`);
            isMounted = false;
            abortController.abort();
        };
    }, [endpoint, manager]);
};

const getAccessToken = async (forceRefresh?: boolean) => {
    const msalInstance = await getMsalInstance();

    const account = msalInstance.getActiveAccount();
    if (!account) {
        throw new Error('No active account');
    }

    const response = await msalInstance
        .acquireTokenSilent({
            ...AuthHelper.loginRequest,
            account,
            forceRefresh,
        })
        .catch(async (error) => {
            if (error instanceof InteractionRequiredAuthError) {
                return await AuthHelper.loginAsync(msalInstance);
            }
            throw error;
        });
    if (!response) {
        throw new Error('Could not acquire access token');
    }

    return response.accessToken;
};

const getIdTokenAsync = async (forceRefresh?: boolean) => {
    const msalInstance = await getMsalInstance();

    const account = msalInstance.getActiveAccount();
    if (!account) {
        throw new Error('No active account');
    }

    const response = await msalInstance
        .acquireTokenSilent({
            ...AuthHelper.loginRequest,
            account,
            forceRefresh,
        })
        .catch(async (error) => {
            if (error instanceof InteractionRequiredAuthError) {
                return await AuthHelper.loginAsync(msalInstance);
            }
            throw error;
        });
    if (!response) {
        throw new Error('Could not acquire ID token');
    }

    return response.idToken;
};

export const useWorkbenchUserEventSource = (manager: EventSubscriptionManager) => {
    const environment = useEnvironment();
    const [endpoint, setEndpoint] = React.useState<string>();

    React.useEffect(() => {
        setEndpoint(`${environment.url}/events`);
    }, [environment]);

    return useWorkbenchEventSource(manager, endpoint);
};

export const useWorkbenchConversationEventSource = (manager: EventSubscriptionManager, conversationId?: string) => {
    const environment = useEnvironment();
    const [endpoint, setEndpoint] = React.useState<string>();

    React.useEffect(() => {
        setEndpoint(conversationId ? `${environment.url}/conversations/${conversationId}/events` : undefined);
    }, [environment, conversationId]);

    useWorkbenchEventSource(manager, endpoint);
};
