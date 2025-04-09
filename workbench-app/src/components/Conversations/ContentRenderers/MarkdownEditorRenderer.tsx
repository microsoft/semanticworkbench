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
            padding: '14px 20px 20px 80px',
        },
    },
    toolbar: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingLeft: '80px',
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
            });

            return crepe;
        },
        [content],
    );

    // Update readonly state when it changes
    React.useEffect(() => {
        if (editorInstance) {
            editorInstance.setReadonly(readOnly);
        }
    }, [readOnly, editorInstance]);

    const handleSave = React.useCallback(() => {
        if (!onSave || !editorInstance) return;
        const currentContent = editorInstance.getMarkdown();
        onSave(currentContent);
    }, [onSave, editorInstance]);

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
                            <Button appearance="primary" icon={<SaveRegular />} onClick={handleSave}>
                                Save
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
