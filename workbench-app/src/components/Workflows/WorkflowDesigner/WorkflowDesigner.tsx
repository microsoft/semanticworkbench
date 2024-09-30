// Copyright (c) Microsoft. All rights reserved.

import { Button, makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { useUpdateNodeInternals } from 'reactflow';
import { WorkflowDefinition } from '../../../models/WorkflowDefinition';
import { useUpdateWorkflowDefinitionMutation } from '../../../services/workbench/workflow';
import { ConfirmLeave } from '../../App/ConfirmLeave';
import { DefinitionPropertiesEditor } from './DefinitionPropertiesEditor';
import { StatePropertiesEditor } from './StatePropertiesEditor';
import { WorkflowCanvas } from './WorkflowCanvas';
import { WorkflowExport } from './WorkflowExport';
import { WorkflowHelp } from './WorkflowHelp';
import { WorkflowImport } from './WorkflowImport';

const useClasses = makeStyles({
    root: {
        position: 'relative',
        height: '100%',
        backgroundColor: tokens.colorNeutralBackground1,
    },
    actions: {
        position: 'absolute',
        top: tokens.spacingVerticalM,
        right: tokens.spacingHorizontalM,
        zIndex: tokens.zIndexFloating,
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'flex-end',
        gap: tokens.spacingHorizontalS,
    },
});

interface WorkflowDesignerProps {
    workflowDefinition: WorkflowDefinition;
    showSettings?: boolean;
    onShowSettingsChange?: (showSettings: boolean) => void;
}

export const WorkflowDesigner: React.FC<WorkflowDesignerProps> = (props) => {
    const { workflowDefinition, showSettings, onShowSettingsChange } = props;
    const classes = useClasses();
    const [updateWorkflowDefinition] = useUpdateWorkflowDefinitionMutation();
    const [localWorkflowDefinition, setLocalWorkflowDefinition] =
        React.useState<WorkflowDefinition>(workflowDefinition);
    const [stateIdToEdit, setStateIdToEdit] = React.useState<string>();
    const [isDirty, setIsDirty] = React.useState(false);
    const [isSaving, setIsSaving] = React.useState(false);
    const updateNodeInternals = useUpdateNodeInternals();

    const handleWorkflowDefinitionSave = async () => {
        if (isSaving) {
            return;
        }
        setIsSaving(true);

        // Clean up the workflow definition before saving
        // Remove conversation definitions that are not being used
        const usedConversationDefinitionIds = new Set<string>();
        localWorkflowDefinition.states.forEach((state) => {
            usedConversationDefinitionIds.add(state.conversationDefinitionId);
        });
        const cleanedConversationDefinitions = localWorkflowDefinition.definitions.conversations.filter(
            (conversation) => usedConversationDefinitionIds.has(conversation.id),
        );
        const cleanedWorkflowDefinition: WorkflowDefinition = {
            ...localWorkflowDefinition,
            definitions: {
                ...localWorkflowDefinition.definitions,
                conversations: cleanedConversationDefinitions,
            },
        };

        await updateWorkflowDefinition(cleanedWorkflowDefinition);
        setIsDirty(false);
        setIsSaving(false);
    };

    const handleWorkflowDefinitionChange = (updatedWorkflowDefinition: WorkflowDefinition) => {
        setIsDirty(true);
        setLocalWorkflowDefinition(updatedWorkflowDefinition);
    };

    const handleWorkflowImport = (importedWorkflowDefinition: Partial<WorkflowDefinition>) => {
        const updatedWorkflowDefinition: WorkflowDefinition = {
            ...localWorkflowDefinition,
            ...importedWorkflowDefinition,
            id: localWorkflowDefinition.id,
        };

        handleWorkflowDefinitionChange(updatedWorkflowDefinition);
    };

    return (
        <div className={classes.root}>
            <ConfirmLeave isDirty={isDirty} />
            <StatePropertiesEditor
                workflowDefinition={localWorkflowDefinition}
                stateIdToEdit={stateIdToEdit}
                onChange={(updatedWorkflowDefinition) => {
                    handleWorkflowDefinitionChange(updatedWorkflowDefinition);
                    if (!stateIdToEdit) {
                        throw new Error('State ID to edit is not set');
                    }
                    updateNodeInternals(stateIdToEdit);
                }}
                onClose={() => setStateIdToEdit(undefined)}
            />
            <div className={classes.actions}>
                <Button disabled={isSaving || !isDirty} onClick={handleWorkflowDefinitionSave} appearance="primary">
                    Save
                </Button>
                <WorkflowImport iconOnly onImport={handleWorkflowImport} />
                <WorkflowExport iconOnly workflowDefinition={localWorkflowDefinition} />
                <WorkflowHelp />
                <DefinitionPropertiesEditor
                    workflowDefinition={localWorkflowDefinition}
                    onChange={handleWorkflowDefinitionChange}
                    open={showSettings}
                    onOpenChange={onShowSettingsChange}
                />
            </div>
            <WorkflowCanvas
                workflowDefinition={localWorkflowDefinition}
                onChange={handleWorkflowDefinitionChange}
                onSelectWorkflowStateToEdit={(workflowStateId) => setStateIdToEdit(workflowStateId)}
            />
        </div>
    );
};
