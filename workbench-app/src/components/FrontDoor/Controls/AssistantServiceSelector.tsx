import { Divider, Dropdown, Label, makeStyles, Option, tokens, Tooltip } from '@fluentui/react-components';
import { Info16Regular, PresenceAvailableRegular, PresenceOfflineRegular } from '@fluentui/react-icons';
import React from 'react';
import { AssistantServiceRegistration } from '../../../models/AssistantServiceRegistration';

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
        assistantServices: AssistantServiceRegistration[];
    }>;
    onChange: (value: AssistantServiceRegistration) => void;
    disabled?: boolean;
}

export const AssistantServiceSelector: React.FC<AssistantServiceSelectorProps> = (props) => {
    const { assistantServicesByCategory, onChange, disabled } = props;
    const classes = useClasses();

    const assistantServiceOption = React.useCallback(
        (assistantService: AssistantServiceRegistration) => (
            <Option
                key={assistantService.assistantServiceId}
                text={assistantService.name}
                value={assistantService.assistantServiceId}
            >
                <div className={classes.option}>
                    {assistantService.assistantServiceOnline ? (
                        <PresenceAvailableRegular color="green" />
                    ) : (
                        <PresenceOfflineRegular color="red" />
                    )}
                    <Label weight="semibold">{assistantService.name}</Label>
                    <Tooltip
                        content={
                            <div className={classes.optionDescription}>
                                <Label size="small">
                                    <em>{assistantService.description}</em>
                                </Label>
                                <Divider />
                                <Label size="small">Assistant service ID:</Label>
                                <Label size="small">{assistantService.assistantServiceId}</Label>
                                <Divider />
                                <Label size="small">Hosted at:</Label>
                                <Label size="small">{assistantService.assistantServiceUrl}</Label>
                                <Divider />
                                <Label size="small">Created by:</Label>
                                <Label size="small">{assistantService.createdByUserName}</Label>
                                <Label size="small">[{assistantService.createdByUserId}]</Label>
                            </div>
                        }
                        relationship="description"
                    >
                        <Info16Regular />
                    </Tooltip>
                </div>
            </Option>
        ),
        [classes],
    );

    return (
        <Dropdown
            placeholder="Select an assistant service"
            disabled={disabled}
            onOptionSelect={(_event, data) => {
                const assistantService = assistantServicesByCategory
                    .flatMap((category) => category.assistantServices)
                    .find((assistantService) => assistantService.assistantServiceId === (data.optionValue as string));
                if (assistantService) {
                    onChange(assistantService);
                }
            }}
        >
            {assistantServicesByCategory.map(({ assistantServices }) =>
                assistantServices
                    .sort((a, b) => a.name.localeCompare(b.name))
                    .map((assistantService) => assistantServiceOption(assistantService)),
            )}
        </Dropdown>
    );
};
