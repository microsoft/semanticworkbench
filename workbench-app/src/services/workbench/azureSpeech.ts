import { AzureSpeechToken } from '../../models/AzureSpeechToken';
import { workbenchApi } from './workbench';

export const azureSpeechApi = workbenchApi.injectEndpoints({
    endpoints: (builder) => ({
        getAzureSpeechServiceToken: builder.query<AzureSpeechToken, void>({
            query: () => '/azure-speech/token',
            providesTags: ['AzureSpeechServiceToken'],
        }),
    }),
    overrideExisting: false,
});

export const { useGetAzureSpeechServiceTokenQuery } = azureSpeechApi;
