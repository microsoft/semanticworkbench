// Copyright (c) Microsoft. All rights reserved.

import Form from '@rjsf/fluentui-rc';
import { RegistryWidgetsType } from '@rjsf/utils';
import validator from '@rjsf/validator-ajv8';
import React from 'react';
import { Utility } from '../../libs/Utility';
import { Assistant } from '../../models/Assistant';
import { useGetConfigQuery, useUpdateConfigMutation } from '../../services/workbench';
import { ConfirmLeave } from '../App/ConfirmLeave';
import { CustomizedArrayFieldTemplate } from '../App/FormWidgets/CustomizedArrayFieldTemplate';
import { CustomizedObjectFieldTemplate } from '../App/FormWidgets/CustomizedObjectFieldTemplate';
import { InspectableWidget } from '../App/FormWidgets/InspectableWidget';
import { Loading } from '../App/Loading';

interface AssistantInstanceEditProps {
    assistant: Assistant;
}

export const AssistantEdit: React.FC<AssistantInstanceEditProps> = (props) => {
    const { assistant } = props;
    const {
        data: config,
        error: configError,
        isLoading: isLoadingConfig,
    } = useGetConfigQuery({ assistantId: assistant.id });
    const [updateConfig] = useUpdateConfigMutation();
    const [formData, setFormData] = React.useState<object>();
    const [isDirty, setDirty] = React.useState(false);

    if (configError) {
        const errorMessage = JSON.stringify(configError);
        throw new Error(`Error loading assistant config: ${errorMessage}`);
    }

    React.useEffect(() => {
        if (isLoadingConfig) return;
        setFormData(config?.config);
    }, [isLoadingConfig, config]);

    const handleChange = async (updatedConfig: object) => {
        if (!config) return;
        setFormData(updatedConfig);
        await updateConfig({ assistantId: assistant.id, config: { ...config, config: updatedConfig } });
        setDirty(false);
    };

    React.useEffect(() => {
        if (config?.config && formData) {
            const diff = Utility.deepDiff(config.config, formData);
            setDirty(Object.keys(diff).length > 0);
        }
    }, [config, formData]);

    if (isLoadingConfig || !config) {
        return <Loading />;
    }

    const widgets: RegistryWidgetsType = {
        inspectable: InspectableWidget,
    };

    const templates = {
        ArrayFieldTemplate: CustomizedArrayFieldTemplate,
        ObjectFieldTemplate: CustomizedObjectFieldTemplate,
    };

    return (
        <>
            <ConfirmLeave isDirty={isDirty} />
            <Form
                aria-autocomplete="none"
                autoComplete="off"
                widgets={widgets}
                templates={templates}
                schema={config.jsonSchema ?? {}}
                uiSchema={{
                    ...config.uiSchema,
                    'ui:title': 'Update the assistant configuration',
                    'ui:submitButtonOptions': {
                        submitText: 'Save',
                        props: {
                            disabled: isDirty === false,
                        },
                    },
                }}
                validator={validator}
                formData={formData}
                onChange={(data) => {
                    setFormData(data.formData);
                }}
                onSubmit={(data, event) => {
                    event.preventDefault();
                    handleChange(data.formData);
                }}
            />
        </>
    );
};
