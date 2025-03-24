import { Checkbox, Field, Input, makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { AssistantServiceTemplate, useCreateConversation } from '../../../libs/useCreateConversation';
import { AssistantImport } from '../../Assistants/AssistantImport';
import { AssistantSelector } from './AssistantSelector';
import { AssistantServiceSelector } from './AssistantServiceSelector';

const useClasses = makeStyles({
    content: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
    serviceOptions: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'space-between',
    },
    actions: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'end',
        alignItems: 'center',
        gap: tokens.spacingHorizontalM,
    },
});

export interface NewConversationData {
    assistantId?: string;
    assistantServiceId?: string;
    templateId?: string;
    name?: string;
}

interface NewConversationFormProps {
    onSubmit?: () => void;
    onChange?: (isValid: boolean, data: NewConversationData) => void;
    disabled?: boolean;
}

export const NewConversationForm: React.FC<NewConversationFormProps> = (props) => {
    const { onSubmit, onChange, disabled } = props;
    const classes = useClasses();
    const {
        isFetching: createConversationIsFetching,
        assistants,
        assistantServicesByCategories,
    } = useCreateConversation();

    const [config, setConfig] = React.useState<NewConversationData>({
        assistantId: '',
        assistantServiceId: '',
        name: '',
    });
    const [manualEntry, setManualEntry] = React.useState(false);

    const checkIsValid = React.useCallback((data: NewConversationData) => {
        if (!data.assistantId) {
            return false;
        }

        if (data.assistantId === 'new') {
            if (!data.assistantServiceId || !data.name || !data.templateId) {
                return false;
            }
        }

        return true;
    }, []);

    const isValid = React.useMemo(() => checkIsValid(config), [checkIsValid, config]);

    const updateAndNotifyChange = React.useCallback(
        (data: NewConversationData) => {
            const updatedConfig = { ...config, ...data };
            if (data.assistantId === 'new') {
                updatedConfig.assistantServiceId = data.assistantServiceId ?? '';
                updatedConfig.name = data.name ?? '';
                updatedConfig.templateId = data.templateId ?? '';
            }

            setConfig(updatedConfig);
            onChange?.(checkIsValid(updatedConfig), updatedConfig);
        },
        [checkIsValid, config, onChange],
    );

    return (
        <form
            onSubmit={(event) => {
                event.preventDefault();
                if (isValid) {
                    onSubmit?.();
                }
            }}
        >
            <div className={classes.content}>
                <Field label="Assistant">
                    {createConversationIsFetching ? (
                        <Input disabled={true} value="Loading..." />
                    ) : (
                        <AssistantSelector
                            assistants={assistants}
                            defaultAssistant={assistants?.[0]}
                            onChange={(assistantId) =>
                                updateAndNotifyChange({
                                    assistantId,
                                    assistantServiceId: assistantId === 'new' ? '' : undefined,
                                    name: assistantId === 'new' ? '' : undefined,
                                })
                            }
                            disabled={disabled}
                        />
                    )}
                </Field>
                {config.assistantId === 'new' && (
                    <>
                        {!manualEntry && (
                            <Field label="Assistant Service">
                                <AssistantServiceSelector
                                    disabled={disabled}
                                    assistantServicesByCategory={assistantServicesByCategories}
                                    onChange={(assistantService: AssistantServiceTemplate) =>
                                        updateAndNotifyChange({
                                            assistantServiceId: assistantService.service.assistantServiceId,
                                            name: assistantService.template.name,
                                            templateId: assistantService.template.id,
                                        })
                                    }
                                />
                            </Field>
                        )}
                        {manualEntry && (
                            <Field label="Assistant Service ID">
                                <Input
                                    disabled={disabled}
                                    value={config.assistantServiceId}
                                    onChange={(_event, data) =>
                                        updateAndNotifyChange({ assistantServiceId: data?.value })
                                    }
                                    aria-autocomplete="none"
                                />
                            </Field>
                        )}
                        <Field label="Name">
                            <Input
                                disabled={disabled}
                                value={config.name}
                                onChange={(_event, data) => updateAndNotifyChange({ name: data?.value })}
                                aria-autocomplete="none"
                            />
                        </Field>
                        <div className={classes.serviceOptions}>
                            <Checkbox
                                disabled={disabled}
                                style={{ whiteSpace: 'nowrap' }}
                                label="Enter Assistant Service ID"
                                checked={manualEntry}
                                onChange={(_event, data) => {
                                    setManualEntry(data.checked === true);
                                }}
                            />
                            <AssistantImport label="Import Assistant" disabled={disabled} />
                        </div>
                    </>
                )}
                <button disabled={disabled} type="submit" hidden />
            </div>
        </form>
    );
};
