import { SystemMessage } from '@fluentui-copilot/react-copilot';
import {
    AlertUrgent24Regular,
    KeyCommandRegular,
    Note24Regular,
    TextBulletListSquareSparkleRegular,
} from '@fluentui/react-icons';
import React from 'react';
import { Conversation } from '../../../models/Conversation';
import { ConversationMessage } from '../../../models/ConversationMessage';
import { AssistantCard } from '../../FrontDoor/Controls/AssistantCard';
import { MessageContent } from './MessageContent';

interface ContentRendererProps {
    conversation: Conversation;
    message: ConversationMessage;
}

export const ContentRenderer: React.FC<ContentRendererProps> = (props) => {
    const { conversation, message } = props;

    const appComponent = message.metadata?._appComponent;
    if (appComponent) {
        switch (appComponent.type) {
            case 'AssistantCard':
                return (
                    <AssistantCard
                        assistantServiceId={appComponent.props.assistantServiceId}
                        templateId={appComponent.props.templateId}
                        existingConversationId={appComponent.props.existingConversationId}
                        participantMetadata={appComponent.props.participantMetadata}
                        hideContent
                    />
                );
            default:
                return null;
        }
    }

    const messageContent = <MessageContent message={message} conversation={conversation} />;

    const renderedContent =
        message.messageType === 'notice' ||
        message.messageType === 'note' ||
        message.messageType === 'command' ||
        message.messageType === 'command-response' ? (
            <NoticeRenderer content={messageContent} messageType={message.messageType} />
        ) : (
            messageContent
        );

    return renderedContent;
};

interface MessageRendererProps {
    content: JSX.Element;
    messageType: string;
}

const NoticeRenderer: React.FC<MessageRendererProps> = (props) => {
    const { content, messageType } = props;

    let icon = null;
    switch (messageType) {
        case 'notice':
            icon = <AlertUrgent24Regular />;
            break;
        case 'note':
            icon = <Note24Regular />;
            break;
        case 'command':
            icon = <KeyCommandRegular />;
            break;
        case 'command-response':
            icon = <TextBulletListSquareSparkleRegular />;
            break;
        default:
            break;
    }

    return (
        <SystemMessage icon={icon} message={content}>
            {content}
        </SystemMessage>
    );
};
