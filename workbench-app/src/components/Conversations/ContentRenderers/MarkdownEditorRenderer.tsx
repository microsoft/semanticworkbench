import { Button, makeStyles, Text } from '@fluentui/react-components';
import { LockClosedRegular, LockOpenRegular, SaveRegular } from '@fluentui/react-icons';
import { Crepe } from '@milkdown/crepe';
import '@milkdown/crepe/theme/common/style.css';
import '@milkdown/crepe/theme/frame.css';
import React from 'react';

const useStyles = makeStyles({
    editorContainer: {
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        height: '100%',
        flex: 1,
    },
    crepeEditorRoot: {
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
        '& .ProseMirror': {
            margin: '10px 0 0 0',
            padding: '14px 20px 20px 80px',
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

interface CrepeEditorProps {
    content?: string;
    onSave?: (content: string) => void;
    filename?: string;
    readOnly?: boolean;
    onToggleReadOnly?: () => void;
    isBackendReadOnly?: boolean;
}

const CrepeEditor: React.FC<CrepeEditorProps> = ({
    content = '',
    onSave,
    filename,
    readOnly = false,
    onToggleReadOnly,
    isBackendReadOnly = false,
}) => {
    const styles = useStyles();
    const editorRef = React.useRef<HTMLDivElement>(null);
    const crepeRef = React.useRef<Crepe | null>(null);

    React.useEffect(() => {
        if (!editorRef.current) return;

        const crepe = new Crepe({
            root: editorRef.current,
            defaultValue: content,
        });
        crepeRef.current = crepe;
        crepe.create().then(() => {
            if (crepeRef.current) {
                crepeRef.current.setReadonly(readOnly);
            }
        });
        return () => {
            if (crepeRef.current) {
                crepeRef.current.destroy();
                crepeRef.current = null;
            }
        };
    }, [content, readOnly]);

    // Update readonly state when it changes
    React.useEffect(() => {
        if (crepeRef.current) {
            crepeRef.current.setReadonly(readOnly);
        }
    }, [readOnly]);

    const handleSave = React.useCallback(() => {
        if (!onSave || !crepeRef.current) return;
        const currentContent = crepeRef.current.getMarkdown();
        onSave(currentContent);
    }, [onSave]);

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
            <div className={styles.crepeEditorRoot} ref={editorRef} />
        </>
    );
};

export interface MilkdownEditorWrapperProps extends CrepeEditorProps {
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
            <CrepeEditor
                content={content}
                onSave={onSubmit && !isReadOnly ? handleSave : undefined}
                filename={filename}
                readOnly={isReadOnly}
                onToggleReadOnly={toggleReadOnly}
                isBackendReadOnly={isBackendReadOnly}
            />
        </div>
    );
};
