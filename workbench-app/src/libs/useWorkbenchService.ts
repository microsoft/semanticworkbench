// Copyright (c) Microsoft. All rights reserved.

import { InteractionRequiredAuthError } from '@azure/msal-browser';
import { useAccount, useMsal } from '@azure/msal-react';
import { AssistantServiceInfo } from '../models/AssistantServiceInfo';
import { ConversationFile } from '../models/ConversationFile';
import { useAppDispatch } from '../redux/app/hooks';
import { addError } from '../redux/features/app/appSlice';
import { assistantApi, workbenchApi, workflowApi } from '../services/workbench';
import { AuthHelper } from './AuthHelper';
import { Utility } from './Utility';
import { useEnvironment } from './useEnvironment';

export const useWorkbenchService = () => {
    const environment = useEnvironment();
    const dispatch = useAppDispatch();
    const account = useAccount();
    const msal = useMsal();

    const getAccessTokenAsync = async () => {
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
    };

    const getIdTokenAsync = async () => {
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
    };

    const tryFetchAsync = async (operationTitle: string, url: string, options?: RequestInit): Promise<Response> => {
        const accessToken = await getAccessTokenAsync();
        const idToken = await getIdTokenAsync();
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    ...options?.headers,
                    Authorization: `Bearer ${accessToken}`,
                    'X-OpenIdToken': idToken,
                },
            });

            if (!response.ok) {
                dispatch(addError({ title: operationTitle, message: response.statusText }));
                throw new Error(`failed to fetch: ${response.statusText}`);
            }

            return response;
        } catch (error) {
            dispatch(addError({ title: operationTitle, message: (error as Error).message }));
            throw error;
        }
    };

    const tryFetchStreamAsync = async (
        operationTitle: string,
        url: string,
        options?: RequestInit,
    ): Promise<Response> => {
        const accessToken = await getAccessTokenAsync();
        const idToken = await getIdTokenAsync();
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    ...options?.headers,
                    Authorization: `Bearer ${accessToken}`,
                    'X-OpenIdToken': idToken,
                },
            });
            return response;
        } catch (error) {
            dispatch(addError({ title: operationTitle, message: (error as Error).message }));
            throw error;
        }
    };

    const tryFetchFileAsync = async (
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
    };

    const getAzureSpeechTokenAsync = async (): Promise<{ token: string; region: string }> => {
        const response = await tryFetchAsync('Get Azure Speech token', `${environment.url}/azure-speech/token`);
        const json = await response.json();
        return { token: json.token, region: json.region };
    };

    const downloadConversationFileAsync = async (
        conversationId: string,
        conversationFile: ConversationFile,
    ): Promise<Response> => {
        const path = `/conversations/${conversationId}/files/${conversationFile.name}`;
        return await tryFetchStreamAsync('Download conversation file', `${environment.url}${path}`);
    };

    const exportConversationsAsync = async (conversationIds: string[]): Promise<{ blob: Blob; filename: string }> => {
        const response = await tryFetchAsync(
            'Export conversations',
            `${environment.url}/conversations/export?id=${conversationIds.join(',')}`,
        );

        // file comes back as an attachment with the name available in the content-disposition header
        const contentDisposition = response.headers.get('Content-Disposition');
        const filename = contentDisposition?.split('filename=')[1].replaceAll('"', '');
        const blob = await response.blob();
        return { blob, filename: filename || 'conversation-export.zip' };
    };

    const importConversationsAsync = async (
        exportData: File,
    ): Promise<{ assistantIds: string[]; conversationIds: string[] }> => {
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
    };

    const duplicateConversationsAsync = async (conversationIds: string[]) => {
        const { blob, filename } = await exportConversationsAsync(conversationIds);
        const result = await importConversationsAsync(new File([blob], filename));
        return result.conversationIds;
    };

    const exportAssistantAsync = async (
        assistantId: string,
    ): Promise<{
        blob: Blob;
        filename: string;
    }> => {
        const path = `/assistants/${assistantId}/export`;
        return await tryFetchFileAsync('Export assistant', path, 'assistant-export.zip');
    };

    const duplicateAssistantAsync = async (assistantId: string) => {
        const { blob, filename } = await exportAssistantAsync(assistantId);
        const result = await importConversationsAsync(new File([blob], filename));
        return result.assistantIds[0];
    };

    const getAssistantServiceInfoAsync = async (
        assistant_service_id: string,
    ): Promise<AssistantServiceInfo | undefined> => {
        const results = await dispatch(assistantApi.endpoints.getAssistantServiceInfo.initiate(assistant_service_id));
        return results.data;
    };

    const exportWorkflowDefinitionAsync = async (workflowId: string) => {
        const results = await dispatch(workflowApi.endpoints.getWorkflowDefinition.initiate(workflowId));
        const workflowDefinition = results.data;

        if (!workflowDefinition) {
            throw new Error(`Workflow with ID ${workflowId} not found`);
        }

        const blob = new Blob([JSON.stringify(workflowDefinition)], { type: 'application/json' });
        const filename = `workflow_${workflowDefinition.label.replace(
            ' ',
            '_',
        )}_${Utility.getTimestampForExport()}.json`;
        return { blob, filename };
    };

    // TODO: implement importWorkflowDefinitionAsync
    // const duplicateWorkflowDefinitionAsync = async (workflowId: string) => {
    //     const { blob, filename } = await exportWorkflowDefinitionAsync(workflowId);
    //     return await importWorkflowDefinitionAsync(new File([blob], filename));
    // };

    const getWorkflowDefinitionDefaultsAsync = async () => {
        const results = await dispatch(workflowApi.endpoints.getWorkflowDefinitionDefaults.initiate());
        return results.data;
    };

    return {
        getAzureSpeechTokenAsync,
        downloadConversationFileAsync,
        exportConversationsAsync,
        importConversationsAsync,
        duplicateConversationsAsync,
        exportAssistantAsync,
        duplicateAssistantAsync,
        getAssistantServiceInfoAsync,
        exportWorkflowDefinitionAsync,
        getWorkflowDefinitionDefaultsAsync,
    };
};
