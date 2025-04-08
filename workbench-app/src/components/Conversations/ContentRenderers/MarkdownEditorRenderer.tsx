import { Button, makeStyles, Text } from '@fluentui/react-components';
import { LockClosedRegular, LockOpenRegular, SaveRegular } from '@fluentui/react-icons';
import { defaultValueCtx, Editor, editorViewCtx, rootCtx, serializerCtx } from '@milkdown/kit/core';
import { commonmark } from '@milkdown/kit/preset/commonmark';
import { Milkdown, MilkdownProvider, useEditor } from '@milkdown/react';
import { nord } from '@milkdown/theme-nord';
import React from 'react';

const useStyles = makeStyles({
    editorContainer: {
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        height: '100%',
        flex: 1,
    },
    milkdownRoot: {
        '& .milkdown': {
            height: '100%',
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            flex: 1,
            overflow: 'auto',
            '& .editor': {
                height: '100%',
            },
        },
        height: '100%',
        width: '100%',
        flex: 1,
        display: 'flex',
        '& [data-milkdown-root="true"]': {
            width: '100%',
        },
    },
    toolbar: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    filenameContainer: {
        display: 'flex',
        alignItems: 'baseline',
        gap: '12px',
    },
    filename: {
        margin: '0',
        fontSize: '2rem',
        fontWeight: 'bold',
        lineHeight: '1',
    },
    readOnlyIndicator: {
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
        color: 'var(--colorNeutralForeground3)',
        fontStyle: 'italic',
    },
    buttonGroup: {
        display: 'flex',
        gap: '4px',
    },
});

interface MilkdownEditorProps {
    content?: string;
    onSave?: (content: string) => void;
    filename?: string;
    readOnly?: boolean;
    onToggleReadOnly?: () => void;
    isBackendReadOnly?: boolean;
}

const MilkdownEditor: React.FC<MilkdownEditorProps> = ({
    content = '',
    onSave,
    filename,
    readOnly = false,
    onToggleReadOnly,
    isBackendReadOnly = false,
}) => {
    const styles = useStyles();
    const { get } = useEditor(
        (root) =>
            Editor.make()
                .config(nord)
                .config((ctx) => {
                    ctx.set(rootCtx, root);
                    ctx.set(defaultValueCtx, content);
                })
                .use(commonmark),
        [content],
    );

    React.useEffect(() => {
        const editor = get();
        if (!editor) return;

        const view = editor.ctx.get(editorViewCtx);
        if (!view) return;

        // Set editor's editable state based on readOnly prop
        view.setProps({ editable: () => !readOnly });
    }, [get, readOnly]);

    const handleSave = React.useCallback(() => {
        if (!onSave) return;

        const editor = get();
        if (!editor) return;

        // Gets the entire Markdown content to save.
        const serializer = editor.ctx.get(serializerCtx);
        const view = editor.ctx.get(editorViewCtx);
        if (!serializer || !view) return;

        const content = serializer(view.state.doc);
        onSave(content);
    }, [get, onSave]);

    return (
        <>
            {/* Toolbar with filename and save button */}
            {(onSave || filename || readOnly) && (
                <div className={styles.toolbar}>
                    <div className={styles.filenameContainer}>
                        {/* File name */}
                        {filename && (
                            <Text as="h1" className={styles.filename}>
                                {/* Remove file extension from filename */}
                                {filename ? filename.replace(/\.[^/.]+$/, '') : ''}
                            </Text>
                        )}
                        {/* Read-only indicator */}
                        {readOnly && (
                            <div className={styles.readOnlyIndicator}>
                                <LockClosedRegular />
                                <Text>{isBackendReadOnly ? 'View-only due to assistant at work' : 'View-only'}</Text>
                            </div>
                        )}
                    </div>
                    <div className={styles.buttonGroup}>
                        {/* Save button */}
                        {onSave && !readOnly && (
                            <Button appearance="primary" icon={<SaveRegular />} onClick={handleSave}>
                                Save
                            </Button>
                        )}
                        {/* Toggle read-only button - hide if backend has enforced read-only */}
                        {onToggleReadOnly && !isBackendReadOnly && (
                            <Button
                                icon={readOnly ? <LockOpenRegular /> : <LockClosedRegular />}
                                onClick={onToggleReadOnly}
                                appearance="subtle"
                            >
                                {readOnly ? 'Switch to Edit Mode' : 'Switch to View Mode'}
                            </Button>
                        )}
                    </div>
                </div>
            )}
            <div className={styles.milkdownRoot}>
                <Milkdown />
            </div>
        </>
    );
};

export interface MilkdownEditorWrapperProps extends MilkdownEditorProps {
    onSubmit?: (content: string) => Promise<void>;
    readOnly?: boolean;
}

export const MilkdownEditorWrapper: React.FC<MilkdownEditorWrapperProps> = ({
    content,
    onSubmit,
    filename,
    readOnly = false,
}) => {
    const styles = useStyles();
    const [isSubmitting, setIsSubmitting] = React.useState(false);
    const [isReadOnly, setIsReadOnly] = React.useState(readOnly);

    // Track if read-only state is backend-enforced
    const isBackendReadOnly = readOnly;

    React.useEffect(() => {
        setIsReadOnly(readOnly);
    }, [readOnly]);

    const handleSave = React.useCallback(
        async (updatedContent: string) => {
            if (!onSubmit || isSubmitting || isReadOnly) return;

            setIsSubmitting(true);
            try {
                await onSubmit(updatedContent);
            } finally {
                setIsSubmitting(false);
            }
        },
        [onSubmit, isSubmitting, isReadOnly],
    );

    const toggleReadOnly = React.useCallback(() => {
        // Only allow toggling if not backend-enforced
        if (!isBackendReadOnly) {
            setIsReadOnly(!isReadOnly);
        }
    }, [isReadOnly, isBackendReadOnly]);

    return (
        <div className={styles.editorContainer}>
            <MilkdownProvider>
                <MilkdownEditor
                    content={content}
                    onSave={onSubmit && !isReadOnly ? handleSave : undefined}
                    filename={filename}
                    readOnly={isReadOnly}
                    onToggleReadOnly={toggleReadOnly}
                    isBackendReadOnly={isBackendReadOnly}
                />
            </MilkdownProvider>
        </div>
    );
};
