// Copyright (c) Microsoft. All rights reserved.

import {
    Card,
    Field,
    Input,
    MessageBar,
    MessageBarBody,
    Text,
    Textarea,
    makeStyles,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { WorkflowDefinition } from '../../../models/WorkflowDefinition';
import { LabelWithDescription } from '../../App/LabelWithDescription';

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
});

export const isValidWorkflowDefinitionData = (
    value: WorkflowDefinition,
): {
    isValid: boolean;
    errors: string[];
} => {
    const errors: string[] = [];
    if (!value.label) {
        errors.push('Label is required');
    }
    if (!value.instructions.contextTransfer) {
        errors.push('Context transfer instruction is required');
    }
    return {
        isValid: errors.length === 0,
        errors,
    };
};

interface WorkflowDefinitionEditorProps {
    workflowDefinition: WorkflowDefinition;
    onChange: (newValue: WorkflowDefinition) => void;
}

export const WorkflowDefinitionEditor: React.FC<WorkflowDefinitionEditorProps> = (props) => {
    const { workflowDefinition, onChange } = props;
    const classes = useClasses();

    const checkValid = isValidWorkflowDefinitionData(workflowDefinition);

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
                        value={workflowDefinition.label}
                        onChange={(_event, data) => {
                            onChange({
                                ...workflowDefinition,
                                label: data.value,
                            });
                        }}
                        aria-autocomplete="none"
                    />
                </Field>
                <Field
                    label={
                        <LabelWithDescription
                            label="Context Transfer Instruction"
                            description={[
                                'Instruction for how the workflow should generate context transfer notes to bring',
                                ' context from a source state to target state. This instruction will be combined',
                                ' with the source conversation chat history and the transition context transfer',
                                ' request to create a natural language request for creating a context transfer',
                                ' note.The result will be added to the target conversation chat history.',
                            ].join(' ')}
                        />
                    }
                >
                    <Textarea
                        value={workflowDefinition.instructions.contextTransfer}
                        onChange={(_event, data) => {
                            onChange({
                                ...workflowDefinition,
                                instructions: {
                                    ...workflowDefinition.instructions,
                                    contextTransfer: data.value,
                                },
                            });
                        }}
                        aria-autocomplete="none"
                        rows={3}
                    />
                </Field>
            </Card>
        </div>
    );
};
