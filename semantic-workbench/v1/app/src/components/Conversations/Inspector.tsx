// Copyright (c) Microsoft. All rights reserved.

import { Text, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import { EventSourceMessage } from '@microsoft/fetch-event-source';
import {} from '@rjsf/core';
import Form from '@rjsf/fluentui-rc';
import { RegistryWidgetsType } from '@rjsf/utils';
import validator from '@rjsf/validator-ajv8';
import React from 'react';
import { WorkbenchEventSource } from '../../libs/WorkbenchEventSource';
import { useEnvironment } from '../../libs/useEnvironment';
import { AssistantStateDescription } from '../../models/AssistantStateDescription';
import { useGetConversationStateQuery, useUpdateConversationStateMutation } from '../../services/workbench';
import { CustomizedArrayFieldTemplate } from '../App/FormWidgets/CustomizedArrayFieldTemplate';
import { CustomizedObjectFieldTemplate } from '../App/FormWidgets/CustomizedObjectFieldTemplate';
import { InspectableWidget } from '../App/FormWidgets/InspectableWidget';
import { Loading } from '../App/Loading';
import { CodeContentRenderer } from './ContentRenderers/CodeContentRenderer';
import { ContentRenderer } from './ContentRenderers/ContentRenderer';
import { DebugInspector } from './DebugInspector';

const useClasses = makeStyles({
    root: {
        display: 'grid',
        gridTemplateRows: 'auto 1fr',
        height: '100%',
    },
    header: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
        ...shorthands.padding(tokens.spacingVerticalM),
    },
    body: {
        display: 'flex',
        flexDirection: 'column',
        overflow: 'auto',
    },
    form: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
});

interface InspectorProps {
    assistantId: string;
    conversationId: string;
    stateDescription: AssistantStateDescription;
}

export const Inspector: React.FC<InspectorProps> = (props) => {
    const { assistantId, conversationId, stateDescription } = props;
    const classes = useClasses();
    const {
        data: state,
        error: stateError,
        isLoading: isLoadingState,
        refetch: refetchState,
    } = useGetConversationStateQuery({ assistantId, stateId: stateDescription.id, conversationId });
    const [updateConversationState] = useUpdateConversationStateMutation();
    const [formData, setFormData] = React.useState<object>();
    const [isSubmitting, setIsSubmitting] = React.useState(false);
    const environment = useEnvironment();

    if (stateError) {
        const errorMessage = JSON.stringify(stateError);
        throw new Error(`Error loading assistant state: ${errorMessage}`);
    }

    React.useEffect(() => {
        var workbenchEventSource: WorkbenchEventSource | undefined;

        const handleEvent = (event: EventSourceMessage) => {
            const { data } = JSON.parse(event.data);
            if (assistantId !== data['assistant_id']) return;
            if (stateDescription.id !== data['state_id']) return;
            if (conversationId !== data['conversation_id']) return;
            refetchState();
        };

        (async () => {
            workbenchEventSource = await WorkbenchEventSource.createOrUpdate(environment.url, conversationId);
            workbenchEventSource.addEventListener('assistant.state.updated', handleEvent);
        })();

        return () => {
            workbenchEventSource?.removeEventListener('assistant.state.updated', handleEvent);
        };
    }, [environment, assistantId, stateDescription.id, conversationId, refetchState]);

    React.useEffect(() => {
        if (isLoadingState) return;
        setFormData(state?.data);
    }, [isLoadingState, state]);

    const handleChange = async (updatedState: object) => {
        if (!state || isSubmitting) return;
        setIsSubmitting(true);
        setFormData(updatedState);
        await updateConversationState({ assistantId, conversationId, state: { ...state, data: updatedState } });
        setIsSubmitting(false);
    };

    if (isLoadingState || !state) {
        return <Loading />;
    }

    const widgets: RegistryWidgetsType = {
        inspectable: InspectableWidget,
    };

    const templates = {
        ArrayFieldTemplate: CustomizedArrayFieldTemplate,
        ObjectFieldTemplate: CustomizedObjectFieldTemplate,
    };

    const renderers = {
        default: () => {
            // check to see if data contains a key "content" that is a string, if so, render it
            // with the default content renderer, otherwise, render the data as a json object
            if ('content' in state.data && typeof state.data['content'] === 'string') {
                return <ContentRenderer content={state.data['content']} />;
            }
            return <CodeContentRenderer content={JSON.stringify(state.data, null, 2)} language="json" />;
        },
        jsonSchema: () => {
            return (
                <Form
                    aria-autocomplete="none"
                    autoComplete="off"
                    className={classes.form}
                    widgets={widgets}
                    templates={templates}
                    schema={state.jsonSchema ?? {}}
                    uiSchema={{
                        ...state.uiSchema,
                        'ui:submitButtonOptions': {
                            submitText: 'Save',
                            props: {
                                disabled: JSON.stringify(formData) === JSON.stringify(state.data),
                            },
                        },
                    }}
                    formData={formData}
                    validator={validator}
                    onChange={(data) => {
                        setFormData(data.formData);
                    }}
                    onSubmit={(data, event) => {
                        event.preventDefault();
                        handleChange(data.formData);
                    }}
                />
            );
        },
    };

    const getRender = () => {
        if (state.jsonSchema) {
            return renderers.jsonSchema;
        }
        return renderers.default;
    };

    const renderer = getRender();

    let debugInspector = null;
    if ('metadata' in state.data) {
        if ('debug' in (state.data.metadata as Record<string, unknown>)) {
            const debug = (state.data.metadata as Record<string, Record<string, unknown>>).debug;
            debugInspector = <DebugInspector debug={debug} />;
        }
    }

    return (
        <div className={classes.root}>
            <div className={classes.header}>
                <Text>{stateDescription.description}</Text>
                {debugInspector}
            </div>
            <div className={classes.body}>{renderer()}</div>
        </div>
    );
};
