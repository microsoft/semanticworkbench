// Copyright (c) Microsoft. All rights reserved.

import { Button, Text, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import { ArrowDownloadRegular } from '@fluentui/react-icons';
import {} from '@rjsf/core';
import Form from '@rjsf/fluentui-rc';
import { RegistryWidgetsType } from '@rjsf/utils';
import validator from '@rjsf/validator-ajv8';
import React from 'react';
import { ConversationState } from '../../../models/ConversationState';
import { ConversationStateDescription } from '../../../models/ConversationStateDescription';
import { useUpdateConversationStateMutation } from '../../../services/workbench';
import { CustomizedArrayFieldTemplate } from '../../App/FormWidgets/CustomizedArrayFieldTemplate';
import { CustomizedObjectFieldTemplate } from '../../App/FormWidgets/CustomizedObjectFieldTemplate';
import { InspectableWidget } from '../../App/FormWidgets/InspectableWidget';
import { CodeContentRenderer } from '../ContentRenderers/CodeContentRenderer';
import { ContentListRenderer } from '../ContentRenderers/ContentListRenderer';
import { ContentRenderer } from '../ContentRenderers/ContentRenderer';
import { MilkdownEditorWrapper } from '../ContentRenderers/MarkdownEditorRenderer';
import { DebugInspector } from '../DebugInspector';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
    },
    header: {
        flexShrink: 0,
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
        ...shorthands.padding(tokens.spacingVerticalM),
    },
    body: {
        flexGrow: 1,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'auto',
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
    },
    form: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
});

interface Attachment {
    filename: string;
    content: string;
}

interface AssistantInspectorProps {
    assistantId: string;
    conversationId: string;
    stateDescription: ConversationStateDescription;
    state: ConversationState;
}

export const AssistantInspector: React.FC<AssistantInspectorProps> = (props) => {
    const { assistantId, conversationId, stateDescription, state } = props;
    const classes = useClasses();
    const [updateConversationState] = useUpdateConversationStateMutation();
    const [formData, setFormData] = React.useState<object>(state.data);
    const [isSubmitting, setIsSubmitting] = React.useState(false);

    const handleChange = React.useCallback(
        async (updatedState: object) => {
            if (!state || isSubmitting) return;
            setIsSubmitting(true);
            setFormData(updatedState);
            await updateConversationState({ assistantId, conversationId, state: { ...state, data: updatedState } });
            setIsSubmitting(false);
        },
        [assistantId, conversationId, state, updateConversationState, isSubmitting],
    );

    const defaultRenderer = React.useCallback(() => {
        // check to see if data contains a key "content" that is a string, if so, render it
        // with the default content renderer, otherwise, render the data as a json object
        if ('content' in state.data) {
            const content = state.data['content'];
            if (typeof content === 'string') {
                return <ContentRenderer content={content} />;
            }
            if (Array.isArray(content)) {
                return <ContentListRenderer contentList={content} />;
            }
        }
        return <CodeContentRenderer content={JSON.stringify(state.data, null, 2)} language="json" />;
    }, [state]);

    const jsonSchemaRenderer = React.useCallback(() => {
        const widgets: RegistryWidgetsType = {
            inspectable: InspectableWidget,
        };

        const templates = {
            ArrayFieldTemplate: CustomizedArrayFieldTemplate,
            ObjectFieldTemplate: CustomizedObjectFieldTemplate,
        };
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
                        ...state.uiSchema?.['ui:submitButtonOptions'],
                        props: {
                            disabled: JSON.stringify(formData) === JSON.stringify(state.data),
                            ...state.uiSchema?.['ui:submitButtonOptions']?.['props'],
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
    }, [classes.form, formData, handleChange, state]);

    const markdownEditorRenderer = React.useCallback(() => {
        // Check if the data contains markdown_content, if not assume its empty.
        var markdownContent = 'markdown_content' in state.data ? String(state.data.markdown_content ?? '') : '';
        // Replace <br> tags with unicode line separator to prevent parser issues.
        markdownContent = markdownContent.replace(/<br\s*\/?>|<br>/gi, '\u2028');
        const filename = 'filename' in state.data ? String(state.data.filename) : undefined;
        // Check if the document is in read-only mode
        const isReadOnly = 'readonly' in state.data ? Boolean(state.data.readonly) : false;

        return (
            <MilkdownEditorWrapper
                content={markdownContent}
                filename={filename}
                readOnly={isReadOnly}
                onSubmit={async (updatedContent: string) => {
                    if (!state || isSubmitting || isReadOnly) return;
                    setIsSubmitting(true);
                    try {
                        // Convert back the unicode line separators to <br> tags
                        const processedContent = updatedContent.replace(/\u2028/g, '<br>');
                        const updatedState = {
                            ...state.data,
                            markdown_content: processedContent,
                        };
                        setFormData(updatedState);
                        await updateConversationState({
                            assistantId,
                            conversationId,
                            state: { ...state, data: updatedState },
                        });
                    } finally {
                        setIsSubmitting(false);
                    }
                }}
            />
        );
    }, [state, isSubmitting, updateConversationState, assistantId, conversationId]);

    let debugInspector = null;
    if (state && 'metadata' in state.data) {
        if ('debug' in (state.data.metadata as Record<string, unknown>)) {
            const debug = (state.data.metadata as Record<string, Record<string, unknown>>).debug;
            debugInspector = <DebugInspector debug={debug} />;
        }
    }

    const attachments = (state && 'attachments' in state.data ? state.data['attachments'] : []) as Attachment[];

    const handleDownloadAttachment = async (attachment: Attachment) => {
        // download helper function
        const download = (filename: string, href: string) => {
            const a = document.createElement('a');
            a.download = filename;
            a.href = href;
            a.click();
        };

        // if the content is a data URL, use it directly, otherwise create a blob URL
        if (attachment.content.startsWith('data:')) {
            download(attachment.filename, attachment.content);
        } else {
            const url = URL.createObjectURL(new Blob([attachment.content]));
            download(attachment.filename, url);
            URL.revokeObjectURL(url);
        }
    };

    const renderer = () => {
        if (!state) {
            return defaultRenderer();
        }
        if (state.jsonSchema) {
            return jsonSchemaRenderer();
        } else if (state.data && 'markdown_content' in state.data) {
            return markdownEditorRenderer();
        }
        return defaultRenderer();
    };
    return (
        <div className={classes.root}>
            <div className={classes.header}>
                <Text>{stateDescription.description}</Text>
                {debugInspector}
                {attachments.map((attachment) => (
                    <div key={attachment.filename}>
                        <Button
                            onClick={() => handleDownloadAttachment(attachment)}
                            icon={<ArrowDownloadRegular />}
                            appearance="subtle"
                        >
                            {attachment.filename}
                        </Button>
                    </div>
                ))}
            </div>
            <div className={classes.body}>{renderer()}</div>
        </div>
    );
};
