// Copyright (c) Microsoft. All rights reserved.

import { Button, Field, Input, Radio, RadioGroup } from '@fluentui/react-components';
import { Copy24Regular, Share24Regular } from '@fluentui/react-icons';
import React from 'react';
import { ConversationShareType, useConversationUtility } from '../../libs/useConversationUtility';
import { Conversation } from '../../models/Conversation';
import { ConversationShare } from '../../models/ConversationShare';
import { useCreateShareMutation } from '../../services/workbench/share';
import { CommandButton } from '../App/CommandButton';
import { CopyButton } from '../App/CopyButton';
import { MiniControl } from '../App/MiniControl';
import { MyItemsManager } from '../App/MyItemsManager';
import { ShareRemove } from './ShareRemove';

interface MySharesProps {
    shares: ConversationShare[];
    title?: string;
    hideInstruction?: boolean;
    conversation?: Conversation;
}

export const MyShares: React.FC<MySharesProps> = (props) => {
    const { shares, hideInstruction, title, conversation } = props;
    const [createShare] = useCreateShareMutation();
    const [submitted, setSubmitted] = React.useState(false);
    const [shareLabel, setShareLabel] = React.useState(conversation?.title ?? '');
    const [shareType, setShareType] = React.useState(ConversationShareType.InvitedToParticipate);
    const conversationUtility = useConversationUtility();

    const handleCreate = React.useCallback(async () => {
        // Get the permission and metadata for the share type.
        const { permission, metadata } = conversationUtility.getShareTypeMetadata(shareType);
        // Create the share.
        await createShare({
            conversationId: conversation!.id,
            label: shareLabel,
            conversationPermission: permission,
            metadata: metadata,
        });
    }, [createShare, conversation, shareLabel, shareType, conversationUtility]);

    const handleDialogOpenChange = React.useCallback(async () => {
        setSubmitted(false);
        setShareLabel(conversation?.title ?? '');
        setShareType(ConversationShareType.InvitedToParticipate);
    }, [setSubmitted, setShareLabel, conversation]);

    const handleFocus = (event: React.FocusEvent<HTMLInputElement>) => event.target.select();

    // The create share button is internal to the MyShares component so that we're always
    // presenting the list of current shares for the conversation in case the user wants to
    // reuse a previously created share link.
    const actions = conversation ? (
        <>
            <CommandButton
                label="New Share"
                description="Create a new share"
                dialogContent={{
                    title: 'Create a share',
                    content: (
                        <>
                            <p>
                                <Field label="Label for display in your Shared links list" required={true}>
                                    <Input
                                        disabled={submitted}
                                        value={shareLabel}
                                        onChange={(_event, data) => setShareLabel(data.value)}
                                        onFocus={handleFocus}
                                        required={true}
                                    />
                                </Field>
                            </p>
                            <p>
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
                                        <Radio
                                            value={ConversationShareType.InvitedToDuplicate}
                                            label={`${ConversationShareType.InvitedToDuplicate} the conversation (read-only)`}
                                        />
                                    </RadioGroup>
                                </Field>
                            </p>
                        </>
                    ),
                    closeLabel: 'Cancel',
                    additionalActions: [
                        <Button
                            key="create"
                            disabled={!shareLabel || submitted}
                            onClick={handleCreate}
                            appearance="primary"
                        >
                            {submitted ? 'Creating...' : 'Create'}
                        </Button>,
                    ],
                    onOpenChange: handleDialogOpenChange,
                }}
            />
        </>
    ) : (
        <></>
    );

    const titleFor = (share: ConversationShare) => {
        const shareType = conversationUtility.getShareType(share);
        return `${share.label} (${shareType.toLowerCase()})`;
    };

    const linkFor = (share: ConversationShare) => {
        return `${window.location.origin}/conversation-share/${encodeURIComponent(share.id)}/redeem`;
    };

    return (
        <MyItemsManager
            items={shares.map((share) => (
                <MiniControl
                    key={share.id}
                    icon={<Share24Regular />}
                    label={titleFor(share)}
                    linkUrl={linkFor(share)}
                    tooltip="Open share link"
                    actions={
                        <>
                            <CopyButton data={linkFor(share)} icon={<Copy24Regular />} tooltip="Copy share link" />
                            <ShareRemove share={share} iconOnly />
                        </>
                    }
                />
            ))}
            title={title ?? 'My Shared Links'}
            itemLabel="Share Link"
            hideInstruction={hideInstruction}
            actions={actions}
        />
    );
};
