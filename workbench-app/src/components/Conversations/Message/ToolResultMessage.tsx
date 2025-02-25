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
import { Conversation } from '../../../models/Conversation';
import { ConversationMessage } from '../../../models/ConversationMessage';
import { useGetConversationMessageDebugDataQuery } from '../../../services/workbench';
import { CodeLabel } from '../../App/CodeLabel';
import { DebugInspector } from '../DebugInspector';
import { MessageDelete } from '../MessageDelete';
import { MessageContent } from './MessageContent';

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
    actions: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
    },
});

interface ToolResultMessageProps {
    conversation: Conversation;
    message: ConversationMessage;
    readOnly: boolean;
}

/**
 * Allows experimental support for displaying tool call results that are attached to a message
 * via the metadata property. To use this, the message must have a metadata property
 * with a 'tool_result' key, which is an object with a 'tool_call_id' key, and a 'tool_calls'
 * key, which is an array of tool calls, each with an 'id', 'name', and 'arguments' property.
 * The result of the tool call should be in the message content.
 *
 * [Read more about special metadata support in UX...](../../../docs/MESSAGE_METADATA.md)
 *
 * This component will display each tool call result in an accordion, with the tool name
 * as the header and the result as the content.
 */
export const ToolResultMessage: React.FC<ToolResultMessageProps> = (props) => {
    const { conversation, message, readOnly } = props;
    const classes = useClasses();

    const [skipDebugLoad, setSkipDebugLoad] = React.useState(true);
    const {
        data: debugData,
        isLoading: isLoadingDebugData,
        isUninitialized: isUninitializedDebugData,
    } = useGetConversationMessageDebugDataQuery(
        { conversationId: conversation.id, messageId: message.id },
        { skip: skipDebugLoad },
    );

    const toolCallId = message.metadata?.['tool_result']?.['tool_call_id'] as string;
    const toolCalls: { id: string; name: string }[] = message.metadata?.['tool_calls'];
    const toolName = toolCalls?.find((toolCall) => toolCall.id === toolCallId)?.name;

    const messageContent = React.useMemo(
        () => <MessageContent message={message} conversation={conversation} />,
        [message, conversation],
    );

    return (
        <div className={classes.root}>
            <Accordion collapsible>
                <AccordionItem value="1">
                    <AccordionHeader icon={<Toolbox24Regular />}>
                        <div className={classes.header}>
                            <Text>Received tool result </Text>
                            <CodeLabel>{toolName}</CodeLabel>
                        </div>
                    </AccordionHeader>
                    <AccordionPanel>{messageContent}</AccordionPanel>
                </AccordionItem>
            </Accordion>
            <div className={classes.actions}>
                <DebugInspector
                    debug={message.hasDebugData ? debugData?.debugData || { loading: true } : undefined}
                    loading={isLoadingDebugData || isUninitializedDebugData}
                    onOpen={() => {
                        setSkipDebugLoad(false);
                    }}
                />
                {!readOnly && (
                    <>
                        <MessageDelete conversationId={conversation.id} message={message} />
                    </>
                )}
            </div>
        </div>
    );
};

export const MemoizedToolResultMessage = React.memo(ToolResultMessage);
