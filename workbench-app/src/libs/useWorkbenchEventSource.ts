import { InteractionRequiredAuthError } from '@azure/msal-browser';
import { EventSourceMessage, fetchEventSource } from '@microsoft/fetch-event-source';
import React from 'react';
import { getMsalInstance } from '../main';
import { AuthHelper } from './AuthHelper';
import { EventSubscriptionManager } from './EventSubscriptionManager';
import { useEnvironment } from './useEnvironment';

const useWorkbenchEventSource = (manager: EventSubscriptionManager, endpoint?: string) => {
    const getAccessToken = React.useCallback(async (forceRefresh?: boolean) => {
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
    }, []);

    const getIdTokenAsync = React.useCallback(async (forceRefresh?: boolean) => {
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
    }, []);

    React.useEffect(() => {
        const abortController = new AbortController();
        let isMounted = true;

        const startEventSource = async () => {
            if (!endpoint || !isMounted) return;

            const accessToken = await getAccessToken();
            const idToken = await getIdTokenAsync();

            const reconnect = () => {
                // re-connect after a delay
                setTimeout(() => {
                    startEventSource();
                }, 1000);
            };

            // this promise is intentionally not awaited. it runs in the background and is cancelled when
            // the control is aborted or an error occurs.
            fetchEventSource(endpoint, {
                signal: abortController.signal,
                openWhenHidden: true,
                headers: {
                    Authorization: `Bearer ${accessToken}`,
                    'X-OpenIdToken': idToken,
                },
                onmessage(event: EventSourceMessage) {
                    if (!event.event) return;
                    manager.emit(event.event, event);
                },
                onclose() {
                    if (!isMounted) return;
                    // retry if the server closes the connection unexpectedly
                    reconnect();
                },
                onerror(err) {
                    if (!isMounted) return;
                    // retry if the fetch fails
                    const fetchFailure = err instanceof TypeError;
                    if (fetchFailure) {
                        reconnect();
                    }
                },
            });
        };

        startEventSource();

        return () => {
            isMounted = false;
            abortController.abort();
        };
    }, [endpoint, getAccessToken, getIdTokenAsync, manager]);
};

export const useWorkbenchUserEventSource = (manager: EventSubscriptionManager) => {
    const environment = useEnvironment();
    const endpoint = `${environment.url}/events`;
    return useWorkbenchEventSource(manager, endpoint);
};

export const useWorkbenchConversationEventSource = (manager: EventSubscriptionManager, conversationId?: string) => {
    const environment = useEnvironment();
    const endpoint = conversationId ? `${environment.url}/conversations/${conversationId}/events` : undefined;
    return useWorkbenchEventSource(manager, endpoint);
};
