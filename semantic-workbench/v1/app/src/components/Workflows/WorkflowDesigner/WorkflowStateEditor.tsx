// Copyright (c) Microsoft. All rights reserved.

import {
    Card,
    Checkbox,
    Field,
    Input,
    MessageBar,
    MessageBarBody,
    Text,
    Tooltip,
    makeStyles,
    tokens,
} from '@fluentui/react-components';
import { QuestionCircle16Regular } from '@fluentui/react-icons';
import React from 'react';
import { WorkflowDefinition, WorkflowState } from '../../../models/WorkflowDefinition';
import { WorkflowStateAssistants } from './WorkflowStateAssistants';
import { WorkflowStateConversation } from './WorkflowStateConversation';
import { WorkflowStateOutlets } from './WorkflowStateOutlets';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalXL,
    },
    card: {
        backgroundColor: tokens.colorNeutralBackground2,
    },
    section: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
    infoItem: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: 0,
    },
});

export const isValidWorkflowStateData = (
    value: WorkflowState,
): {
    isValid: boolean;
    errors: string[];
} => {
    const errors: string[] = [];
    if (!value.label) {
        errors.push('Label is required');
    }
    if (!value.conversationDefinitionId) {
        errors.push('Conversation is required');
    }
    if (value.outlets.length === 0) {
        errors.push('At least one outlet is required');
    }
    if (value.assistantDataList.length === 0) {
        errors.push('At least one assistant is required');
    }
    return {
        isValid: errors.length === 0,
        errors,
    };
};

interface WorkflowStateEditorProps {
    workflowDefinition: WorkflowDefinition;
    stateIdToEdit: string;
    onChange: (newValue: WorkflowDefinition) => void;
}

export const WorkflowStateEditor: React.FC<WorkflowStateEditorProps> = (props) => {
    const { workflowDefinition, stateIdToEdit, onChange } = props;
    const classes = useClasses();

    const stateToEdit = workflowDefinition.states.find((state) => state.id === stateIdToEdit);
    if (!stateToEdit) {
        throw new Error(`State not found: ${stateIdToEdit}`);
    }

    const checkValid = isValidWorkflowStateData(stateToEdit);

    const handleStateChange = (updatedState: WorkflowState) => {
        const stateIndex = workflowDefinition.states.findIndex((state) => state.id === stateIdToEdit);
        if (stateIndex === -1) {
            throw new Error(`State not found: ${stateIdToEdit}`);
        }
        const newStates = [...workflowDefinition.states];
        newStates[stateIndex] = updatedState;
        onChange({
            ...workflowDefinition,
            states: newStates,
        });
    };

    const isStartState = workflowDefinition.startStateId === stateIdToEdit;

    return (
        <div className={classes.root}>
            {checkValid.errors.length > 0 &&
                checkValid.errors.map((error, index) => (
                    <MessageBar key={index} intent="warning" layout="multiline">
                        <MessageBarBody>
                            <Text>{error}</Text>
                        </MessageBarBody>
                    </MessageBar>
                ))}
            <Card className={classes.card}>
                <Field label={<Text weight="semibold">Label</Text>}>
                    <Input
                        value={stateToEdit.label}
                        onChange={(_event, data) => {
                            handleStateChange({
                                ...stateToEdit,
                                label: data.value,
                            });
                        }}
                        aria-autocomplete="none"
                    />
                </Field>
            </Card>
            <Card className={classes.card}>
                <div>
                    <Text weight="semibold" size={400}>
                        Conversation
                    </Text>
                    <Tooltip
                        content={
                            'Each state can have a different conversation associated with it or share a conversation' +
                            ' with other states. The conversation is the context in which the state operates.'
                        }
                        relationship="description"
                    >
                        <QuestionCircle16Regular />
                    </Tooltip>
                </div>
                <div className={classes.section}>
                    <WorkflowStateConversation
                        workflowDefinition={workflowDefinition}
                        stateIdToEdit={stateIdToEdit}
                        onChange={onChange}
                    />
                </div>
                <div className={classes.infoItem}>
                    <Checkbox
                        disabled={isStartState}
                        label="Force New Conversation Instance"
                        checked={stateToEdit.forceNewConversationInstance ?? false}
                        onChange={(_event, data) => {
                            handleStateChange({
                                ...stateToEdit,
                                forceNewConversationInstance: data.checked === true,
                            });
                        }}
                    />
                    <Tooltip
                        content={
                            'If enabled, a new conversation instance will be created when this state is activated. This' +
                            ' will create a new conversation context, and the conversation will start from the beginning.'
                        }
                        relationship="description"
                    >
                        <QuestionCircle16Regular />
                    </Tooltip>
                </div>
            </Card>
            <Card className={classes.card}>
                <div>
                    <Text weight="semibold" size={400}>
                        Assistants
                    </Text>
                    <Tooltip
                        content={
                            'Assistants are the bots that will be active in this state. You can add multiple assistants to' +
                            ' a state, and each assistant can have its own configuration. The assistant will be active' +
                            ' when the state is active'
                        }
                        relationship="description"
                    >
                        <QuestionCircle16Regular />
                    </Tooltip>
                </div>
                <div className={classes.section}>
                    <WorkflowStateAssistants
                        workflowDefinition={workflowDefinition}
                        stateIdToEdit={stateIdToEdit}
                        onChange={onChange}
                    />
                </div>
            </Card>
            <Card className={classes.card}>
                <div>
                    <Text weight="semibold" size={400}>
                        Outlets
                    </Text>
                    <Tooltip
                        content={
                            'Outlets are the possible transitions from this state to other states. Connect an outlet to' +
                            ' another state to create a transition within a workflow. If no other states are connected to' +
                            ' an outlet, the workflow will return to the initial state if the transition is triggered.'
                        }
                        relationship="description"
                    >
                        <QuestionCircle16Regular />
                    </Tooltip>
                </div>
                <div className={classes.section}>
                    <WorkflowStateOutlets
                        workflowDefinition={workflowDefinition}
                        stateIdToEdit={stateIdToEdit}
                        onChange={onChange}
                    />
                </div>
            </Card>
        </div>
    );
};
