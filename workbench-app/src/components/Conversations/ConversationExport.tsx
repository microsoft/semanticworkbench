// Copyright (c) Microsoft. All rights reserved.

import { ProgressBar } from '@fluentui/react-components';
import React from 'react';
import { useExportUtility } from '../../libs/useExportUtility';
import { useNotify } from '../../libs/useNotify';
import { Utility } from '../../libs/Utility';
import { ContentExport } from '../App/ContentExport';
import { DialogControl } from '../App/DialogControl';

interface ConversationExportWithStatusDialogProps {
    conversationId?: string;
    onExport: (id: string) => Promise<void>;
}

export const ConversationExportWithStatusDialog: React.FC<ConversationExportWithStatusDialogProps> = (props) => {
    const { conversationId, onExport } = props;
    const { exportConversation } = useExportUtility();
    const { notifyWarning } = useNotify();
    const [submitted, setSubmitted] = React.useState(false);

    const handleError = React.useCallback(
        (error: Error) => {
            notifyWarning({
                id: 'error',
                title: 'Export conversation failed',
                message: error.message,
            });
        },
        [notifyWarning],
    );

    React.useEffect(() => {
        if (!conversationId) {
            return;
        }

        (async () => {
            try {
                await Utility.withStatus(setSubmitted, async () => {
                    await exportConversation(conversationId);
                    await onExport(conversationId);
                });
            } catch (error) {
                handleError(error as Error);
            }
        })();
    }, [conversationId, exportConversation, handleError, notifyWarning, onExport]);

    return (
        <DialogControl
            open={submitted}
            title="Exporting Conversation"
            hideDismissButton
            content={
                <p>
                    <ProgressBar />
                </p>
            }
        />
    );
};

interface ConversationExportProps {
    conversationId: string;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const ConversationExport: React.FC<ConversationExportProps> = (props) => {
    const { conversationId, iconOnly, asToolbarButton } = props;
    const { exportConversationFunction } = useExportUtility();

    return (
        <ContentExport
            id={conversationId}
            contentTypeLabel="conversation"
            exportFunction={exportConversationFunction}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
        />
    );
};
