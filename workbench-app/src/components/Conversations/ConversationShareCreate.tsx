// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    DialogOpenChangeData,
    DialogOpenChangeEvent,
    Field,
    Input,
    makeStyles,
    Radio,
    RadioGroup,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { ConversationShareType, useConversationUtility } from '../../libs/useConversationUtility';
import { Conversation } from '../../models/Conversation';
import { ConversationShare } from '../../models/ConversationShare';
import { useCreateShareMutation } from '../../services/workbench/share';
import { DialogControl } from '../App/DialogControl';

const useClasses = makeStyles({
    dialogContent: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
});

interface ConversationShareCreateProps {
    conversation: Conversation;
    linkToMessageId?: string;
    onCreated?: (conversationShare: ConversationShare) => void;
    onClosed?: () => void;
}

export const ConversationShareCreate: React.FC<ConversationShareCreateProps> = (props) => {
    const { conversation, linkToMessageId, onCreated, onClosed } = props;
    const classes = useClasses();
    const [createShare] = useCreateShareMutation();
    const [submitted, setSubmitted] = React.useState(false);
    const defaultShareLabel = conversation.title + (linkToMessageId ? ' - message link' : '');
    const [shareLabel, setShareLabel] = React.useState(defaultShareLabel);
    const defaultShareType = ConversationShareType.InvitedToParticipate;
    const [shareType, setShareType] = React.useState(defaultShareType);
    const conversationUtility = useConversationUtility();

    const handleCreate = React.useCallback(async () => {
        setSubmitted(true);
        // Get the permission and metadata for the share type.
        const { permission, metadata } = conversationUtility.getShareTypeMetadata(shareType, linkToMessageId);
        // Create the share.
        const conversationShare = await createShare({
            conversationId: conversation!.id,
            label: shareLabel,
            conversationPermission: permission,
            metadata: metadata,
        }).unwrap();
        onCreated?.(conversationShare);
        setSubmitted(false);
    }, [
        conversationUtility,
        shareType,
        linkToMessageId,
        createShare,
        conversation,
        shareLabel,
        setSubmitted,
        onCreated,
    ]);

    const handleFocus = (event: React.FocusEvent<HTMLInputElement>) => event.target.select();

    const createTitle = linkToMessageId ? 'Create a new message share link' : 'Create a new share link';

    const handleOpenChange = React.useCallback(
        (_: DialogOpenChangeEvent, data: DialogOpenChangeData) => {
            if (!data.open) {
                onClosed?.();
            }
        },
        [onClosed],
    );

    return (
        <DialogControl
            defaultOpen={true}
            onOpenChange={handleOpenChange}
            title={createTitle}
            classNames={{
                dialogContent: classes.dialogContent,
            }}
            content={
                <>
                    <Field label="Label for display in your Shared links list" required={true}>
                        <Input
                            disabled={submitted}
                            value={shareLabel}
                            onChange={(_event, data) => setShareLabel(data.value)}
                            onFocus={handleFocus}
                            required={true}
                        />
                    </Field>
                    <Field label="Permissions" required={true}>
                        <RadioGroup
                            defaultValue={shareType}
                            onChange={(_, data) => setShareType(data.value as ConversationShareType)}
                            required={true}
                        >
                            <Radio
                                value={ConversationShareType.InvitedToParticipate}
                                label={`${ConversationShareType.InvitedToParticipate} in the conversation (read/write)`}
                            />
                            <Radio
                                value={ConversationShareType.InvitedToObserve}
                                label={`${ConversationShareType.InvitedToObserve} the conversation (read-only)`}
                            />
                            {!linkToMessageId && (
                                <Radio
                                    value={ConversationShareType.InvitedToDuplicate}
                                    label={`${ConversationShareType.InvitedToDuplicate} the conversation (read-only)`}
                                />
                            )}
                        </RadioGroup>
                    </Field>
                </>
            }
            closeLabel="Cancel"
            additionalActions={[
                <Button key="create" disabled={!shareLabel || submitted} onClick={handleCreate} appearance="primary">
                    {submitted ? 'Creating...' : 'Create'}
                </Button>,
            ]}
        />
    );
};
