// Copyright (c) Microsoft. All rights reserved.

import { Button, Field, Input, Radio, RadioGroup } from '@fluentui/react-components';
import { Copy24Regular, Share24Regular } from '@fluentui/react-icons';
import React from 'react';
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
    const [shareAllowJoin, setShareAllowJoin] = React.useState(true);

    const handleCreate = React.useCallback(async () => {
        const permission = shareAllowJoin ? 'read_write' : 'read';
        const metadata = { showDuplicateAction: true, showJoinAction: shareAllowJoin };
        await createShare({
            conversationId: conversation!.id,
            label: shareLabel,
            conversationPermission: permission,
            metadata: metadata,
        });
    }, [shareAllowJoin, createShare, conversation, shareLabel]);

    const handleDialogOpenChange = React.useCallback(async () => {
        setSubmitted(false);
        setShareLabel(conversation?.title ?? '');
        setShareAllowJoin(true);
    }, [setSubmitted, setShareLabel, conversation]);

    const handleFocus = (event: React.FocusEvent<HTMLInputElement>) => event.target.select();

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
                                        defaultValue={shareAllowJoin ? 'true' : 'false'}
                                        onChange={(_, data) => setShareAllowJoin(data.value === 'true')}
                                        required={true}
                                    >
                                        <Radio
                                            value="true"
                                            label="Invite to join and participate in the conversation"
                                        />
                                        <Radio
                                            value="false"
                                            label="Invite to create a copy of the conversation and assistant(s)"
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
        const showJoinAction = share.metadata['showJoinAction'] === false ? '' : 'join';
        const showDuplicateAction = share.metadata['showDuplicateAction'] === false ? '' : 'duplicate';
        const openMessageAction = share.metadata['openMessageAction'] ? 'join and open message' : '';
        const action = [openMessageAction, showJoinAction, showDuplicateAction].filter((a) => a).join(' or ');

        if (conversation) return `${share.label} ( ${action} )`;
        const title =
            share.label !== share.conversationTitle ? `${share.conversationTitle} : ${share.label}` : share.label;
        return `${title} ( ${action} )`;
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
