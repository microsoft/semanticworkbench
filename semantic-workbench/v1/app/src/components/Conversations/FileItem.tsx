// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Caption1,
    Card,
    CardFooter,
    CardHeader,
    DialogTrigger,
    Text,
    makeStyles,
} from '@fluentui/react-components';
import { ArrowDownloadRegular, Delete16Regular } from '@fluentui/react-icons';
import dayjs from 'dayjs';
import timezone from 'dayjs/plugin/timezone';
import utc from 'dayjs/plugin/utc';
import React from 'react';
import * as StreamSaver from 'streamsaver';
import { useWorkbenchService } from '../../libs/useWorkbenchService';
import { Conversation } from '../../models/Conversation';
import { ConversationFile } from '../../models/ConversationFile';
import { useDeleteConversationFileMutation } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';
import { ConversationFileIcon } from './ConversationFileIcon';

dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.tz.guess();

const useClasses = makeStyles({
    details: {
        display: 'flex',
        flexDirection: 'column',
        // gap: tokens.spacingVerticalM,
        marginTop: '0.5rem',
    },
});

interface FileItemProps {
    conversation: Conversation;
    conversationFile: ConversationFile;
    onFileSelect?: (file: ConversationFile) => void;
}

export const FileItem: React.FC<FileItemProps> = (props) => {
    const { conversation, conversationFile } = props;
    const classes = useClasses();
    const workbenchService = useWorkbenchService();
    const [deleteConversationFile] = useDeleteConversationFileMutation();

    const time = dayjs.utc(conversationFile.updated).tz(dayjs.tz.guess()).format('M/D/YYYY h:mm A');

    const sizeToDisplay = (size: number) => {
        if (size < 1024) {
            return `${size} B`;
        } else if (size < 1024 * 1024) {
            return `${(size / 1024).toFixed(2)} KB`;
        } else {
            return `${(size / 1024 / 1024).toFixed(2)} MB`;
        }
    };

    const handleDelete = async () => {
        await deleteConversationFile({ conversationId: conversation.id, filename: conversationFile.name });
    };

    const handleDownload = async () => {
        const response: Response = await workbenchService.downloadConversationFileAsync(
            conversation.id,
            conversationFile,
        );

        if (!response.ok || !response.body) {
            throw new Error('Failed to fetch file');
        }

        const contentDisposition = response.headers.get('content-disposition');
        const fileName = contentDisposition ? contentDisposition.split('filename=')[1] : conversationFile.name;

        // Create a file stream using StreamSaver
        const fileStream = StreamSaver.createWriteStream(fileName);

        const readableStream = response.body;

        // Check if the browser supports pipeTo (most modern browsers do)
        if (readableStream.pipeTo) {
            await readableStream.pipeTo(fileStream);
            console.log('Download complete');
        } else {
            // Fallback for browsers that don't support pipeTo
            const reader = readableStream.getReader();
            const writer = fileStream.getWriter();

            const pump = () =>
                reader.read().then(({ done, value }) => {
                    if (done) {
                        writer.close();
                        return;
                    }
                    writer.write(value).then(pump);
                });

            await pump();
            console.log('Download complete');
        }
    };

    return (
        <Card key={conversationFile.name}>
            <CardHeader
                image={<ConversationFileIcon conversationFile={conversationFile} size={24} />}
                header={<Text weight="semibold">{conversationFile.name}</Text>}
                description={
                    <Caption1>
                        Modified: {time} | Size: {sizeToDisplay(conversationFile.size)}
                    </Caption1>
                }
            />
            <CardFooter>
                <CommandButton
                    label="Delete"
                    description="Delete file from conversation"
                    icon={<Delete16Regular />}
                    dialogContent={{
                        title: 'Delete file',
                        content: (
                            <>
                                Are you sure you want to delete <strong>{conversationFile.name}</strong>?
                            </>
                        ),
                        closeLabel: 'Cancel',
                        additionalActions: [
                            <DialogTrigger key="delete">
                                <Button appearance="primary" onClick={handleDelete}>
                                    Delete
                                </Button>
                            </DialogTrigger>,
                        ],
                    }}
                />
                <CommandButton
                    label="Download"
                    description="Download file from conversation"
                    icon={<ArrowDownloadRegular />}
                    onClick={handleDownload}
                />
            </CardFooter>
        </Card>
    );
};
