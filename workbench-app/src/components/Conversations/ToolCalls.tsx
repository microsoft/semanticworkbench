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
import { ConversationMessage } from '../../models/ConversationMessage';
import { CodeLabel } from '../App/CodeLabel';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
    },
    item: {
        backgroundColor: tokens.colorNeutralBackground3,
        borderRadius: tokens.borderRadiusMedium,
        ...shorthands.border('none'),
        marginTop: tokens.spacingVerticalM,
    },
    header: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: tokens.spacingHorizontalS,
    },
});

interface ToolCallsProps {
    message: ConversationMessage;
}

/**
 * Allows experimental support for displaying tool calls that are attached to a message
 * via the metadata property. To use this, the message must have a metadata property
 * with a 'tool_calls' key, which is an array of tool calls, each with an 'id', 'name',
 * and 'arguments' property.
 *
 * [Read more about special metadata support in UX...](../../../docs/MESSAGE_METADATA.md)
 *
 * This component will display each tool call in an accordion, with the tool name
 * as the header and the arguments as the content.
 */
export const ToolCalls: React.FC<ToolCallsProps> = (props) => {
    const { message } = props;
    const classes = useClasses();

    const toolCalls: { id: string; name: string; arguments: string }[] = message.metadata?.['tool_calls'];

    if (!toolCalls || toolCalls.length === 0) {
        return null;
    }

    return (
        <div className={classes.root}>
            {toolCalls.map((toolCall) => {
                const content = JSON.stringify(toolCall.arguments, null, 4);

                return (
                    <Accordion key={toolCall.id} collapsible className={classes.item}>
                        <AccordionItem value="1">
                            <AccordionHeader icon={<Toolbox24Regular />}>
                                <div className={classes.header}>
                                    <Text>Invoking tool</Text>
                                    <CodeLabel>{toolCall.name}</CodeLabel>
                                </div>
                            </AccordionHeader>
                            <AccordionPanel>{content}</AccordionPanel>
                        </AccordionItem>
                    </Accordion>
                );
            })}
        </div>
    );
};

export const MemoizedToolResultMessage = React.memo(ToolCalls);
