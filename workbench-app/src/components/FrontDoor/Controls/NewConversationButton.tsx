import { Button } from '@fluentui/react-components';
import { ChatAddRegular } from '@fluentui/react-icons';
import React from 'react';
import { Conversation } from '../../../models/Conversation';
import { useAppDispatch } from '../../../redux/app/hooks';
import { setActiveConversationId } from '../../../redux/features/app/appSlice';
import { useGetConversationsQuery } from '../../../services/workbench';
import { ConversationCreate } from '../../Conversations/ConversationCreate';

export const NewConversationButton: React.FC = () => {
    const { refetch: refetchConversations } = useGetConversationsQuery();
    const [conversationCreateOpen, setConversationCreateOpen] = React.useState(false);
    const dispatch = useAppDispatch();

    const handleConversationCreate = async (conversation: Conversation) => {
        await refetchConversations();
        dispatch(setActiveConversationId(conversation.id));
    };

    return (
        <>
            <Button icon={<ChatAddRegular />} onClick={() => setConversationCreateOpen(true)} />
            <ConversationCreate
                open={conversationCreateOpen}
                onOpenChange={(open) => setConversationCreateOpen(open)}
                onCreate={handleConversationCreate}
            />
        </>
    );
};
