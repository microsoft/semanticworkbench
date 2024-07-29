// Copyright (c) Microsoft. All rights reserved.

import { Button, Caption1, Card, CardHeader, DialogTrigger, Text, makeStyles } from '@fluentui/react-components';
import { Delete16Regular } from '@fluentui/react-icons';
import dayjs from 'dayjs';
import timezone from 'dayjs/plugin/timezone';
import utc from 'dayjs/plugin/utc';
import React from 'react';
import { ConversationFile } from '../../models/ConversationFile';
import { useDeleteConversationFileMutation } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';

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
    conversationId: string;
    file: ConversationFile;
}

export const FileItem: React.FC<FileItemProps> = (props) => {
    const { conversationId, file } = props;
    const classes = useClasses();
    const [deleteConversationFile] = useDeleteConversationFileMutation();

    const time = dayjs.utc(file.updated).tz(dayjs.tz.guess()).format('M/D/YYYY h:mm A');

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
        await deleteConversationFile({ conversationId, filename: file.name });
    };

    return (
        <Card
            key={file.name}
            floatingAction={
                <CommandButton
                    description="Delete file"
                    icon={<Delete16Regular />}
                    iconOnly
                    dialogContent={{
                        title: 'Delete file',
                        content: (
                            <>
                                Are you sure you want to delete <strong>{file.name}</strong>?
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
            }
        >
            <CardHeader
                header={<Text weight="semibold">{file.name}</Text>}
                description={
                    <div className={classes.details}>
                        <Caption1>{time}</Caption1>
                        <Caption1>
                            {sizeToDisplay(file.size)} / {file.contentType}
                        </Caption1>
                    </div>
                }
            />
        </Card>
    );
};
