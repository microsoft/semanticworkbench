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
                const toolCallId = message.metadata?.['tool_result']?.['tool_call_id'] as string;
                const toolName = toolCall.name;
                const content = JSON.stringify(toolCall.arguments, null, 4);

                return (
                    <Accordion key={toolCallId} collapsible className={classes.item}>
                        <AccordionItem value="1">
                            <AccordionHeader icon={<Toolbox24Regular />}>
                                <div className={classes.header}>
                                    <Text>Calling tool</Text>
                                    <CodeLabel>{toolName}</CodeLabel>
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
