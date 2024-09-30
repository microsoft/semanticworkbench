// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Divider,
    Menu,
    MenuItem,
    MenuList,
    MenuPopover,
    MenuTrigger,
    makeStyles,
} from '@fluentui/react-components';
import { Bot24Regular, BotAddRegular, Sparkle24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useWorkbenchService } from '../../../libs/useWorkbenchService';
import { AssistantDefinition, WorkflowDefinition } from '../../../models/WorkflowDefinition';
import { AssistantDefinitionCreate } from './AssistantDefinitionCreate';

const useClasses = makeStyles({
    menuList: {
        maxHeight: 'calc(100vh - 200px)',
    },
});

interface AssistantAddProps {
    workflowDefinition: WorkflowDefinition;
    stateIdToEdit: string;
    onChange: (newValue: WorkflowDefinition) => void;
}

export const AssistantDefinitionAdd: React.FC<AssistantAddProps> = (props) => {
    const { workflowDefinition, stateIdToEdit, onChange } = props;
    const classes = useClasses();
    const workbenchService = useWorkbenchService();
    const [assistantCreateOpen, setAssistantCreateOpen] = React.useState(false);

    const stateToEdit = workflowDefinition.states.find((state) => state.id === stateIdToEdit);
    if (!stateToEdit) {
        throw new Error(`State not found: ${stateIdToEdit}`);
    }

    const handleNewAssistant = () => {
        setAssistantCreateOpen(true);
    };

    const handleCreateAssistantDefinition = async (assistantDefinition: AssistantDefinition) => {
        const assistantServiceInfo = await workbenchService.getAssistantServiceInfoAsync(
            assistantDefinition.assistantServiceId,
        );
        if (!assistantServiceInfo) {
            throw new Error(`Assistant service not found for assistant ${assistantDefinition.id}`);
        }

        onChange({
            ...workflowDefinition,
            definitions: {
                ...workflowDefinition.definitions,
                assistants: [...workflowDefinition.definitions.assistants, assistantDefinition],
            },
            states: workflowDefinition.states.map((state) => {
                if (state.id === stateIdToEdit) {
                    return {
                        ...state,
                        assistantDataList: [
                            ...(state.assistantDataList || []),
                            {
                                assistantDefinitionId: assistantDefinition.id,
                                configData: assistantServiceInfo.defaultConfig.config,
                            },
                        ],
                    };
                }
                return state;
            }),
        });
    };

    const handleAddAssistant = async (assistantDefinitionId: string) => {
        const assistantDefinition = workflowDefinition.definitions.assistants.find(
            (possibleAssistantDefinition) => possibleAssistantDefinition.id === assistantDefinitionId,
        );
        if (!assistantDefinition) {
            throw new Error(`Assistant definition not found: ${assistantDefinitionId}`);
        }

        const assistantServiceInfo = await workbenchService.getAssistantServiceInfoAsync(
            assistantDefinition.assistantServiceId,
        );
        if (!assistantServiceInfo) {
            throw new Error(`Assistant service not found for assistant ${assistantDefinitionId}`);
        }

        onChange({
            ...workflowDefinition,
            states: workflowDefinition.states.map((state) => {
                if (state.id === stateIdToEdit) {
                    return {
                        ...state,
                        assistantDataList: [
                            ...(state.assistantDataList || []),
                            {
                                assistantDefinitionId,
                                configData: assistantServiceInfo.defaultConfig.config,
                            },
                        ],
                    };
                }
                return state;
            }),
        });
    };

    const unusedAssistantDefinitions = workflowDefinition.definitions.assistants.filter(
        (assistantDefinition) =>
            !stateToEdit.assistantDataList?.some(
                (assistantData) => assistantData.assistantDefinitionId === assistantDefinition.id,
            ),
    );

    return (
        <div>
            <AssistantDefinitionCreate
                open={assistantCreateOpen}
                onOpenChange={(open) => setAssistantCreateOpen(open)}
                onCreate={handleCreateAssistantDefinition}
            />
            <Menu>
                <MenuTrigger disableButtonEnhancement>
                    <Button icon={<BotAddRegular />}>Add assistant</Button>
                </MenuTrigger>
                <MenuPopover className={classes.menuList}>
                    <MenuList>
                        {unusedAssistantDefinitions.length === 0 && <MenuItem>No assistants available</MenuItem>}
                        {unusedAssistantDefinitions
                            .sort((a, b) => a.name.toLocaleLowerCase().localeCompare(b.name.toLocaleLowerCase()))
                            .map((assistantDefinition) => (
                                <MenuItem
                                    key={assistantDefinition.id}
                                    icon={<Bot24Regular />}
                                    onClick={() => handleAddAssistant(assistantDefinition.id)}
                                >
                                    {assistantDefinition.name}
                                </MenuItem>
                            ))}
                    </MenuList>
                    <Divider />
                    <MenuItem icon={<Sparkle24Regular />} onClick={handleNewAssistant}>
                        Create new assistant
                    </MenuItem>
                </MenuPopover>
            </Menu>
        </div>
    );
};
