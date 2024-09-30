// Copyright (c) Microsoft. All rights reserved.

import { Button, Dropdown, Option, makeStyles, tokens } from '@fluentui/react-components';
import { ChatAddRegular } from '@fluentui/react-icons';
import React from 'react';
import { ConversationDefinition, WorkflowDefinition } from '../../../models/WorkflowDefinition';
import { ConversationDefinitionCreate } from './ConversationDefinitionCreate';

const useClasses = makeStyles({
    row: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: tokens.spacingHorizontalS,
    },
});

interface WorkflowStateConversationProps {
    workflowDefinition: WorkflowDefinition;
    stateIdToEdit: string;
    onChange: (newValue: WorkflowDefinition) => void;
}

export const WorkflowStateConversation: React.FC<WorkflowStateConversationProps> = (props) => {
    const { workflowDefinition, stateIdToEdit, onChange } = props;
    const classes = useClasses();
    const [open, setOpen] = React.useState(false);

    const stateToEdit = workflowDefinition.states.find((state) => state.id === stateIdToEdit);
    if (!stateToEdit) {
        throw new Error(`State not found: ${stateIdToEdit}`);
    }

    const conversationDefinitions = workflowDefinition.definitions.conversations;

    const handleConversationDefinitionChange = (newValue: string) => {
        onChange({
            ...workflowDefinition,
            states: workflowDefinition.states.map((state) => {
                if (state.id === stateIdToEdit) {
                    return {
                        ...state,
                        conversationDefinitionId: newValue,
                    };
                }
                return state;
            }),
        });
    };

    const handleConversationDefinitionCreate = (conversationDefinition: ConversationDefinition) => {
        onChange({
            ...workflowDefinition,
            definitions: {
                ...workflowDefinition.definitions,
                conversations: workflowDefinition.definitions.conversations.concat(conversationDefinition),
            },
            states: workflowDefinition.states.map((state) => {
                if (state.id === stateIdToEdit) {
                    return {
                        ...state,
                        conversationDefinitionId: conversationDefinition.id,
                    };
                }
                return state;
            }),
        });

        setOpen(false);
    };

    const sortedConversationDefinitions = conversationDefinitions.toSorted((a, b) =>
        a.title.toLocaleLowerCase().localeCompare(b.title.toLocaleLowerCase()),
    );

    return (
        <>
            <div className={classes.row}>
                <Dropdown
                    disabled={stateToEdit.id === workflowDefinition.startStateId}
                    placeholder="Select a conversation"
                    value={
                        sortedConversationDefinitions.find(
                            (conversationDefinition) =>
                                conversationDefinition.id === stateToEdit.conversationDefinitionId,
                        )?.title
                    }
                    selectedOptions={[stateToEdit.conversationDefinitionId]}
                    onOptionSelect={(_event, data) => handleConversationDefinitionChange(data.optionValue as string)}
                >
                    {sortedConversationDefinitions.map((conversationDefinition) => (
                        <Option key={conversationDefinition.id} value={conversationDefinition.id}>
                            {conversationDefinition.title}
                        </Option>
                    ))}
                </Dropdown>
                <ConversationDefinitionCreate
                    open={open}
                    onOpenChange={setOpen}
                    onCreate={handleConversationDefinitionCreate}
                />
                <Button
                    disabled={stateToEdit.id === workflowDefinition.startStateId}
                    icon={<ChatAddRegular />}
                    onClick={() => setOpen(true)}
                >
                    New conversation
                </Button>
            </div>
        </>
    );
};
