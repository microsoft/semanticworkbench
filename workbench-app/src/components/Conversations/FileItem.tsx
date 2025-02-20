// Copyright (c) Microsoft. All rights reserved.

import { Button, Caption1, Card, CardHeader, DialogTrigger, makeStyles, Text } from '@fluentui/react-components';
import { ArrowDownloadRegular, Delete16Regular } from '@fluentui/react-icons';
import React from 'react';
import * as StreamSaver from 'streamsaver';
import { useWorkbenchService } from '../../libs/useWorkbenchService';
import { Utility } from '../../libs/Utility';
import { Conversation } from '../../models/Conversation';
import { ConversationFile } from '../../models/ConversationFile';
import { useDeleteConversationFileMutation } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';
import { TooltipWrapper } from '../App/TooltipWrapper';
import { ConversationFileIcon } from './ConversationFileIcon';

const useClasses = makeStyles({
    cardHeader: {
        '> .fui-CardHeader__header': {
            overflow: 'hidden',
        },
    },
    actions: {
        display: 'flex',
        flexDirection: 'row',
        gap: '8px',
    },
});

interface FileItemProps {
    conversation: Conversation;
    conversationFile: ConversationFile;
    readOnly?: boolean;
    onFileSelect?: (file: ConversationFile) => void;
}

export const FileItem: React.FC<FileItemProps> = (props) => {
    const { conversation, conversationFile, readOnly } = props;
    const classes = useClasses();
    const workbenchService = useWorkbenchService();
    const [deleteConversationFile] = useDeleteConversationFileMutation();
    const [submitted, setSubmitted] = React.useState(false);

    const time = React.useMemo(
        () => Utility.toFormattedDateString(conversationFile.updated, 'M/D/YYYY h:mm A'),
        [conversationFile.updated],
    );

    const sizeToDisplay = (size: number) => {
        if (size < 1024) {
            return `${size} B`;
        } else if (size < 1024 * 1024) {
            return `${(size / 1024).toFixed(2)} KB`;
        } else {
            return `${(size / 1024 / 1024).toFixed(2)} MB`;
        }
    };

    const handleDelete = React.useCallback(async () => {
        if (submitted) {
            return;
        }
        setSubmitted(true);

        try {
            await deleteConversationFile({ conversationId: conversation.id, filename: conversationFile.name });
        } finally {
            setSubmitted(false);
        }
    }, [conversation.id, conversationFile.name, deleteConversationFile, submitted]);

    const handleDownload = React.useCallback(async () => {
        if (submitted) {
            return;
        }
        setSubmitted(true);

        try {
            const response: Response = await workbenchService.downloadConversationFileAsync(
                conversation.id,
                conversationFile,
            );

            if (!response.ok || !response.body) {
                throw new Error('Failed to fetch file');
            }

            // Create a file stream using StreamSaver
            const fileStream = StreamSaver.createWriteStream(conversationFile.name);

            const readableStream = response.body;

            // Check if the browser supports pipeTo (most modern browsers do)
            if (readableStream.pipeTo) {
                await readableStream.pipeTo(fileStream);
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
            }
        } finally {
            setSubmitted(false);
        }
    }, [conversation.id, conversationFile, workbenchService, submitted]);

    return (
        <Card key={conversationFile.name}>
            <CardHeader
                className={classes.cardHeader}
                image={<ConversationFileIcon file={conversationFile} size={24} />}
                header={
                    <TooltipWrapper content={conversationFile.name}>
                        <Text truncate wrap={false} weight="semibold">
                            {conversationFile.name}
                        </Text>
                    </TooltipWrapper>
                }
                description={
                    <Caption1>
                        {time} | {sizeToDisplay(conversationFile.size)}
                    </Caption1>
                }
                action={
                    <div className={classes.actions}>
                        <CommandButton
                            description="Download file from conversation"
                            icon={<ArrowDownloadRegular />}
                            onClick={handleDownload}
                            disabled={submitted}
                        />
                        <CommandButton
                            description="Delete file from conversation"
                            disabled={readOnly}
                            icon={<Delete16Regular />}
                            dialogContent={{
                                title: 'Delete file',
                                content: (
                                    <p>
                                        Are you sure you want to delete <strong>{conversationFile.name}</strong>?
                                    </p>
                                ),
                                closeLabel: 'Cancel',
                                additionalActions: [
                                    <DialogTrigger key="delete" disableButtonEnhancement>
                                        <Button appearance="primary" onClick={handleDelete} disabled={submitted}>
                                            {submitted ? 'Deleting...' : 'Delete'}
                                        </Button>
                                    </DialogTrigger>,
                                ],
                            }}
                        />
                    </div>
                }
            />
        </Card>
    );
};
