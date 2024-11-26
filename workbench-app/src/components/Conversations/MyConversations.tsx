// Copyright (c) Microsoft. All rights reserved.

import { Chat24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Conversation } from '../../models/Conversation';
import { useAppSelector } from '../../redux/app/hooks';
import { useGetAssistantsQuery, useGetConversationsQuery } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';
import { MiniControl } from '../App/MiniControl';
import { MyItemsManager } from '../App/MyItemsManager';
import { ConversationCreate } from './ConversationCreate';
import { ConversationDuplicate } from './ConversationDuplicate';
import { ConversationExport } from './ConversationExport';
import { ConversationRemove } from './ConversationRemove';
import { ConversationRename } from './ConversationRename';
import { ConversationShare } from './ConversationShare';
import { ConversationsImport } from './ConversationsImport';

interface MyConversationsProps {
    conversations?: Conversation[];
    participantId: string;
    title?: string;
    hideInstruction?: boolean;
    onCreate?: (conversation: Conversation) => void;
}

export const MyConversations: React.FC<MyConversationsProps> = (props) => {
    const { conversations, title, hideInstruction, onCreate, participantId } = props;
    const { refetch: refetchAssistants } = useGetAssistantsQuery();
    const { refetch: refetchConversations } = useGetConversationsQuery();
    const [conversationCreateOpen, setConversationCreateOpen] = React.useState(false);
    const localUserId = useAppSelector((state) => state.localUser.id);

    const handleConversationCreate = async (conversation: Conversation) => {
        await refetchConversations();
        onCreate?.(conversation);
    };

    const handleConversationsImport = async (_conversationIds: string[]) => {
        await refetchAssistants();
        await refetchConversations();
    };

    return (
        <MyItemsManager
            items={conversations
                ?.toSorted((a, b) => a.title.toLocaleLowerCase().localeCompare(b.title.toLocaleLowerCase()))
                .map((conversation) => (
                    <MiniControl
                        key={conversation.id}
                        icon={<Chat24Regular />}
                        label={conversation.title}
                        linkUrl={`/${encodeURIComponent(conversation.id)}`}
                        actions={
                            <>
                                <ConversationRename
                                    disabled={conversation.ownerId !== localUserId}
                                    conversationId={conversation.id}
                                    value={conversation.title}
                                    iconOnly
                                />
                                <ConversationExport conversationId={conversation.id} iconOnly />
                                <ConversationDuplicate conversationId={conversation.id} iconOnly />
                                <ConversationShare conversation={conversation} iconOnly />
                                <ConversationRemove
                                    conversations={conversation}
                                    participantId={participantId}
                                    iconOnly
                                />
                            </>
                        }
                    />
                ))}
            title={title ?? 'My Conversations'}
            itemLabel="Conversation"
            hideInstruction={hideInstruction}
            actions={
                <>
                    <CommandButton
                        icon={<Chat24Regular />}
                        label={`New Conversation`}
                        description={`Create a new conversation`}
                        onClick={() => setConversationCreateOpen(true)}
                    />
                    <ConversationCreate
                        open={conversationCreateOpen}
                        onOpenChange={(open) => setConversationCreateOpen(open)}
                        onCreate={handleConversationCreate}
                    />
                    <ConversationsImport onImport={handleConversationsImport} />
                </>
            }
        />
    );
};
