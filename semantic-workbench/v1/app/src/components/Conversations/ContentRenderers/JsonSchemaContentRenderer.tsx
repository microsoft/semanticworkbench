// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, shorthands, tokens } from '@fluentui/react-components';
import {} from '@rjsf/core';
import Form from '@rjsf/fluentui-rc';
import { RegistryWidgetsType } from '@rjsf/utils';
import validator from '@rjsf/validator-ajv8';
import React from 'react';
import { CustomizedArrayFieldTemplate } from '../../App/FormWidgets/CustomizedArrayFieldTemplate';
import { CustomizedObjectFieldTemplate } from '../../App/FormWidgets/CustomizedObjectFieldTemplate';
import { InspectableWidget } from '../../App/FormWidgets/InspectableWidget';
import { DebugInspector } from '../DebugInspector';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        ...shorthands.padding(tokens.spacingVerticalM),
        gap: tokens.spacingVerticalL,
    },
    form: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
});

interface InspectorProps {
    content: string;
    metadata: Record<string, unknown>;
    onSubmit?: (data: string) => Promise<void>;
}

export const JsonSchemaContentRenderer: React.FC<InspectorProps> = (props) => {
    const { content, metadata, onSubmit } = props;
    const classes = useClasses();

    const currentData = JSON.parse(content);
    const jsonSchema: object = metadata.json_schema || {};
    const uiSchema: object = metadata.ui_schema || {};

    const [formData, setFormData] = React.useState<object>(currentData);
    const [isSubmitting, setIsSubmitting] = React.useState(false);

    const handleSubmit = async (updatedData: object) => {
        if (isSubmitting) return;
        setIsSubmitting(true);
        setFormData(updatedData);
        await onSubmit?.(JSON.stringify(updatedData));
        setIsSubmitting(false);
    };

    const widgets: RegistryWidgetsType = {
        inspectable: InspectableWidget,
    };

    const templates = {
        ArrayFieldTemplate: CustomizedArrayFieldTemplate,
        ObjectFieldTemplate: CustomizedObjectFieldTemplate,
    };

    // metadata minus the debug key, as that is handled separately
    const debug: Record<string, unknown> = { ...metadata };
    delete debug.debug;

    return (
        <>
            <DebugInspector debug={debug} />
            <Form
                aria-autocomplete="none"
                autoComplete="off"
                className={classes.form}
                widgets={widgets}
                templates={templates}
                schema={jsonSchema}
                uiSchema={uiSchema}
                formData={formData}
                validator={validator}
                onChange={(data) => {
                    setFormData(data.formData);
                }}
                onSubmit={(data, event) => {
                    event.preventDefault();
                    handleSubmit(data.formData);
                }}
            />
        </>
    );
};
