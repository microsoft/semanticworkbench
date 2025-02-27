import { Dropdown, Field, Option, Text, tokens } from '@fluentui/react-components';
import {
    FieldTemplateProps,
    FormContextType,
    getTemplate,
    getUiOptions,
    RJSFSchema,
    StrictRJSFSchema,
} from '@rjsf/utils';
import React from 'react';

/** The `FieldTemplate` component is the template used by `SchemaField` to render any field. It renders the field
 * content, (label, description, children, errors and help) inside of a `WrapIfAdditional` component.
 *
 * @param props - The `FieldTemplateProps` for this component
 */
export default function CustomizedFieldTemplate<
    T = any,
    S extends StrictRJSFSchema = RJSFSchema,
    F extends FormContextType = any,
>(props: FieldTemplateProps<T, S, F>) {
    const {
        id,
        children,
        classNames,
        style,
        disabled,
        displayLabel,
        formData,
        hidden,
        label,
        onChange,
        onDropPropertyClick,
        onKeyChange,
        readonly,
        required,
        rawErrors = [],
        errors,
        help,
        description,
        rawDescription,
        schema,
        uiSchema,
        registry,
    } = props;
    const uiOptions = getUiOptions<T, S, F>(uiSchema);
    const WrapIfAdditionalTemplate = getTemplate<'WrapIfAdditionalTemplate', T, S, F>(
        'WrapIfAdditionalTemplate',
        registry,
        uiOptions,
    );

    // If uiSchema includes ui:options for this field, check if it has configurations
    // These are used to provide a dropdown to select a configuration for the field
    // that will update the formData value and allow users to switch between configurations
    // If the user modifies the field value, the configuration dropdown will be reset
    const configurationsComponent = React.useMemo(() => {
        if (uiOptions && uiOptions['configurations'] && typeof uiOptions['configurations'] === 'object') {
            // handle as record
            const configurations = uiOptions['configurations'] as Record<string, any>;

            // Handle selection change for dropdown
            const handleSelectionChange = (_: React.SyntheticEvent<HTMLElement>, option: any) => {
                const selectedConfig = configurations[option.optionValue];
                onChange(selectedConfig);
            };

            const selectedKey =
                Object.keys(configurations).find(
                    (key) => JSON.stringify(configurations[key]) === JSON.stringify(formData),
                ) || '';

            const selectedOptions = selectedKey ? [selectedKey] : [];

            return (
                <Field label={`${label}: Select Configuration`} style={{ padding: `${tokens.spacingVerticalM} 0` }}>
                    <div>
                        <Dropdown
                            value={selectedKey}
                            selectedOptions={selectedOptions}
                            onOptionSelect={handleSelectionChange}
                            placeholder="Choose a configuration"
                        >
                            {Object.entries(configurations).map(([key]) => (
                                <Option key={key} value={key}>
                                    {key}
                                </Option>
                            ))}
                        </Dropdown>
                    </div>
                </Field>
            );
        }
        return null;
    }, [formData, label, onChange, uiOptions]);

    if (hidden) {
        return <div style={{ display: 'none' }}>{children}</div>;
    }
    return (
        <WrapIfAdditionalTemplate
            classNames={classNames}
            style={style}
            disabled={disabled}
            id={id}
            label={label}
            onDropPropertyClick={onDropPropertyClick}
            onKeyChange={onKeyChange}
            readonly={readonly}
            required={required}
            schema={schema}
            uiSchema={uiSchema}
            registry={registry}
        >
            <Field validationState={rawErrors.length ? 'error' : undefined} required={required}>
                {configurationsComponent}
                {children}
                {displayLabel && rawDescription ? (
                    <Text block style={{ display: 'block', marginTop: tokens.spacingVerticalS }}>
                        {description}
                    </Text>
                ) : null}
                {errors}
                {help}
            </Field>
        </WrapIfAdditionalTemplate>
    );
}
