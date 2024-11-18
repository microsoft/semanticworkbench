import { Dropdown, Option, OptionGroup } from '@fluentui/react-components';
import React from 'react';
import { Assistant } from '../../../models/Assistant';

interface AssistantSelectorProps {
    assistants?: Assistant[];
    onChange: (assistantId: string) => void;
    disabled?: boolean;
}

export const AssistantSelector: React.FC<AssistantSelectorProps> = (props) => {
    const { assistants, onChange, disabled } = props;

    return (
        <Dropdown
            placeholder="Select an assistant"
            disabled={disabled}
            onOptionSelect={(_event, data) => onChange(data.optionValue as string)}
        >
            <Option text="Create new assistant" value="new">
                Create new assistant
            </Option>
            <OptionGroup label="Existing Assistants">
                {assistants
                    ?.slice()
                    .sort((a, b) => a.name.localeCompare(b.name))
                    .map((assistant) => (
                        <Option key={assistant.id} text={assistant.name} value={assistant.id}>
                            {assistant.name}
                        </Option>
                    ))}
            </OptionGroup>
        </Dropdown>
    );
};
