import {
    Button,
    Dropdown,
    Field,
    Input,
    makeStyles,
    Option,
    shorthands,
    Text,
    Textarea,
    tokens,
} from '@fluentui/react-components';
import { Add16Regular, Delete16Regular } from '@fluentui/react-icons';
import { WidgetProps } from '@rjsf/utils';
import React from 'react';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalXXS,
    },
    properties: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalL,
        ...shorthands.margin(tokens.spacingVerticalS, 0),
    },
    property: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalL,
        padding: tokens.spacingHorizontalM,
        border: '1px solid #ccc',
        borderRadius: tokens.borderRadiusMedium,
    },
    nestedProperties: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalL,
        ...shorthands.margin(tokens.spacingVerticalS, 0, tokens.spacingVerticalS, tokens.spacingHorizontalM),
    },
});

interface ModelSchema {
    properties?: {
        [key: string]: {
            title?: string;
            type?: string;
            description?: string;
            enum?: string[]; // For handling dropdowns
            properties?: ModelSchema['properties']; // For nested objects
            items?: { type: string }; // For handling arrays (lists)
        };
    };
}

export const BaseModelEditorWidget: React.FC<WidgetProps> = (props) => {
    const { label, schema, value, onChange } = props;
    const classes = useClasses();

    // Define the schema type
    const [modelSchema, setModelSchema] = React.useState<ModelSchema>(() => {
        return typeof value === 'string' ? JSON.parse(value) : value || {};
    });

    // Update the modelSchema when the value changes
    React.useEffect(() => {
        setModelSchema(typeof value === 'string' ? JSON.parse(value) : value || {});
    }, [value]);

    // Helper function to update the modelSchema
    const handleSchemaChange = (
        keyPath: string,
        propertyKey: keyof NonNullable<ModelSchema['properties']>[string],
        newValue: any,
    ) => {
        const keys = keyPath.split('.');
        const updatedModelSchema = { ...modelSchema };
        let current = updatedModelSchema.properties;

        for (let i = 0; i < keys.length - 1; i++) {
            if (!current || !current[keys[i]]) return;
            current = current[keys[i]].properties;
        }

        if (current && current[keys[keys.length - 1]]) {
            current[keys[keys.length - 1]] = {
                ...current[keys[keys.length - 1]],
                [propertyKey]: newValue,
            };
        }

        setModelSchema(updatedModelSchema);
        onChange(JSON.stringify(updatedModelSchema));
    };

    // Helper function to add a new property
    const handleAddProperty = () => {
        const newKey = `new_property_${Object.keys(modelSchema.properties || {}).length + 1}`;
        const updatedProperties = {
            ...modelSchema.properties,
            [newKey]: {
                title: 'New Property',
                type: 'string',
                description: '',
            },
        };
        const updatedModelSchema = {
            ...modelSchema,
            properties: updatedProperties,
        };
        setModelSchema(updatedModelSchema);
        onChange(JSON.stringify(updatedModelSchema));
    };

    // Helper function to remove a property
    const handleRemoveProperty = (key: string) => {
        const { [key]: _, ...remainingProperties } = modelSchema.properties || {};
        const updatedModelSchema = {
            ...modelSchema,
            properties: remainingProperties,
        };
        setModelSchema(updatedModelSchema);
        onChange(JSON.stringify(updatedModelSchema));
    };

    // Helper function to add a new nested property
    const handleAddNestedProperty = (parentKey: string) => {
        const keys = parentKey.split('.');
        const updatedModelSchema = { ...modelSchema };
        let current = updatedModelSchema.properties;

        for (let i = 0; i < keys.length; i++) {
            if (!current || !current[keys[i]]) return;
            current = current[keys[i]].properties;
        }

        const newKey = `new_nested_property_${Object.keys(current || {}).length + 1}`;
        const updatedNestedProperties = {
            ...current,
            [newKey]: {
                title: 'New Nested Property',
                type: 'string',
                description: '',
            },
        };

        if (current) {
            Object.assign(current, updatedNestedProperties);
        }

        setModelSchema(updatedModelSchema);
        onChange(JSON.stringify(updatedModelSchema));
    };

    // Helper function to render nested properties
    const renderNestedProperties = (properties: ModelSchema['properties'], parentKey: string) => {
        return (
            <div className={classes.nestedProperties}>
                {Object.entries(properties || {}).map(([key, property]) => (
                    <div key={key}>{renderSchemaFieldEditor(`${parentKey}.${key}`, property)}</div>
                ))}
                <div>
                    <Button
                        onClick={() => handleAddNestedProperty(parentKey)}
                        appearance="outline"
                        size="small"
                        icon={<Add16Regular />}
                    >
                        Add Nested Property
                    </Button>
                </div>
            </div>
        );
    };

    // Helper function to render the schema field editor
    const renderSchemaFieldEditor = (
        key: string,
        property: {
            title?: string;
            type?: string;
            description?: string;
            enum?: string[];
            properties?: ModelSchema['properties'];
            items?: { type: string };
        },
    ) => {
        return (
            <div className={classes.property}>
                <Field label="Key">
                    <div>
                        <Input value={key} />
                    </div>
                </Field>
                <Field label="Description">
                    <Textarea
                        value={property.description || ''}
                        onChange={(_, data) => handleSchemaChange(key, 'description', data.value)}
                        rows={2}
                    />
                </Field>
                <Field label="Type">
                    <div>
                        <Dropdown
                            placeholder="Select a type"
                            selectedOptions={property.type ? [property.type] : []}
                            value={property.type ? property.type.charAt(0).toUpperCase() + property.type.slice(1) : ''}
                            onOptionSelect={(_, item) => {
                                handleSchemaChange(key, 'type', item.optionValue);
                                if (item.optionValue === 'array') {
                                    handleSchemaChange(key, 'items', { type: 'string' });
                                } else if (item.optionValue === 'object') {
                                    handleSchemaChange(key, 'properties', {});
                                } else {
                                    handleSchemaChange(key, 'items', undefined);
                                    handleSchemaChange(key, 'properties', undefined);
                                }
                            }}
                        >
                            <Option key="string" value="string">
                                String
                            </Option>
                            <Option key="number" value="number">
                                Number
                            </Option>
                            <Option key="boolean" value="boolean">
                                Boolean
                            </Option>
                            <Option key="object" value="object">
                                Object
                            </Option>
                            <Option key="array" value="array">
                                Array
                            </Option>
                        </Dropdown>
                    </div>
                </Field>
                {property.type === 'object' && property.properties && (
                    <div className={classes.root}>
                        <Text>Nested Properties:</Text>
                        {renderNestedProperties(property.properties, key)}
                    </div>
                )}
                {property.type === 'array' && property.items && (
                    <Field label="Array Item Type">
                        <div>
                            <Dropdown
                                placeholder="Select an item type"
                                selectedOptions={property.items.type ? [property.items.type] : []}
                                value={
                                    property.items?.type
                                        ? property.items.type.charAt(0).toUpperCase() + property.items.type.slice(1)
                                        : ''
                                }
                                onOptionSelect={(_, item) =>
                                    handleSchemaChange(key, 'items', { type: item.optionValue })
                                }
                            >
                                <Option key="string" value="string">
                                    String
                                </Option>
                                <Option key="number" value="number">
                                    Number
                                </Option>
                                <Option key="boolean" value="boolean">
                                    Boolean
                                </Option>
                                <Option key="object" value="object">
                                    Object
                                </Option>
                            </Dropdown>
                        </div>
                    </Field>
                )}
                <div>
                    <Button
                        onClick={() => handleRemoveProperty(key)}
                        appearance="outline"
                        size="small"
                        icon={<Delete16Regular />}
                    >
                        Remove Property
                    </Button>
                </div>
            </div>
        );
    };

    // Render the component
    return (
        <div className={classes.root}>
            <Text>{label}</Text>
            <div className={classes.properties}>
                {Object.entries(modelSchema.properties || {}).map(([key, property]) => (
                    <div key={key}>{renderSchemaFieldEditor(key, property)}</div>
                ))}
            </div>
            <div>
                <Button onClick={handleAddProperty} appearance="outline" size="small" icon={<Add16Regular />}>
                    Add New Property
                </Button>
            </div>
        </div>
    );
};
