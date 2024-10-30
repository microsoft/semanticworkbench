// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogTrigger } from '@fluentui/react-components';
import { Delete24Regular } from '@fluentui/react-icons';
import React from 'react';
import { ConversationShare } from '../../models/ConversationShare';
import { useDeleteShareMutation } from '../../services/workbench/share';
import { CommandButton } from '../App/CommandButton';

interface ShareRemoveProps {
    share: ConversationShare;
    onRemove?: () => void;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const ShareRemove: React.FC<ShareRemoveProps> = (props) => {
    const { share, onRemove: onDelete, iconOnly, asToolbarButton } = props;
    const [deleteShare] = useDeleteShareMutation();
    const [isDeleting, setIsDeleting] = React.useState(false);

    const handleDelete = React.useCallback(async () => {
        setIsDeleting(true);
        await deleteShare(share.id);
        onDelete?.();
    }, [share.id, onDelete, deleteShare, setIsDeleting]);

    return (
        <CommandButton
            description="Delete share"
            icon={<Delete24Regular />}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
            label="Delete"
            disabled={isDeleting}
            dialogContent={{
                title: 'Delete Share',
                content: <p>Are you sure you want to delete this share?</p>,
                closeLabel: 'Cancel',
                additionalActions: [
                    <DialogTrigger key="delete" disableButtonEnhancement>
                        <Button appearance="primary" onClick={handleDelete}>
                            Delete
                        </Button>
                    </DialogTrigger>,
                ],
            }}
        />
    );
};
