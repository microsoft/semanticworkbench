// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { useGetConversationFilesQuery } from '../../services/workbench';
import { FileItem } from './FileItem';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingHorizontalM,
    },
});

interface FileListProps {
    conversationId: string;
}

export const FileList: React.FC<FileListProps> = (props) => {
    const { conversationId } = props;
    const classes = useClasses();

    const {
        data: conversationFiles,
        error: getConversationFilesError,
        isLoading: isLoadingConversationFiles,
    } = useGetConversationFilesQuery(conversationId);

    if (getConversationFilesError) {
        const errorMessage = JSON.stringify(getConversationFilesError);
        throw new Error(`Error loading conversation files: ${errorMessage}`);
    }

    if (isLoadingConversationFiles) {
        return null;
    }

    if (!conversationFiles) {
        throw new Error('Conversation not found');
    }

    if (conversationFiles.length === 0) {
        return 'No files found.';
    }

    return (
        <div className={classes.root}>
            {conversationFiles
                .toSorted((a, b) => a.name.localeCompare(b.name))
                .map((file) => (
                    <FileItem key={file.name} conversationId={conversationId} file={file} />
                ))}
        </div>
    );
};
