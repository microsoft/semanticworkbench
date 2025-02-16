import { CopilotMessage, SystemMessage, UserMessage } from '@fluentui-copilot/react-copilot';
import { makeStyles, shorthands, tokens } from '@fluentui/react-components';
import {
    AlertUrgent24Regular,
    KeyCommandRegular,
    Note24Regular,
    TextBulletListSquareSparkleRegular,
} from '@fluentui/react-icons';
import React from 'react';
import { Conversation } from '../../../models/Conversation';
import { ConversationMessage } from '../../../models/ConversationMessage';
import { ConversationParticipant } from '../../../models/ConversationParticipant';
import { MessageContent } from './MessageContent';

const useClasses = makeStyles({
    noteContent: {
        backgroundColor: tokens.colorNeutralBackground3,
        borderRadius: tokens.borderRadiusMedium,
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalS),
        ...shorthands.border('none'),
        ...shorthands.margin(0),
    },
    innerContent: {
        maxWidth: '100%',
    },
});

interface ContentRendererProps {
    conversation: Conversation;
    message: ConversationMessage;
    participant: ConversationParticipant;
}

export const ContentRenderer: React.FC<ContentRendererProps> = (props) => {
    const { conversation, message, participant } = props;
    const classes = useClasses();

    const isUser = participant.role === 'user';

    const messageContent = <MessageContent message={message} conversation={conversation} />;

    const renderedContent =
        message.messageType === 'notice' ||
        message.messageType === 'note' ||
        message.messageType === 'command' ||
        message.messageType === 'command-response' ? (
            <NoticeRenderer
                content={messageContent}
                innerClassName={classes.innerContent}
                className={classes.noteContent}
            />
        ) : isUser ? (
            <UserMessage>{messageContent}</UserMessage>
        ) : (
            <CopilotMessage>{messageContent}</CopilotMessage>
        );

    return renderedContent;
};

interface MessageRendererProps {
    content: JSX.Element;
    className?: string;
    innerClassName?: string;
}

const NoticeRenderer: React.FC<MessageRendererProps> = (props) => {
    const { content, className, innerClassName } = props;

    let icon = null;
    switch (className) {
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
        <div className={className}>
            <SystemMessage className={innerClassName} icon={icon} message={content}>
                {content}
            </SystemMessage>
        </div>
    );
};
