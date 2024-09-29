// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, tokens } from '@fluentui/react-components';
import { Form } from '@rjsf/fluentui-rc';
import { RegistryWidgetsType } from '@rjsf/utils';
import validator from '@rjsf/validator-ajv8';
import React from 'react';
import { Utility } from '../../../libs/Utility';
import { useWorkbenchService } from '../../../libs/useWorkbenchService';
import { Config } from '../../../models/Config';
import { WorkflowDefinition } from '../../../models/WorkflowDefinition';
import { CustomizedArrayFieldTemplate } from '../../App/FormWidgets/CustomizedArrayFieldTemplate';
import { CustomizedObjectFieldTemplate } from '../../App/FormWidgets/CustomizedObjectFieldTemplate';
import { InspectableWidget } from '../../App/FormWidgets/InspectableWidget';
import { Loading } from '../../App/Loading';
import { AssistantServiceMetadata } from '../../Assistants/AssistantServiceMetadata';

const useClasses = makeStyles({
    form: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
});

interface WorkflowStateAssistantEditorProps {
    workflowDefinition: WorkflowDefinition;
    stateIdToEdit: string;
    assistantIdToEdit: string;
    onChange: (newValue: WorkflowDefinition) => void;
}

export const WorkflowStateAssistantEditor: React.FC<WorkflowStateAssistantEditorProps> = (props) => {
    const { workflowDefinition, stateIdToEdit, assistantIdToEdit, onChange } = props;
    const classes = useClasses();
    const [assistantDefaultConfig, setAssistantDefaultConfig] = React.useState<Config>();
    const workbenchService = useWorkbenchService();

    const stateToEdit = workflowDefinition.states.find((state) => state.id === stateIdToEdit);
    if (!stateToEdit) {
        throw new Error(`State not found: ${stateIdToEdit}`);
    }

    const assistantToEdit = stateToEdit.assistantDataList.find(
        (assistant) => assistant.assistantDefinitionId === assistantIdToEdit,
    );
    if (!assistantToEdit) {
        throw new Error(`Assistant not found: ${assistantIdToEdit}`);
    }

    const assistantDefinition = workflowDefinition.definitions.assistants.find(
        (assistantDefinition) => assistantDefinition.id === assistantToEdit.assistantDefinitionId,
    );
    if (!assistantDefinition) {
        throw new Error(`Assistant definition not found: ${assistantToEdit.assistantDefinitionId}`);
    }

    React.useEffect(() => {
        (async () => {
            const assistantDefinition = workflowDefinition.definitions.assistants.find(
                (assistantDefinition) => assistantDefinition.id === assistantToEdit.assistantDefinitionId,
            );
            if (!assistantDefinition) {
                throw new Error(`Assistant definition not found: ${assistantToEdit.assistantDefinitionId}`);
            }
            const assistantServiceInfo = await workbenchService.getAssistantServiceInfoAsync(
                assistantDefinition.assistantServiceId,
            );
            if (!assistantServiceInfo) {
                throw new Error(`Assistant service not found for assistant ${assistantToEdit.assistantDefinitionId}`);
            }
            setAssistantDefaultConfig(assistantServiceInfo.defaultConfig);
        })();
    }, [assistantToEdit.assistantDefinitionId, workbenchService, workflowDefinition.definitions.assistants]);

    const widgets: RegistryWidgetsType = {
        inspectable: InspectableWidget,
    };

    const templates = {
        ArrayFieldTemplate: CustomizedArrayFieldTemplate,
        ObjectFieldTemplate: CustomizedObjectFieldTemplate,
    };

    const handleConfigChange = (data: object) => {
        const differences = Utility.deepDiff(assistantToEdit.configData, data);
        if (Object.keys(differences).length === 0) {
            return;
        }

        onChange({
            ...workflowDefinition,
            states: workflowDefinition.states.map((state) => {
                if (state.id === stateIdToEdit) {
                    return {
                        ...state,
                        assistantDataList: state.assistantDataList.map((assistantData) => {
                            if (assistantData.assistantDefinitionId === assistantIdToEdit) {
                                return {
                                    ...assistantData,
                                    configData: data,
                                };
                            }
                            return assistantData;
                        }),
                    };
                }
                return state;
            }),
        });
    };

    if (!assistantDefaultConfig) {
        return <Loading />;
    }

    return (
        <>
            <AssistantServiceMetadata assistantServiceId={assistantDefinition.assistantServiceId} />
            <Form
                aria-autocomplete="none"
                autoComplete="off"
                className={classes.form}
                widgets={widgets}
                templates={templates}
                schema={assistantDefaultConfig.jsonSchema ?? {}}
                uiSchema={{
                    ...assistantDefaultConfig.uiSchema,
                    'ui:submitButtonOptions': {
                        norender: true,
                    },
                }}
                validator={validator}
                formData={assistantToEdit.configData}
                onChange={(data) => handleConfigChange(data.formData)}
            />
        </>
    );
};
