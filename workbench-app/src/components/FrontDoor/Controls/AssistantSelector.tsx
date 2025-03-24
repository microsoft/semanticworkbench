import { Dropdown, Option, OptionGroup } from '@fluentui/react-components';
import React from 'react';
import { Assistant } from '../../../models/Assistant';

interface AssistantSelectorProps {
    assistants?: Assistant[];
    defaultAssistant?: Assistant;
    onChange: (assistantId: string) => void;
    disabled?: boolean;
}

export const AssistantSelector: React.FC<AssistantSelectorProps> = (props) => {
    const { defaultAssistant, assistants, onChange, disabled } = props;
    const [emittedDefaultAssistant, setEmittedDefaultAssistant] = React.useState<boolean>(false);

    // Call onChange when defaultAssistant changes or on initial mount
    React.useEffect(() => {
        if (defaultAssistant && !emittedDefaultAssistant) {
            setEmittedDefaultAssistant(true);
            onChange(defaultAssistant.id);
        }
    }, [defaultAssistant, emittedDefaultAssistant, onChange]);

    return (
        <Dropdown
            placeholder="Select an assistant"
            disabled={disabled}
            onOptionSelect={(_event, data) => onChange(data.optionValue as string)}
            defaultSelectedOptions={defaultAssistant ? [defaultAssistant.id] : []}
            defaultValue={defaultAssistant ? defaultAssistant.name : undefined}
        >
            <OptionGroup>
                {assistants
                    ?.slice()
                    .sort((a, b) => a.name.localeCompare(b.name))
                    .map((assistant) => (
                        <Option key={assistant.id} text={assistant.name} value={assistant.id}>
                            {assistant.name}
                        </Option>
                    ))}
            </OptionGroup>
            <Option text="Create new assistant" value="new">
                Create new assistant
            </Option>
        </Dropdown>
    );
};
