// Copyright (c) Microsoft. All rights reserved.

import { InteractionRequiredAuthError } from '@azure/msal-browser';
import { useAccount, useMsal } from '@azure/msal-react';
import { Assistant } from '../models/Assistant';
import { AssistantServiceInfo } from '../models/AssistantServiceInfo';
import { useAppDispatch } from '../redux/app/hooks';
import { addError } from '../redux/features/app/appSlice';
import { assistantApi, workflowApi } from '../services/workbench';
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
                    'Authorization': `Bearer ${accessToken}`,
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

    const importConversationsAsync = async (exportData: File): Promise<string[]> => {
        const formData = new FormData();
        formData.append('from_export', exportData);

        const response = await tryFetchAsync('Import conversations', `${environment.url}/conversations/import`, {
            method: 'POST',
            body: formData,
        });

        try {
            const json = await response.json();
            return json.conversation_ids as string[];
        } catch (error) {
            dispatch(addError({ title: 'Import conversations', message: (error as Error).message }));
            throw error;
        }
    };

    const duplicateConversationsAsync = async (conversationIds: string[]) => {
        const { blob, filename } = await exportConversationsAsync(conversationIds);
        return await importConversationsAsync(new File([blob], filename));
    };

    const exportAssistantAsync = async (
        assistantId: string,
    ): Promise<{
        blob: Blob;
        filename: string;
    }> => {
        const response = await tryFetchAsync('Export assistant', `${environment.url}/assistants/${assistantId}/export`);

        // file comes back as an attachment with the name available in the content-disposition header
        const contentDisposition = response.headers.get('Content-Disposition');
        const filename = contentDisposition?.split('filename=')[1].replaceAll('"', '');
        const blob = await response.blob();
        return { blob, filename: filename || 'assistant-export.zip' };
    };

    const importAssistantAsync = async (exportData: File) => {
        const formData = new FormData();
        formData.append('from_export', exportData);

        const response = await tryFetchAsync('Import assistant', `${environment.url}/assistants/import`, {
            method: 'POST',
            body: formData,
        });

        try {
            return (await response.json()) as Assistant;
        } catch (error) {
            dispatch(addError({ title: 'Import assistant', message: (error as Error).message }));
            throw error;
        }
    };

    const duplicateAssistantAsync = async (assistantId: string) => {
        const { blob, filename } = await exportAssistantAsync(assistantId);
        return await importAssistantAsync(new File([blob], filename));
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
        exportConversationsAsync,
        importConversationsAsync,
        duplicateConversationsAsync,
        exportAssistantAsync,
        importAssistantAsync,
        duplicateAssistantAsync,
        getAssistantServiceInfoAsync,
        exportWorkflowDefinitionAsync,
        getWorkflowDefinitionDefaultsAsync,
    };
};
