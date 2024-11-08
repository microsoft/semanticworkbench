// Copyright (c) Microsoft. All rights reserved.

import { Copy24Regular, Info24Regular, Share24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useConversationUtility } from '../../libs/useConversationUtility';
import { Conversation } from '../../models/Conversation';
import { ConversationShare } from '../../models/ConversationShare';
import { CommandButton } from '../App/CommandButton';
import { CopyButton } from '../App/CopyButton';
import { MiniControl } from '../App/MiniControl';
import { MyItemsManager } from '../App/MyItemsManager';
import { ConversationShareCreate } from './ConversationShareCreate';
import { ConversationShareView } from './ConversationShareView';
import { ShareRemove } from './ShareRemove';

interface MySharesProps {
    shares: ConversationShare[];
    title?: string;
    hideInstruction?: boolean;
    conversation?: Conversation;
}

export const MyShares: React.FC<MySharesProps> = (props) => {
    const { shares, hideInstruction, title, conversation } = props;
    const [newOpen, setNewOpen] = React.useState(Boolean(conversation && shares.length === 0));
    const [conversationShareForDetails, setConversationShareForDetails] = React.useState<ConversationShare>();
    const conversationUtility = useConversationUtility();

    const createTitle = 'Create a new share link';

    // The create share button is internal to the MyShares component so that we're always
    // presenting the list of current shares for the conversation in case the user wants to
    // reuse a previously created share link.
    const actions = conversation ? (
        <CommandButton label="New Share" description={createTitle} onClick={() => setNewOpen(true)} />
    ) : (
        <></>
    );

    const titleFor = (share: ConversationShare) => {
        const { shareType } = conversationUtility.getShareType(share);
        return `${share.label} (${shareType.toLowerCase()})`;
    };

    const linkFor = (share: ConversationShare) => {
        return conversationUtility.getShareLink(share);
    };

    return (
        <>
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
                                <CommandButton
                                    icon={<Info24Regular />}
                                    iconOnly
                                    onClick={() => setConversationShareForDetails(share)}
                                    description="View details"
                                />
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
            {newOpen && conversation && (
                <ConversationShareCreate
                    conversation={conversation}
                    onClosed={() => setNewOpen(false)}
                    onCreated={(createdShare) => setConversationShareForDetails(createdShare)}
                />
            )}
            {conversationShareForDetails && (
                <ConversationShareView
                    conversationShare={conversationShareForDetails}
                    showDetails
                    onClosed={() => setConversationShareForDetails(undefined)}
                />
            )}
        </>
    );
};
