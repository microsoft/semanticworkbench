// Copyright (c) Microsoft. All rights reserved.

import { Button, Dropdown, Option, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import { ArrowResetRegular } from '@fluentui/react-icons';
import debug from 'debug';
import React from 'react';
import { Constants } from '../../Constants';
import { WorkflowState } from '../../models/WorkflowDefinition';
import { WorkflowRun } from '../../models/WorkflowRun';
import { useGetWorkflowDefinitionQuery, useSwitchWorkflowRunStateMutation } from '../../services/workbench';

const log = debug(Constants.debug.root).extend('workflow-control');

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        ...shorthands.padding(0, tokens.spacingHorizontalM),
        gap: tokens.spacingHorizontalS,
    },
    link: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: tokens.spacingHorizontalS,
    },
    label: {
        fontWeight: tokens.fontWeightSemibold,
    },
});

interface WorkflowControlProps {
    workflowRun: WorkflowRun;
    readOnly?: boolean;
}

export const WorkflowControl: React.FC<WorkflowControlProps> = (props) => {
    const { workflowRun, readOnly } = props;
    const classes = useClasses();

    const {
        data: workflowDefinition,
        error: workflowDefinitionError,
        isLoading: workflowDefinitionIsLoading,
    } = useGetWorkflowDefinitionQuery(workflowRun.workflowDefinitionId);
    const [switchWorkflowRunState] = useSwitchWorkflowRunStateMutation();
    const [isSwitchingState, setIsSwitchingState] = React.useState(false);

    if (workflowDefinitionError) {
        const errorMessage = JSON.stringify(workflowDefinitionError);
        throw new Error(`Error loading workflow definition: ${errorMessage}`);
    }

    if (workflowDefinitionIsLoading) {
        return null;
    }

    if (!workflowDefinition) {
        throw new Error('Workflow definition not found');
    }

    const sortedStates = [];
    const startState = workflowDefinition.states.find((state) => state.id === workflowDefinition.startStateId);
    if (startState) {
        sortedStates.push(startState);
    }
    for (const state of workflowDefinition.states || []) {
        if (state.id !== startState?.id) {
            sortedStates.push(state);
        }
    }

    const getLabelForDisplay = (state: WorkflowState) => {
        return state.label + (state.id === workflowDefinition.startStateId ? ' (Default)' : '');
    };

    const stateOptions = sortedStates.map((state) => ({
        key: state.id,
        text: getLabelForDisplay(state),
    }));

    const currentState = workflowDefinition.states.find((state) => state.id === workflowRun.currentStateId);
    if (!currentState) {
        throw new Error('Current state not found');
    }

    const currentConversationLabel = workflowDefinition.definitions.conversations.find(
        (conversation) => conversation.id === currentState.conversationDefinitionId,
    )?.title;

    const handleSwitchToState = (stateId: string) => {
        (async () => {
            setIsSwitchingState(true);
            log(`Switching to state ${stateId}`);
            await switchWorkflowRunState({
                workflowRunId: workflowRun.id,
                stateId,
            });
            setIsSwitchingState(false);
        })();
    };

    // show the current status
    return (
        <div className={classes.root}>
            Workflow State:
            {readOnly ? (
                <span className={classes.label}>{getLabelForDisplay(currentState)}</span>
            ) : (
                <>
                    <Dropdown
                        disabled={isSwitchingState}
                        placeholder="Choose a state"
                        size="small"
                        value={getLabelForDisplay(currentState) ?? ''}
                        onOptionSelect={(_event, data) => {
                            if (data.optionValue !== currentState.id && data.optionValue) {
                                handleSwitchToState(data.optionValue);
                            }
                        }}
                    >
                        {stateOptions?.map((option) => (
                            <Option key={option.key} value={option.key}>
                                {option.text}
                            </Option>
                        ))}
                    </Dropdown>
                    <Button
                        disabled={currentState.id === workflowDefinition.startStateId}
                        size="small"
                        icon={<ArrowResetRegular />}
                        onClick={() => handleSwitchToState(workflowDefinition.startStateId)}
                    >
                        Reset
                    </Button>
                </>
            )}
            {workflowRun.conversationMappings.length > 1 && (
                <>
                    / Current Conversation: <span className={classes.label}>{currentConversationLabel}</span>
                </>
            )}
        </div>
    );
};
