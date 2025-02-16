import React from 'react';

import { Conversation } from '../../../models/Conversation';
import { ConversationMessage } from '../../../models/ConversationMessage';
import { useCreateConversationMessageMutation } from '../../../services/workbench';
import { ContentRenderer } from '../ContentRenderers/ContentRenderer';

interface MessageContentProps {
    conversation: Conversation;
    message: ConversationMessage;
}

export const MessageContent: React.FC<MessageContentProps> = (props) => {
    const { conversation, message } = props;

    const [createConversationMessage] = useCreateConversationMessageMutation();

    const onSubmit = async (data: string) => {
        if (message.metadata?.command) {
            await createConversationMessage({
                conversationId: conversation.id,
                content: JSON.stringify({
                    command: message.metadata.command,
                    parameters: data,
                }),
                messageType: 'command',
            });
        }
    };

    return (
        <ContentRenderer
            content={message.content}
            contentType={message.contentType}
            metadata={message.metadata}
            onSubmit={onSubmit}
        />
    );
};
