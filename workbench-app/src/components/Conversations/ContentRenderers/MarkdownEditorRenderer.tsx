import { makeStyles } from '@fluentui/react-components';
import { Editor, defaultValueCtx, rootCtx } from '@milkdown/kit/core';
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
});

interface MilkdownEditorProps {
    content?: string;
}

const MilkdownEditor: React.FC<MilkdownEditorProps> = ({ content = '' }) => {
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
    return (
        <div className={styles.milkdownRoot}>
            <Milkdown />
        </div>
    );
};

export const MilkdownEditorWrapper: React.FC<MilkdownEditorProps> = ({ content }) => {
    const styles = useStyles();

    return (
        <div className={styles.editorContainer}>
            <MilkdownProvider>
                <MilkdownEditor content={content} />
            </MilkdownProvider>
        </div>
    );
};
