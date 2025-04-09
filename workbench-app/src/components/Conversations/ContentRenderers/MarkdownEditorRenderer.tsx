import { Button, makeStyles, Text } from '@fluentui/react-components';
import { LockClosedRegular, LockOpenRegular, SaveRegular } from '@fluentui/react-icons';
import { Crepe } from '@milkdown/crepe';
import '@milkdown/crepe/theme/common/style.css';
import '@milkdown/crepe/theme/frame.css';
import { Milkdown, MilkdownProvider, useEditor } from '@milkdown/react';
import React from 'react';

const useStyles = makeStyles({
    editorContainer: {
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        height: '100%',
        flex: 1,
    },
    milkdownWrapper: {
        height: '100%',
        width: '100%',
        flex: 1,
        display: 'flex',
        '& .milkdown': {
            height: '100%',
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            flex: 1,
            overflow: 'auto',
        },
        '& .ProseMirror': {
            margin: '10px 0 0 0',
            padding: '14px 20px 20px 70px',
        },
        '& [data-milkdown-root="true"]': {
            height: '100%',
            width: '100%',
        },
    },
    toolbar: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingLeft: '70px',
    },
    filenameContainer: {
        display: 'flex',
        alignItems: 'baseline',
        gap: '12px',
    },
    filename: {
        margin: '0',
        fontSize: '42px',
        fontWeight: 'bold',
        lineHeight: '1',
        fontFamily: 'Noto Sans',
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
    saveButton: {
        backgroundColor: 'var(--colorStatusDangerBackground2)',
        color: 'var(--colorStatusDangerForeground2)',
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
    const [editorInstance, setEditorInstance] = React.useState<Crepe | null>(null);
    const [hasUnsavedChanges, setHasUnsavedChanges] = React.useState(false);
    const initialContentRef = React.useRef(content);

    useEditor(
        (root) => {
            const crepe = new Crepe({
                root,
                defaultValue: content,
                featureConfigs: {
                    [Crepe.Feature.Placeholder]: {
                        text: 'Just start typing...',
                        mode: 'block',
                    },
                },
            });

            crepe.create().then(() => {
                crepe.setReadonly(readOnly);
                setEditorInstance(crepe);

                // Set up content change detection
                crepe.on((listener) => {
                    listener.markdownUpdated(() => {
                        const currentContent = crepe.getMarkdown();
                        setHasUnsavedChanges(currentContent !== initialContentRef.current);
                    });
                });
            });

            return crepe;
        },
        [content],
    );

    // Reset unsaved changes flag when content prop changes (after saving)
    React.useEffect(() => {
        initialContentRef.current = content;
        setHasUnsavedChanges(false);
    }, [content]);

    // Update readonly state when it changes
    React.useEffect(() => {
        if (editorInstance) {
            editorInstance.setReadonly(readOnly);
        }
    }, [readOnly, editorInstance]);

    const handleSave = React.useCallback(() => {
        if (!onSave || !editorInstance || !hasUnsavedChanges) return;
        const currentContent = editorInstance.getMarkdown();
        // Replace <br> tags with unicode line separator to prevent parser issues.
        const parsedContent = currentContent.replace(/<br\s*\/?>|<br>/gi, '\u2028');

        onSave(parsedContent);
        // Note: We don't reset hasUnsavedChanges here because the parent component
        // should update the content prop which will trigger the useEffect above
    }, [onSave, editorInstance, hasUnsavedChanges]);

    // Add keyboard shortcut for Ctrl+S
    React.useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                if (!readOnly && hasUnsavedChanges) {
                    handleSave();
                }
            }
        };

        document.addEventListener('keydown', handleKeyDown);
        return () => {
            document.removeEventListener('keydown', handleKeyDown);
        };
    }, [handleSave, readOnly, hasUnsavedChanges]);

    // Add beforeunload event listener to warn when closing with unsaved changes
    React.useEffect(() => {
        const handleBeforeUnload = (e: BeforeUnloadEvent) => {
            if (hasUnsavedChanges && !readOnly) {
                // Standard way to show confirmation dialog when closing
                const message = 'You have unsaved changes in the editor. Are you sure you want to leave?';
                e.preventDefault();
                return message;
            }
            return undefined;
        };

        window.addEventListener('beforeunload', handleBeforeUnload);
        return () => {
            window.removeEventListener('beforeunload', handleBeforeUnload);
        };
    }, [hasUnsavedChanges, readOnly]);

    return (
        <>
            {/* Toolbar with filename and save button */}
            {(onSave || filename || readOnly) && (
                <div className={styles.toolbar}>
                    <div className={styles.filenameContainer}>
                        {filename && (
                            <Text as="h1" className={styles.filename}>
                                {filename.replace(/\.[^/.]+$/, '')}
                            </Text>
                        )}
                        {readOnly && (
                            <div className={styles.readOnlyIndicator}>
                                <LockClosedRegular />
                                <Text>{isBackendReadOnly ? 'View-only due to assistant at work' : 'View-only'}</Text>
                            </div>
                        )}
                    </div>
                    <div className={styles.buttonGroup}>
                        {onSave && !readOnly && (
                            <Button
                                appearance="subtle"
                                icon={<SaveRegular />}
                                onClick={handleSave}
                                disabled={!hasUnsavedChanges}
                                className={hasUnsavedChanges ? styles.saveButton : undefined}
                            >
                                Save Changes
                            </Button>
                        )}
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
            <div className={styles.milkdownWrapper}>
                <Milkdown />
            </div>
        </>
    );
};

export interface MilkdownEditorWrapperProps extends MilkdownEditorProps {
    onSubmit?: (content: string) => Promise<void>;
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
