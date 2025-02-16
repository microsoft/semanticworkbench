import {
    Accordion,
    AccordionHeader,
    AccordionItem,
    AccordionPanel,
    makeStyles,
    shorthands,
    Text,
    tokens,
} from '@fluentui/react-components';
import { Toolbox24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Conversation } from '../../models/Conversation';
import { ConversationMessage } from '../../models/ConversationMessage';
import { CodeLabel } from '../App/CodeLabel';
import { MessageContent } from './Message/MessageContent';

const useClasses = makeStyles({
    root: {
        backgroundColor: tokens.colorNeutralBackground3,
        borderRadius: tokens.borderRadiusMedium,
        ...shorthands.border('none'),
        ...shorthands.margin(tokens.spacingVerticalM, 0, tokens.spacingVerticalM, tokens.spacingHorizontalXXXL),
    },
    header: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: tokens.spacingHorizontalS,
    },
});

interface ToolResultProps {
    conversation: Conversation;
    message: ConversationMessage;
}

export const ToolResult: React.FC<ToolResultProps> = (props) => {
    const { conversation, message } = props;
    const classes = useClasses();

    const toolCallId = message.metadata?.['tool_result']?.['tool_call_id'] as string;
    const toolCalls: { id: string; name: string }[] = message.metadata?.['tool_calls'];
    const toolName = toolCalls?.find((toolCall) => toolCall.id === toolCallId)?.name;

    const messageContent = <MessageContent message={message} conversation={conversation} />;

    return (
        <div className={classes.root}>
            <Accordion collapsible>
                <AccordionItem value="1">
                    <AccordionHeader icon={<Toolbox24Regular />}>
                        <div className={classes.header}>
                            <Text>Tools call result</Text>
                            <CodeLabel>{toolName}</CodeLabel>
                        </div>
                    </AccordionHeader>
                    <AccordionPanel>{messageContent}</AccordionPanel>
                </AccordionItem>
            </Accordion>
        </div>
    );
};

export const MemoizedToolResultMessage = React.memo(ToolResult);
