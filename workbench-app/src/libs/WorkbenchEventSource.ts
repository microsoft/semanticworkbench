// Copyright (c) Microsoft. All rights reserved.

import { InteractionRequiredAuthError } from '@azure/msal-browser';
import { EventSourceMessage, fetchEventSource } from '@microsoft/fetch-event-source';
import debug from 'debug';
import { Constants } from '../Constants';
import { getMsalInstance } from '../main';
import { AuthHelper } from './AuthHelper';

const log = debug(Constants.debug.root).extend('workbench-event-source');

type EventHandler = (event: EventSourceMessage) => void;

// enum for the type of event source
export enum WorkbenchEventSourceType {
    Conversation = 'conversation',
    User = 'user',
}

export class WorkbenchEventSource {
    private currentEndpoint = '';
    private control: AbortController | null = null;
    private eventHandlers: Map<string, EventHandler[]> = new Map();

    private static conversationInstance: WorkbenchEventSource;
    private static userInstance: WorkbenchEventSource;

    private constructor() {}

    public static async getInstance(type: WorkbenchEventSourceType): Promise<WorkbenchEventSource> {
        if (type === WorkbenchEventSourceType.Conversation) {
            if (!WorkbenchEventSource.conversationInstance) {
                throw new Error('Conversation event source not created');
            }
            return WorkbenchEventSource.conversationInstance;
        }

        if (type === WorkbenchEventSourceType.User) {
            if (!WorkbenchEventSource.userInstance) {
                throw new Error('User event source not created');
            }
            return WorkbenchEventSource.userInstance;
        }

        throw new Error('Invalid event source type');
    }

    public static async createOrUpdate(
        serviceUrl: string,
        type: WorkbenchEventSourceType,
        conversationId?: string,
    ): Promise<WorkbenchEventSource> {
        if (type === WorkbenchEventSourceType.Conversation) {
            if (!conversationId) {
                throw new Error('Conversation ID is required');
            }

            const endpoint = `${serviceUrl}/conversations/${conversationId}/events`;

            if (!WorkbenchEventSource.conversationInstance) {
                log('creating new conversation event source');
                WorkbenchEventSource.conversationInstance = new WorkbenchEventSource();
            }

            await WorkbenchEventSource.conversationInstance.updateEndpoint(endpoint, conversationId);
            return WorkbenchEventSource.conversationInstance;
        }

        if (type === WorkbenchEventSourceType.User) {
            const endpoint = `${serviceUrl}/events`;

            if (!WorkbenchEventSource.userInstance) {
                log('creating new user event source');
                WorkbenchEventSource.userInstance = new WorkbenchEventSource();
            }

            await WorkbenchEventSource.userInstance.updateEndpoint(endpoint);
            return WorkbenchEventSource.userInstance;
        }

        throw new Error('Invalid event source type');
    }

    public addEventListener(event: string, handler: EventHandler) {
        if (!this.control) return;
        const eventHandlers = this.eventHandlers.get(event) || [];
        eventHandlers.push(handler);
        this.eventHandlers.set(event, eventHandlers);
    }

    public removeEventListener(event: string, handler: EventHandler) {
        if (!this.control) return;
        const eventHandlers = this.eventHandlers.get(event);
        if (!eventHandlers) return;
        this.eventHandlers.set(
            event,
            eventHandlers.filter((h) => h !== handler),
        );
    }

    public close() {
        if (!this.control) return;
        this.control.abort();
        this.control = null;
    }

    private async getAccessToken(forceRefresh?: boolean): Promise<string> {
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
    }

    private async getIdTokenAsync(forceRefresh?: boolean): Promise<string> {
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
    }

    private async updateEndpoint(endpoint: string, conversationId?: string, force = false) {
        if (this.currentEndpoint === endpoint && !force) return;
        this.currentEndpoint = endpoint;
        log('updateEndpoint - endpoint:', endpoint, 'conversationId:', conversationId);

        const eventHandlers = this.eventHandlers;

        const connect = async () => {
            if (this.control) {
                this.control.abort();
            }

            this.control = new AbortController();
            const accessToken = await this.getAccessToken();
            const idToken = await this.getIdTokenAsync();
            const abortSignal = this.control.signal;

            const reconnect = () => {
                // re-connect after a delay
                setTimeout(() => {
                    if (abortSignal.aborted) return;
                    connect();
                }, 1000);
            };

            // this promise is intentionally not awaited. it runs in the background and is cancelled when
            // the control is aborted or an error occurs.
            fetchEventSource(endpoint, {
                signal: abortSignal,
                openWhenHidden: true,
                headers: {
                    Authorization: `Bearer ${accessToken}`,
                    'X-OpenIdToken': idToken,
                },
                onmessage(event: EventSourceMessage) {
                    if (!event.event) return;
                    const handlers = eventHandlers.get(event.event) || [];
                    handlers.forEach((handler) => handler(event));
                },
                onclose() {
                    // retry if the server closes the connection unexpectedly
                    reconnect();
                },
                onerror(err) {
                    // retry if the fetch fails
                    const fetchFailure = err instanceof TypeError;
                    if (fetchFailure) {
                        reconnect();
                    }
                },
            });
        };

        await connect();
    }
}
