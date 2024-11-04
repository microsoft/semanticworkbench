// Copyright (c) Microsoft. All rights reserved.

import { Button, Card, Divider, makeStyles, shorthands, Text, tokens } from '@fluentui/react-components';
import { Warning24Filled } from '@fluentui/react-icons';
import Form from '@rjsf/fluentui-rc';
import { RegistryWidgetsType, RJSFSchema } from '@rjsf/utils';
import validator from '@rjsf/validator-ajv8';
import debug from 'debug';
import React from 'react';
import { Constants } from '../../Constants';
import { Utility } from '../../libs/Utility';
import { Assistant } from '../../models/Assistant';
import { useGetConfigQuery, useUpdateConfigMutation } from '../../services/workbench';
import { ConfirmLeave } from '../App/ConfirmLeave';
import { ErrorMessageBar } from '../App/ErrorMessageBar';
import { BaseModelEditorWidget } from '../App/FormWidgets/BaseModelEditorWidget';
import { CustomizedArrayFieldTemplate } from '../App/FormWidgets/CustomizedArrayFieldTemplate';
import CustomizedFieldTemplate from '../App/FormWidgets/CustomizedFieldTemplate';
import { CustomizedObjectFieldTemplate } from '../App/FormWidgets/CustomizedObjectFieldTemplate';
import { InspectableWidget } from '../App/FormWidgets/InspectableWidget';
import { Loading } from '../App/Loading';
import { ApplyConfigButton } from './ApplyConfigButton';
import { AssistantConfigExportButton } from './AssistantConfigExportButton';
import { AssistantConfigImportButton } from './AssistantConfigImportButton';

const log = debug(Constants.debug.root).extend('AssistantEdit');

const useClasses = makeStyles({
    card: {
        backgroundImage: `linear-gradient(to right, ${tokens.colorNeutralBackground1}, ${tokens.colorBrandBackground2})`,
    },
    actions: {
        position: 'sticky',
        top: 0,
        display: 'flex',
        flexDirection: 'row',
        gap: '8px',
        zIndex: tokens.zIndexContent,
        backgroundColor: 'white',
        padding: '8px',
        ...shorthands.border(tokens.strokeWidthThin, 'solid', tokens.colorNeutralStroke1),
    },
    warning: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        fontWeight: tokens.fontWeightSemibold,
        color: tokens.colorPaletteRedForeground1,
    },
});

interface AssistantConfigurationProps {
    assistant: Assistant;
}

export const AssistantConfiguration: React.FC<AssistantConfigurationProps> = (props) => {
    const { assistant } = props;
    const classes = useClasses();
    const {
        data: config,
        error: configError,
        isLoading: isLoadingConfig,
    } = useGetConfigQuery({ assistantId: assistant.id });
    const [updateConfig] = useUpdateConfigMutation();
    const [formData, setFormData] = React.useState<object>();
    const [isDirty, setDirty] = React.useState(false);
    const [isValid, setValid] = React.useState(true);
    const [configErrorMessage, setConfigErrorMessage] = React.useState<string>();

    React.useEffect(() => {
        setConfigErrorMessage(configError ? JSON.stringify(configError) : undefined);
    }, [configError]);

    React.useEffect(() => {
        if (isLoadingConfig) return;
        setFormData(config?.config);
    }, [isLoadingConfig, config]);

    const handleSubmit = async (updatedConfig: object) => {
        if (!config) return;
        await updateConfig({ assistantId: assistant.id, config: { ...config, config: updatedConfig } });
        setDirty(false);
    };

    const defaults = React.useMemo(() => {
        if (config?.jsonSchema) {
            return extractDefaultsFromSchema(config.jsonSchema);
        }
        return {};
    }, [config]);

    React.useEffect(() => {
        if (config?.config && formData) {
            // Compare the current form data with the original config to determine if the form is dirty
            const diff = Utility.deepDiff(config.config, formData);
            setDirty(Object.keys(diff).length > 0);
        }

        if (config?.jsonSchema && formData) {
            // Validate the form data against the JSON schema
            const { errors } = validator.validateFormData(
                formData,
                config.jsonSchema,
                undefined,
                undefined,
                config.uiSchema,
            );
            setValid(errors.length === 0);
        }
    }, [config, formData]);

    const restoreConfig = (config: object) => {
        log('Restoring config', config);
        setFormData(config);
    };

    const mergeConfigurations = (uploadedConfig: object) => {
        if (!config) return;

        const updatedConfig = Utility.deepMerge(config.config, uploadedConfig);
        setFormData(updatedConfig);
    };

    const widgets: RegistryWidgetsType = {
        inspectable: InspectableWidget,
        baseModelEditor: BaseModelEditorWidget,
    };

    const templates = {
        ArrayFieldTemplate: CustomizedArrayFieldTemplate,
        FieldTemplate: CustomizedFieldTemplate,
        ObjectFieldTemplate: CustomizedObjectFieldTemplate,
    };

    if (isLoadingConfig) {
        return <Loading />;
    }

    return (
        <Card className={classes.card}>
            <Text size={400} weight="semibold">
                Assistant Configuration
            </Text>
            {!config ? (
                <ErrorMessageBar title="Error loading assistant config" error={configErrorMessage} />
            ) : (
                <>
                    <Text size={300} italic color="neutralSecondary">
                        Please practice Responsible AI when configuring your assistant. See the{' '}
                        <a
                            href="https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/system-message"
                            target="_blank"
                            rel="noreferrer"
                        >
                            Microsoft Azure OpenAI Service: System message templates
                        </a>{' '}
                        page for suggestions regarding content for the prompts below.
                    </Text>
                    <Divider />
                    <ConfirmLeave isDirty={isDirty} />
                    <div className={classes.actions}>
                        <Button appearance="primary" form="assistant-config-form" type="submit" disabled={!isDirty}>
                            Save
                        </Button>
                        <ApplyConfigButton
                            label="Reset"
                            confirmMessage="Are you sure you want to reset the changes to configuration?"
                            currentConfig={formData}
                            newConfig={config.config}
                            onApply={restoreConfig}
                        />
                        <ApplyConfigButton
                            label="Load defaults"
                            confirmMessage="Are you sure you want to load the default configuration?"
                            currentConfig={formData}
                            newConfig={defaults}
                            onApply={restoreConfig}
                        />
                        <AssistantConfigExportButton config={config?.config || {}} assistantId={assistant.id} />
                        <AssistantConfigImportButton onImport={mergeConfigurations} />
                        {!isValid && (
                            <div className={classes.warning}>
                                <Warning24Filled /> Configuration has missing or invalid values
                            </div>
                        )}
                    </div>
                    <Form
                        id="assistant-config-form"
                        aria-autocomplete="none"
                        autoComplete="off"
                        widgets={widgets}
                        templates={templates}
                        schema={config.jsonSchema ?? {}}
                        uiSchema={{
                            'ui:title': 'Update the assistant configuration',
                            ...config.uiSchema,
                            'ui:submitButtonOptions': {
                                norender: true,
                                submitText: 'Save',
                                props: {
                                    disabled: isDirty === false,
                                },
                            },
                        }}
                        validator={validator}
                        liveValidate={true}
                        showErrorList={false}
                        formData={formData}
                        onChange={(data) => {
                            setFormData(data.formData);
                        }}
                        onSubmit={(data, event) => {
                            event.preventDefault();
                            handleSubmit(data.formData);
                        }}
                    />
                </>
            )}
        </Card>
    );
};

/*
 * Helpers
 */

function extractDefaultsFromSchema(schema: RJSFSchema): any {
    const defaults: any = {};

    function traverse(schema: any, path: string[] = [], rootSchema: any = schema) {
        if (schema.default !== undefined) {
            setDefault(defaults, path, schema.default);
        }

        if (schema.properties) {
            for (const key in schema.properties) {
                traverse(schema.properties[key], [...path, key], rootSchema);
            }
        }

        if (schema.$ref) {
            const refPath = schema.$ref.replace(/^#\/\$defs\//, '').split('/');
            const refSchema = refPath.reduce((acc: any, key: string) => acc?.[key], rootSchema.$defs);
            if (refSchema) {
                traverse(refSchema, path, rootSchema);
            } else {
                console.error(`Reference not found: ${schema.$ref}`);
            }
        }
    }

    function setDefault(obj: any, path: string[], value: any) {
        let current = obj;
        for (let i = 0; i < path.length - 1; i++) {
            if (!current[path[i]]) {
                current[path[i]] = {};
            } else {
                // Create a new object to avoid modifying read-only properties
                current[path[i]] = { ...current[path[i]] };
            }
            current = current[path[i]];
        }
        current[path[path.length - 1]] = value;
    }

    traverse(schema);
    return defaults;
}
