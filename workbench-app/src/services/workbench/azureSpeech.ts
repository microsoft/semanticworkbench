import { AzureSpeechServiceAccess } from '../../models/AzureSpeechServiceAccess';
import { workbenchApi } from './workbench';

export const azureSpeechApi = workbenchApi.injectEndpoints({
    endpoints: (builder) => ({
        getAzureSpeechServiceToken: builder.query<string, void>({
            query: () => '/azure-speech/token',
        }),
        getAzureSpeechServiceAccess: builder.query<AzureSpeechServiceAccess, void>({
            query: () => '/azure-speech/service-access',
        }),
    }),
    overrideExisting: false,
});

export const { useGetAzureSpeechServiceTokenQuery, useGetAzureSpeechServiceAccessQuery } = azureSpeechApi;
