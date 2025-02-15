import { CopilotMessage, SystemMessage, UserMessage } from '@fluentui-copilot/react-copilot';
import {
    AlertUrgent24Regular,
    KeyCommandRegular,
    Note24Regular,
    TextBulletListSquareSparkleRegular,
} from '@fluentui/react-icons';
import React from 'react';

interface MessageRendererProps {
    content: JSX.Element;
    innerContentClass: string;
    noteStyle?: string;
}

export const NoticeMessage: React.FC<MessageRendererProps> = ({ content, innerContentClass, noteStyle = '' }) => {
    let icon = null;
    switch (noteStyle) {
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
        <div className={noteStyle}>
            <SystemMessage className={innerContentClass} icon={icon} message={content}>
                {content}
            </SystemMessage>
        </div>
    );
};

export const UserMessageRenderer: React.FC<{ content: JSX.Element }> = ({ content }) => {
    return <UserMessage>{content}</UserMessage>;
};

export const CopilotMessageRenderer: React.FC<{ content: JSX.Element }> = ({ content }) => {
    return <CopilotMessage>{content}</CopilotMessage>;
};
