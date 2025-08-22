// Copyright (c) Microsoft. All rights reserved.

import {
    Accordion,
    AccordionHeader,
    AccordionItem,
    AccordionPanel,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import { ChevronDownRegular } from '@fluentui/react-icons';
import React from 'react';
import { Conversation } from '../../../models/Conversation';
import { ConversationMessage } from '../../../models/ConversationMessage';
import { ConversationParticipant } from '../../../models/ConversationParticipant';
import { MemoizedInteractMessage } from './InteractMessage';
import { MemoizedToolResultMessage } from './ToolResultMessage';

const useClasses = makeStyles({
    root: {
        backgroundColor: tokens.colorNeutralBackground2,
        borderRadius: tokens.borderRadiusMedium,
        ...shorthands.border('1px', 'solid', tokens.colorNeutralStroke2),
        ...shorthands.margin(tokens.spacingVerticalXS, 0),
    },
    header: {
        ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
        fontSize: tokens.fontSizeBase200,
        color: tokens.colorNeutralForeground3,
    },
    panel: {
        ...shorthands.padding(0, tokens.spacingHorizontalM, tokens.spacingVerticalS),
    },
    messageItem: {
        ...shorthands.margin(tokens.spacingVerticalXS, 0),
        '&:last-child': {
            marginBottom: 0,
        },
    },
});

interface NotificationAccordionProps {
    messages: ConversationMessage[];
    participants: ConversationParticipant[];
    conversation: Conversation;
    readOnly: boolean;
    onRead?: (message: ConversationMessage) => void;
    onVisible?: (message: ConversationMessage) => void;
    onRewindToBefore?: (message: ConversationMessage, redo: boolean) => Promise<void>;
}

export const NotificationAccordion: React.FC<NotificationAccordionProps> = (props) => {
    const { messages, participants, conversation, readOnly, onRead, onVisible, onRewindToBefore } = props;
    const classes = useClasses();
    const [isOpen, setIsOpen] = React.useState(false);

    if (messages.length === 0) return null;

    // Create a summary for the accordion header
    const getSummary = () => {
        const count = messages.length;
        return `${count} notice${count === 1 ? '' : 's'}`;
    };

    return (
        <div className={classes.root}>
            <Accordion collapsible>
                <AccordionItem value="notifications">
                    <AccordionHeader
                        className={classes.header}
                        expandIcon={<ChevronDownRegular />}
                        onClick={() => setIsOpen(!isOpen)}
                    >
                        <span>{getSummary()}</span>
                    </AccordionHeader>
                    <AccordionPanel className={classes.panel}>
                        {messages.map((message) => {
                            const messageParticipant = participants.find(
                                p => p.id === message.sender.participantId,
                            );
                            
                            if (!messageParticipant) return null;

                            // Check if this is a tool result message
                            const isToolResult = message.messageType === 'note' && message.metadata?.['tool_result'];

                            const messageContent = isToolResult ? (
                                <MemoizedToolResultMessage 
                                    conversation={conversation} 
                                    message={message} 
                                    readOnly={readOnly} 
                                />
                            ) : (
                                <MemoizedInteractMessage
                                    readOnly={readOnly}
                                    conversation={conversation}
                                    message={message}
                                    participant={messageParticipant}
                                    hideParticipant={true} // Always hide participant in accordion
                                    displayDate={false} // Don't show date for individual messages
                                    onRead={onRead}
                                    onVisible={onVisible}
                                    onRewind={onRewindToBefore}
                                />
                            );

                            return (
                                <div key={message.id} className={classes.messageItem}>
                                    {messageContent}
                                </div>
                            );
                        })}
                    </AccordionPanel>
                </AccordionItem>
            </Accordion>
        </div>
    );
};

export const MemoizedNotificationAccordion = React.memo(NotificationAccordion);