// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, tokens } from '@fluentui/react-components';
import { DiffFile, generateDiffFile } from '@git-diff-view/file';
import { DiffModeEnum, DiffView } from '@git-diff-view/react';
import '@git-diff-view/react/styles/diff-view.css';
import React from 'react';

const useClasses = makeStyles({
    root: {
        position: 'relative',
    },
    copy: {
        position: 'absolute',
        right: tokens.spacingHorizontalXS,
        top: tokens.spacingVerticalXS,
    },
});

export interface DiffItem {
    content: string;
    label?: string;
    language?: string;
}

interface DiffRendererProps {
    source: DiffItem;
    compare: DiffItem;
    splitView?: boolean;
    wrapLines?: boolean;
}

export const DiffRenderer: React.FC<DiffRendererProps> = (props) => {
    const { source, compare, splitView, wrapLines } = props;
    const classes = useClasses();

    const diffFile = React.useMemo(() => {
        if (source.content === compare.content) {
            return undefined;
        }

        const file = generateDiffFile(
            source.label || 'Source',
            source.content,
            compare.label || 'Compare',
            compare.content,
        );

        file.init();
        if (splitView) {
            file.buildSplitDiffLines();
        } else {
            file.buildUnifiedDiffLines();
        }

        const bundle = file.getBundle();
        const mergeFile = DiffFile.createInstance(
            {
                oldFile: {
                    fileName: source.label,
                    content: source.content,
                    fileLang: source.language,
                },
                newFile: {
                    fileName: compare.label,
                    content: compare.content,
                    fileLang: compare.language,
                },
            },
            bundle,
        );

        return mergeFile;
    }, [source.label, source.content, source.language, compare.label, compare.content, compare.language, splitView]);

    return (
        <div className={classes.root}>
            <DiffView
                diffFile={diffFile}
                diffViewMode={splitView ? DiffModeEnum.Split : DiffModeEnum.Unified}
                diffViewWrap={wrapLines}
            />
        </div>
    );
};
