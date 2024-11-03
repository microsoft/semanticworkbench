import { Checkbox, Field, Input, makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { useCreateConversation } from '../../../libs/useCreateConversation';
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
    title?: string;
    assistantId?: string;
    assistantServiceId?: string;
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
    const { assistants, assistantServicesByCategories } = useCreateConversation();

    const [title, setTitle] = React.useState('');
    const [assistantId, setAssistantId] = React.useState<string>();
    const [name, setName] = React.useState('');
    const [assistantServiceId, setAssistantServiceId] = React.useState('');
    const [manualEntry, setManualEntry] = React.useState(false);

    const isValid = React.useMemo(() => {
        if (!title || !assistantId) {
            return false;
        }

        if (assistantId === 'new') {
            if (!assistantServiceId || !name) {
                return false;
            }
        }

        return true;
    }, [title, assistantId, assistantServiceId, name]);

    const notifyChange = React.useCallback(() => {
        onChange?.(isValid, {
            title: title === '' ? undefined : title,
            assistantId,
            assistantServiceId: assistantServiceId === '' ? undefined : assistantServiceId,
            name: name === '' ? undefined : name,
        });
    }, [onChange, isValid, title, assistantId, assistantServiceId, name]);

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
                <Field label="Title">
                    <Input
                        disabled={disabled}
                        value={title}
                        onChange={(_event, data) => {
                            setTitle(data?.value);
                            notifyChange();
                        }}
                        aria-autocomplete="none"
                    />
                </Field>
                <Field label="Assistant">
                    <AssistantSelector
                        assistants={assistants}
                        onChange={(assistantId) => {
                            setAssistantId(assistantId);
                            if (assistantId === 'new') {
                                setAssistantServiceId('');
                                setName('');
                                notifyChange();
                            }
                        }}
                        disabled={disabled}
                    />
                </Field>
                {assistantId === 'new' && (
                    <>
                        {!manualEntry && (
                            <Field label="Assistant Service">
                                <AssistantServiceSelector
                                    disabled={disabled}
                                    assistantServicesByCategory={assistantServicesByCategories}
                                    onChange={(assistantService) => {
                                        setAssistantServiceId(assistantService.assistantServiceId);
                                        setName(assistantService.name);
                                        notifyChange();
                                    }}
                                />
                            </Field>
                        )}
                        {manualEntry && (
                            <Field label="Assistant Service ID">
                                <Input
                                    disabled={disabled}
                                    value={assistantServiceId}
                                    onChange={(_event, data) => {
                                        setAssistantServiceId(data?.value);
                                        notifyChange();
                                    }}
                                    aria-autocomplete="none"
                                />
                            </Field>
                        )}
                        <Field label="Name">
                            <Input
                                disabled={disabled}
                                value={name}
                                onChange={(_event, data) => {
                                    setName(data?.value);
                                    notifyChange();
                                }}
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
                                    notifyChange();
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
