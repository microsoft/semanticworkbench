import { ConversationFile } from '../../models/ConversationFile';
import { workbenchApi } from './workbench';

const fileApi = workbenchApi.injectEndpoints({
    endpoints: (builder) => ({
        getConversationFiles: builder.query<ConversationFile[], string>({
            query: (id) => `/conversations/${id}/files`,
            providesTags: ['Conversation'],
            transformResponse: (response: any) => response.files.map(transformResponseToFile),
        }),
        uploadConversationFiles: builder.mutation<ConversationFile, { conversationId: string; files: File[] }>({
            query: ({ conversationId, files }) => {
                return {
                    url: `/conversations/${conversationId}/files`,
                    method: 'PUT',
                    body: transformConversationFilesForRequest(files),
                };
            },
            invalidatesTags: ['Conversation'],
            transformResponse: (response: any) => transformResponseToFile(response),
        }),
        deleteConversationFile: builder.mutation<void, { conversationId: string; filename: string }>({
            query: ({ conversationId, filename }) => ({
                url: `/conversations/${conversationId}/files/${filename}`,
                method: 'DELETE',
            }),
            invalidatesTags: ['Conversation'],
        }),
    }),
    overrideExisting: false,
});

export const { useGetConversationFilesQuery, useUploadConversationFilesMutation, useDeleteConversationFileMutation } =
    fileApi;

const transformResponseToFile = (response: any): ConversationFile => {
    try {
        return {
            name: response.filename,
            created: response.created_datetime,
            updated: response.updated_datetime,
            size: response.file_size,
            version: response.current_version,
            contentType: response.content_type,
            metadata: response.metadata,
        };
    } catch (error) {
        throw new Error(`Failed to transform file response: ${error}`);
    }
};

const transformConversationFilesForRequest = (files: File[]) => {
    const formData = new FormData();
    for (var i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }
    return formData;
};
