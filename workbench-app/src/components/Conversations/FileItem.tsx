// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Caption1,
    Card,
    CardHeader,
    DialogOpenChangeData,
    DialogOpenChangeEvent,
    makeStyles,
    Menu,
    MenuItem,
    MenuList,
    MenuPopover,
    MenuTrigger,
    Text,
} from '@fluentui/react-components';
import { ArrowDownloadRegular, DeleteRegular, MoreHorizontalRegular } from '@fluentui/react-icons';
import React from 'react';
import * as StreamSaver from 'streamsaver';
import { useWorkbenchService } from '../../libs/useWorkbenchService';
import { Utility } from '../../libs/Utility';
import { Conversation } from '../../models/Conversation';
import { ConversationFile } from '../../models/ConversationFile';
import { useDeleteConversationFileMutation } from '../../services/workbench';
import { DialogControl } from '../App/DialogControl';
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
    const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false);

    const time = React.useMemo(
        () => Utility.toFormattedDateString(conversationFile.updated, 'M/D/YYYY h:mm A'),
        [conversationFile.updated],
    );

    const sizeToDisplay = (size: number) => {
        if (size < 1024) {
            return `${size} B`;
        } else if (size < 1024 * 1024) {
            return `${(size / 1024).toFixed(1).toString().replaceAll('.0', '')} KB`;
        } else {
            return `${(size / 1024 / 1024).toFixed(1).toString().replaceAll('.0', '')} MB`;
        }
    };

    const tokenCountToDisplay = (count: number) => {
        const label = `token${count !== 1 ? 's' : ''}`;
        if (count < 1_000) {
            return `${count} ${label}`;
        } else if (count < 1_000_000) {
            return `${(count / 1_000).toFixed(2).toString().replaceAll('.0', '')}k ${label}`;
        } else {
            return `${(count / 1_000_000).toFixed(2).toString().replaceAll('.0', '')}m ${label}`;
        }
    };

    const handleDeleteMenuItemClick = React.useCallback(() => {
        if (deleteDialogOpen) {
            return;
        }
        setDeleteDialogOpen(true);
    }, [deleteDialogOpen]);

    const onDeleteDialogOpenChange = React.useCallback((_: DialogOpenChangeEvent, data: DialogOpenChangeData) => {
        setDeleteDialogOpen(data.open);
    }, []);

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
        <>
            <Card key={conversationFile.name} size="small">
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
                        <Caption1 truncate wrap={false}>
                            {time}
                            <br />
                            {sizeToDisplay(conversationFile.size)}{' '}
                            {conversationFile.metadata?.token_count !== undefined
                                ? `| ${tokenCountToDisplay(conversationFile.metadata?.token_count)}`
                                : ''}
                        </Caption1>
                    }
                    action={
                        <div className={classes.actions}>
                            <Menu>
                                <MenuTrigger disableButtonEnhancement>
                                    <Button icon={<MoreHorizontalRegular />} />
                                </MenuTrigger>
                                <MenuPopover>
                                    <MenuList>
                                        <MenuItem
                                            icon={<ArrowDownloadRegular />}
                                            onClick={handleDownload}
                                            disabled={submitted}
                                        >
                                            Download
                                        </MenuItem>
                                        <MenuItem
                                            icon={<DeleteRegular />}
                                            onClick={handleDeleteMenuItemClick}
                                            disabled={submitted || readOnly}
                                        >
                                            Delete
                                        </MenuItem>
                                    </MenuList>
                                </MenuPopover>
                            </Menu>
                        </div>
                    }
                />
            </Card>
            <DialogControl
                open={deleteDialogOpen}
                onOpenChange={onDeleteDialogOpenChange}
                title="Delete file"
                content={
                    <p>
                        Are you sure you want to delete <strong>{conversationFile.name}</strong>?
                    </p>
                }
                closeLabel="Cancel"
                additionalActions={[
                    <Button appearance="primary" onClick={handleDelete} disabled={submitted} key="delete">
                        {submitted ? 'Deleting...' : 'Delete'}
                    </Button>,
                ]}
            />
        </>
    );
};
