import { Button, Dropdown, Input, Label, Option, Text } from '@fluentui/react-components';
import { WidgetProps } from '@rjsf/utils';
import React from 'react';

export const BaseModelEditorWidget: React.FC<WidgetProps> = ({ value, onChange }) => {
    // Define the schema type
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

    const [modelSchema, setModelSchema] = React.useState<ModelSchema>(() => {
        return typeof value === 'string' ? JSON.parse(value) : value || {};
    });

    React.useEffect(() => {
        setModelSchema(typeof value === 'string' ? JSON.parse(value) : value || {});
    }, [value]);

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

    const handleRemoveProperty = (key: string) => {
        const { [key]: _, ...remainingProperties } = modelSchema.properties || {};
        const updatedModelSchema = {
            ...modelSchema,
            properties: remainingProperties,
        };
        setModelSchema(updatedModelSchema);
        onChange(JSON.stringify(updatedModelSchema));
    };

    const renderNestedProperties = (properties: ModelSchema['properties'], parentKey: string) => {
        return (
            <div style={{ marginLeft: '20px', borderLeft: '2px solid #ccc', paddingLeft: '10px' }}>
                {Object.entries(properties || {}).map(([key, property]) => (
                    <div key={key}>{renderSchemaFieldEditor(`${parentKey}.${key}`, property)}</div>
                ))}
            </div>
        );
    };

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
            <div style={{ border: '1px solid #ccc', padding: '10px', borderRadius: '4px', marginBottom: '10px' }}>
                <Label>Title</Label>
                <Input
                    value={property.title || ''}
                    onChange={(_, data) => handleSchemaChange(key, 'title', data.value)}
                    style={{ marginBottom: '10px' }}
                />
                <Label>Type</Label>
                <Dropdown
                    placeholder="Select a type"
                    selectedOptions={property.type ? [property.type] : []}
                    value={property.type ? property.type.charAt(0).toUpperCase() + property.type.slice(1) : ''}
                    onOptionSelect={(_, item) => {
                        handleSchemaChange(key, 'type', item.optionValue);
                        if (item.optionValue === 'array') {
                            handleSchemaChange(key, 'items', { type: 'string' });
                        } else {
                            handleSchemaChange(key, 'items', undefined);
                        }
                    }}
                    style={{ marginBottom: '10px' }}
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
                <Label>Description</Label>
                <Input
                    value={property.description || ''}
                    onChange={(_, data) => handleSchemaChange(key, 'description', data.value)}
                    style={{ marginBottom: '10px' }}
                />
                {property.type === 'object' && property.properties && (
                    <div>
                        <Text>Nested Properties:</Text>
                        {renderNestedProperties(property.properties, key)}
                    </div>
                )}
                {property.type === 'array' && property.items && (
                    <div>
                        <Label>Array Item Type</Label>
                        <Dropdown
                            placeholder="Select an item type"
                            selectedOptions={property.items.type ? [property.items.type] : []}
                            value={
                                property.items?.type
                                    ? property.items.type.charAt(0).toUpperCase() + property.items.type.slice(1)
                                    : ''
                            }
                            onOptionSelect={(_, item) => handleSchemaChange(key, 'items', { type: item.optionValue })}
                            style={{ marginBottom: '10px' }}
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
                )}
                <Button onClick={() => handleRemoveProperty(key)} style={{ marginTop: '10px' }}>
                    Remove Property
                </Button>
            </div>
        );
    };

    return (
        <div className="base-model-editor-widget">
            <Text>Edit Model Schema</Text>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {Object.entries(modelSchema.properties || {}).map(([key, property]) => (
                    <div key={key}>{renderSchemaFieldEditor(key, property)}</div>
                ))}
            </div>
            <Button onClick={handleAddProperty} style={{ marginTop: '16px' }}>
                Add New Property
            </Button>
        </div>
    );
};
