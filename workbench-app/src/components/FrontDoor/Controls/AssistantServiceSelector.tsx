import { Divider, Dropdown, Label, makeStyles, Option, tokens, Tooltip } from '@fluentui/react-components';
import { Info16Regular, PresenceAvailableRegular } from '@fluentui/react-icons';
import React from 'react';
import { AssistantServiceTemplate } from '../../../libs/useCreateConversation';

const useClasses = makeStyles({
    option: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: tokens.spacingHorizontalXS,
    },
    optionDescription: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalXS,
    },
});

interface AssistantServiceSelectorProps {
    assistantServicesByCategory: Array<{
        category: string;
        assistantServices: AssistantServiceTemplate[];
    }>;
    onChange: (value: AssistantServiceTemplate) => void;
    disabled?: boolean;
}

export const AssistantServiceSelector: React.FC<AssistantServiceSelectorProps> = (props) => {
    const { assistantServicesByCategory, onChange, disabled } = props;
    const classes = useClasses();

    const assistantServiceOption = React.useCallback(
        (assistantService: AssistantServiceTemplate) => {
            const key = JSON.stringify([assistantService.service.assistantServiceId, assistantService.template.id]);
            return (
                <Option key={key} text={assistantService.template.name} value={key}>
                    <div className={classes.option}>
                        <PresenceAvailableRegular color="green" />
                        <Label weight="semibold">{assistantService.template.name}</Label>
                        <Tooltip
                            content={
                                <div className={classes.optionDescription}>
                                    <Label size="small">
                                        <em>{assistantService.template.description}</em>
                                    </Label>
                                    <Divider />
                                    <Label size="small">Assistant service ID:</Label>
                                    <Label size="small">{assistantService.service.assistantServiceId}</Label>
                                </div>
                            }
                            relationship="description"
                        >
                            <Info16Regular />
                        </Tooltip>
                    </div>
                </Option>
            );
        },
        [classes],
    );

    return (
        <Dropdown
            placeholder="Select an assistant service"
            disabled={disabled}
            onOptionSelect={(_event, data) => {
                const [assistantServiceId, templateId] = JSON.parse(data.optionValue as string);
                const assistantService = assistantServicesByCategory
                    .flatMap((category) => category.assistantServices)
                    .find(
                        (assistantService) =>
                            assistantService.service.assistantServiceId === assistantServiceId &&
                            assistantService.template.id === templateId,
                    );
                if (assistantService) {
                    onChange(assistantService);
                }
            }}
        >
            {assistantServicesByCategory.map(({ assistantServices }) =>
                assistantServices
                    .sort((a, b) => a.template.name.localeCompare(b.template.name))
                    .map((assistantService) => assistantServiceOption(assistantService)),
            )}
        </Dropdown>
    );
};
