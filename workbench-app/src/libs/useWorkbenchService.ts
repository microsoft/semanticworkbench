// Copyright (c) Microsoft. All rights reserved.

import { InteractionRequiredAuthError } from '@azure/msal-browser';
import { useAccount, useMsal } from '@azure/msal-react';
import React from 'react';
import { AssistantServiceInfo } from '../models/AssistantServiceInfo';
import { AssistantServiceRegistration } from '../models/AssistantServiceRegistration';
import { Conversation } from '../models/Conversation';
import { ConversationFile } from '../models/ConversationFile';
import { ConversationParticipant } from '../models/ConversationParticipant';
import { ProcessedFileContent } from '../models/ProcessedFileContent';
import { useAppDispatch } from '../redux/app/hooks';
import { addError } from '../redux/features/app/appSlice';
import { assistantServiceApi, conversationApi, workbenchApi } from '../services/workbench';
import { AuthHelper } from './AuthHelper';
import { Utility } from './Utility';
import { useEnvironment } from './useEnvironment';

export const useWorkbenchService = () => {
    const environment = useEnvironment();
    const dispatch = useAppDispatch();
    const account = useAccount();
    const msal = useMsal();

    const getAccessTokenAsync = React.useCallback(async () => {
        if (!account) {
            throw new Error('No active account');
        }

        const response = await msal.instance
            .acquireTokenSilent({
                ...AuthHelper.loginRequest,
                account,
            })
            .catch(async (error) => {
                if (error instanceof InteractionRequiredAuthError) {
                    return await AuthHelper.loginAsync(msal.instance);
                }
                throw error;
            });
        if (!response) {
            dispatch(addError({ title: 'Failed to acquire token', message: 'Could not acquire access token' }));
            throw new Error('Could not acquire access token');
        }
        return response.accessToken;
    }, [account, dispatch, msal.instance]);

    const getIdTokenAsync = React.useCallback(async () => {
        if (!account) {
            throw new Error('No active account');
        }

        const response = await msal.instance
            .acquireTokenSilent({
                ...AuthHelper.loginRequest,
                account,
            })
            .catch(async (error) => {
                if (error instanceof InteractionRequiredAuthError) {
                    return await AuthHelper.loginAsync(msal.instance);
                }
                throw error;
            });
        if (!response) {
            dispatch(addError({ title: 'Failed to acquire ID token', message: 'Could not acquire token' }));
            throw new Error('Could not acquire ID token');
        }
        return response.idToken;
    }, [account, dispatch, msal.instance]);

    const tryFetchAsync = React.useCallback(
        async (operationTitle: string, url: string, options?: RequestInit): Promise<Response> => {
            const accessToken = await getAccessTokenAsync();
            const idToken = await getIdTokenAsync();
            const response = await fetch(url, {
                ...options,
                headers: {
                    ...options?.headers,
                    Authorization: `Bearer ${accessToken}`,
                    'X-OpenIdToken': idToken,
                },
            });

            if (!response.ok) {
                const json = await response.json();
                const message = json?.detail ?? json?.detail ?? response.statusText;
                dispatch(addError({ title: operationTitle, message }));
                throw new Error(`Failed to ${operationTitle}: ${message}`);
            }

            return response;
        },
        [dispatch, getAccessTokenAsync, getIdTokenAsync],
    );

    const tryFetchStreamAsync = React.useCallback(
        async (operationTitle: string, url: string, options?: RequestInit): Promise<Response> => {
            const accessToken = await getAccessTokenAsync();
            const idToken = await getIdTokenAsync();
            const response = await fetch(url, {
                ...options,
                headers: {
                    ...options?.headers,
                    Authorization: `Bearer ${accessToken}`,
                    'X-OpenIdToken': idToken,
                },
            });

            if (!response.ok) {
                const json = await response.json();
                const message = json?.detail ?? json?.detail ?? response.statusText;
                dispatch(addError({ title: operationTitle, message }));
                throw new Error(`Failed to ${operationTitle}: ${message}`);
            }

            return response;
        },
        [dispatch, getAccessTokenAsync, getIdTokenAsync],
    );

    const tryFetchFileAsync = React.useCallback(
        async (
            operationTitle: string,
            path: string,
            defaultFilename: string,
        ): Promise<{ blob: Blob; filename: string }> => {
            const response = await tryFetchAsync(operationTitle, `${environment.url}${path}`);
            const blob = await response.blob();
            return {
                blob,
                filename:
                    response.headers.get('Content-Disposition')?.split('filename=')[1].replaceAll('"', '') ??
                    defaultFilename,
            };
        },
        [environment.url, tryFetchAsync],
    );

    const getAzureSpeechTokenAsync = React.useCallback(async (): Promise<{ token: string; region: string }> => {
        const response = await tryFetchAsync('Get Azure Speech token', `${environment.url}/azure-speech/token`);
        const json = await response.json();
        return { token: json.token ?? '', region: json.region ?? '' };
    }, [environment.url, tryFetchAsync]);

    const downloadConversationFileAsync = React.useCallback(
        async (conversationId: string, conversationFile: ConversationFile): Promise<Response> => {
            const path = `/conversations/${conversationId}/files/${conversationFile.name}`;
            return await tryFetchStreamAsync('Download conversation file', `${environment.url}${path}`);
        },
        [environment.url, tryFetchStreamAsync],
    );

    const exportTranscriptAsync = React.useCallback(
        async (
            conversation: Conversation,
            participants: ConversationParticipant[],
        ): Promise<{ blob: Blob; filename: string }> => {
            const messages = await dispatch(
                conversationApi.endpoints.getConversationMessages.initiate({
                    conversationId: conversation.id,
                }),
            ).unwrap();

            const timestampForFilename = Utility.getTimestampForFilename();
            const filename = `transcript_${conversation.title.replaceAll(' ', '_')}_${timestampForFilename}.md`;

            const markdown = messages
                .filter((message) => message.messageType !== 'log')
                .map((message) => {
                    const date = Utility.toFormattedDateString(message.timestamp, 'dddd, MMMM D');
                    const time = Utility.toFormattedDateString(message.timestamp, 'h:mm A');
                    const participant = participants.find(
                        (possible_participant) => possible_participant.id === message.sender.participantId,
                    );
                    const sender = participant ? participant.name : 'Unknown';
                    const parts = [];
                    parts.push(`### [${date} ${time}] ${sender}:`);
                    if (message.messageType !== 'chat') {
                        // truncate long messages
                        const trimToLength = 1000;
                        const content =
                            message.content.length > trimToLength
                                ? `${message.content.slice(0, trimToLength)}... <truncated>`
                                : message.content;
                        parts.push(`${message.messageType}: ${content}`);
                    } else {
                        parts.push(message.content);
                    }
                    if (message.filenames && message.filenames.length > 0) {
                        parts.push(
                            message.filenames
                                .map((filename) => {
                                    return `attachment: ${filename}`;
                                })
                                .join('\n'),
                        );
                    }
                    parts.push('----------------------------------\n\n');

                    return parts.join('\n\n');
                })
                .join('\n');

            const blob = new Blob([markdown], { type: 'text/markdown' });

            return { blob, filename };
        },
        [dispatch],
    );

    const exportConversationsAsync = React.useCallback(
        async (conversationIds: string[]): Promise<{ blob: Blob; filename: string }> => {
            const response = await tryFetchAsync(
                'Export conversations',
                `${environment.url}/conversations/export?id=${conversationIds.join(',')}`,
            );

            // file comes back as an attachment with the name available in the content-disposition header
            const contentDisposition = response.headers.get('Content-Disposition');
            const filename = contentDisposition?.split('filename=')[1].replaceAll('"', '');
            const blob = await response.blob();
            return { blob, filename: filename || 'conversation-export.zip' };
        },
        [environment.url, tryFetchAsync],
    );

    const importConversationsAsync = React.useCallback(
        async (exportData: File): Promise<{ assistantIds: string[]; conversationIds: string[] }> => {
            const formData = new FormData();
            formData.append('from_export', exportData);

            const response = await tryFetchAsync(
                'Import assistants and conversations',
                `${environment.url}/conversations/import`,
                {
                    method: 'POST',
                    body: formData,
                },
            );

            try {
                const json = await response.json();
                return {
                    conversationIds: json.conversation_ids as string[],
                    assistantIds: json.assistant_ids as string[],
                };
            } catch (error) {
                dispatch(addError({ title: 'Import assistants and conversations', message: (error as Error).message }));
                throw error;
            } finally {
                // conversation imports can include assistants and conversations
                dispatch(workbenchApi.util.invalidateTags(['Assistant', 'Conversation']));
            }
        },
        [dispatch, environment.url, tryFetchAsync],
    );

    const exportThenImportConversationAsync = React.useCallback(
        async (conversationIds: string[]) => {
            const { blob, filename } = await exportConversationsAsync(conversationIds);
            const result = await importConversationsAsync(new File([blob], filename));
            return result.conversationIds;
        },
        [exportConversationsAsync, importConversationsAsync],
    );

    const exportAssistantAsync = React.useCallback(
        async (
            assistantId: string,
        ): Promise<{
            blob: Blob;
            filename: string;
        }> => {
            const path = `/assistants/${assistantId}/export`;
            return await tryFetchFileAsync('Export assistant', path, 'assistant-export.zip');
        },
        [tryFetchFileAsync],
    );

    const exportThenImportAssistantAsync = React.useCallback(
        async (assistantId: string) => {
            const { blob, filename } = await exportAssistantAsync(assistantId);
            const result = await importConversationsAsync(new File([blob], filename));
            return result.assistantIds[0];
        },
        [exportAssistantAsync, importConversationsAsync],
    );

    const getAssistantServiceInfoAsync = React.useCallback(
        async (assistantServiceId: string): Promise<AssistantServiceInfo | undefined> => {
            const results = await dispatch(
                assistantServiceApi.endpoints.getAssistantServiceInfo.initiate(assistantServiceId),
            );
            if (results.isError) {
                throw results.error;
            }
            return results.data;
        },
        [dispatch],
    );

    const getAssistantServiceRegistrationAsync = React.useCallback(
        async (assistantServiceId: string): Promise<AssistantServiceRegistration | undefined> => {
            const results = await dispatch(
                assistantServiceApi.endpoints.getAssistantServiceRegistration.initiate(assistantServiceId),
            );
            if (results.isError) {
                throw results.error;
            }
            return results.data;
        },
        [dispatch],
    );

    const getAssistantServiceInfosAsync = React.useCallback(
        async (assistantServiceIds: string[]): Promise<Array<AssistantServiceInfo | undefined>> => {
            return await Promise.all(
                assistantServiceIds.map(async (assistantServiceId) => {
                    try {
                        const registration = await getAssistantServiceRegistrationAsync(assistantServiceId);
                        if (!registration?.assistantServiceOnline) {
                            return undefined;
                        }
                    } catch (error) {
                        return undefined;
                    }
                    try {
                        return await getAssistantServiceInfoAsync(assistantServiceId);
                    } catch (error) {
                        return undefined;
                    }
                }),
            );
        },
        [getAssistantServiceInfoAsync, getAssistantServiceRegistrationAsync],
    );

    const getProcessedFileContentAsync = React.useCallback(
        async (conversationId: string, assistantId: string, filename: string): Promise<ProcessedFileContent> => {
            const path = `/conversations/${conversationId}/assistants/${assistantId}/files/${encodeURIComponent(
                filename,
            )}/processed-content`;
            const response = await tryFetchAsync('Get processed file content', `${environment.url}${path}`);

            if (!response.ok) {
                throw new Error(`Failed to fetch file content: ${response.statusText}`);
            }

            return await response.json();
        },
        [environment.url, tryFetchAsync],
    );

    return {
        getAzureSpeechTokenAsync,
        downloadConversationFileAsync,
        exportTranscriptAsync,
        exportConversationsAsync,
        importConversationsAsync,
        exportThenImportConversationAsync,
        exportAssistantAsync,
        exportThenImportAssistantAsync,
        getAssistantServiceInfoAsync,
        getAssistantServiceInfosAsync,
        getProcessedFileContentAsync,
    };
};
