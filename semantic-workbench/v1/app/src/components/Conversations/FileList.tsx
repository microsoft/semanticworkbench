// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { Conversation } from '../../models/Conversation';
import { ConversationFile } from '../../models/ConversationFile';
import { FileItem } from './FileItem';

interface FileListProps {
    conversation: Conversation;
    conversationFiles: ConversationFile[];
}

export const FileList: React.FC<FileListProps> = (props) => {
    const { conversation, conversationFiles } = props;

    if (conversationFiles.length === 0) {
        return 'No conversation files found';
    }

    return (
        <>
            {conversationFiles
                .toSorted((a, b) => a.name.localeCompare(b.name))
                .map((file) => (
                    <FileItem key={file.name} conversation={conversation} conversationFile={file} />
                ))}
        </>
    );
};
