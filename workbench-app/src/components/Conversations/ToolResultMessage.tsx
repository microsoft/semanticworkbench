import {
    Accordion,
    AccordionHeader,
    AccordionItem,
    AccordionPanel,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import { Toolbox24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Conversation } from '../../models/Conversation';
import { ConversationMessage } from '../../models/ConversationMessage';
import { MessageContent } from './Message/MessageContent';

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

interface ToolResultMessageProps {
    conversation: Conversation;
    message: ConversationMessage;
}

export const ToolResultMessage: React.FC<ToolResultMessageProps> = (props) => {
    const { conversation, message } = props;
    const classes = useClasses();

    const toolCallId = message.metadata?.['tool_result']?.['tool_call_id'] as string;
    const toolCalls: { id: string; name: string }[] = message.metadata?.['tool_calls'] as {
        id: string;
        name: string;
    }[];
    const toolName = toolCalls?.find((toolCall) => toolCall.id === toolCallId)?.name;

    const messageContent = <MessageContent message={message} conversation={conversation} />;

    return (
        <div className={classes.noteContent}>
            <Accordion collapsible>
                <AccordionItem value="1">
                    <AccordionHeader icon={<Toolbox24Regular />}>Tools call result for `{toolName}`</AccordionHeader>
                    <AccordionPanel>{messageContent}</AccordionPanel>
                </AccordionItem>
            </Accordion>
        </div>
    );
};

export const MemoizedToolResultMessage = React.memo(ToolResultMessage);
