import { Button, makeStyles, Text } from '@fluentui/react-components';
import { SaveRegular } from '@fluentui/react-icons';
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
        alignItems: 'left',
    },
});

interface MilkdownEditorProps {
    content?: string;
    onSave?: (content: string) => void;
    filename?: string;
}

const MilkdownEditor: React.FC<MilkdownEditorProps> = ({ content = '', onSave, filename }) => {
    const styles = useStyles();
    const { get } = useEditor((root) =>
        Editor.make()
            .config(nord)
            .config((ctx) => {
                ctx.set(rootCtx, root);
                ctx.set(defaultValueCtx, content);
            })
            .use(commonmark),
    );

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
            {(onSave || filename) && (
                <div className={styles.toolbar}>
                    {filename && (
                        <div className={styles.filenameContainer}>
                            {/* File name */}
                            <Text
                                as="h1"
                                weight="bold"
                                style={{
                                    margin: '0',
                                    fontSize: '2rem',
                                }}
                            >
                                {/* Remove file extension from filename */}
                                {filename ? filename.replace(/\.[^/.]+$/, '') : ''}
                            </Text>
                        </div>
                    )}
                    {onSave && (
                        <Button appearance="primary" icon={<SaveRegular />} onClick={handleSave}>
                            Save
                        </Button>
                    )}
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
}

export const MilkdownEditorWrapper: React.FC<MilkdownEditorWrapperProps> = ({ content, onSubmit, filename }) => {
    const styles = useStyles();
    const [isSubmitting, setIsSubmitting] = React.useState(false);

    const handleSave = React.useCallback(
        async (updatedContent: string) => {
            if (!onSubmit || isSubmitting) return;

            setIsSubmitting(true);
            try {
                await onSubmit(updatedContent);
            } finally {
                setIsSubmitting(false);
            }
        },
        [onSubmit, isSubmitting],
    );

    return (
        <div className={styles.editorContainer}>
            <MilkdownProvider>
                <MilkdownEditor content={content} onSave={onSubmit ? handleSave : undefined} filename={filename} />
            </MilkdownProvider>
        </div>
    );
};
