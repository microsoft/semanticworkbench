// Copyright (c) Microsoft. All rights reserved.

import { Attachment, AttachmentList, AttachmentProps } from '@fluentui-copilot/react-attachments';
import { makeStyles } from '@fluentui/react-components';
import debug from 'debug';
import React from 'react';
import { Constants } from '../../Constants';
import { TooltipWrapper } from '../App/TooltipWrapper';
import { ConversationFileIcon } from './ConversationFileIcon';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
    },
    media: {
        maxWidth: '20px',
        maxHeight: '20px',
    },
});

const log = debug(Constants.debug.root).extend('InputAttachmentList');

interface InputAttachmentProps {
    attachments: File[];
    onDismissAttachment: (file: File) => void;
}

export const InputAttachmentList: React.FC<InputAttachmentProps> = (props) => {
    const { attachments, onDismissAttachment } = props;
    const classes = useClasses();

    const attachmentList: AttachmentProps[] = attachments.map((file) => ({
        id: file.name,
        media: <ConversationFileIcon file={file} className={classes.media} />,
        children: (
            <TooltipWrapper content={file.name}>
                <span>{file.name}</span>
            </TooltipWrapper>
        ),
    }));

    return (
        <AttachmentList
            maxVisibleAttachments={3}
            onAttachmentDismiss={(_event, data) => {
                const file = attachments.find((file) => file.name === data.id);
                if (file) {
                    log('Dismissing attachment', file.name);
                    onDismissAttachment(file);
                } else {
                    log('Attachment not found while dismissing', data.id);
                }
            }}
        >
            {attachmentList.map((attachment) => (
                <Attachment id={attachment.id} key={attachment.id} media={attachment.media}>
                    {attachment.children}
                </Attachment>
            ))}
        </AttachmentList>
    );
};
