// Copyright (c) Microsoft. All rights reserved.

import { Button, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import { BookInformation24Regular } from '@fluentui/react-icons';
import React from 'react';
import { ConversationFile } from '../../../models/ConversationFile';
import { useAppDispatch } from '../../../redux/app/hooks';
import { setInspector } from '../../../redux/features/app/appSlice';

const useClasses = makeStyles({
    root: {
        display: 'grid',
        gridTemplateColumns: '1fr',
        gridTemplateRows: 'auto 1fr',
        height: '100%',
    },
    header: {
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        backgroundImage: `linear-gradient(to right, ${tokens.colorNeutralBackground1}, ${tokens.colorBrandBackground2})`,
    },
    headerContent: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: tokens.spacingHorizontalM,
        ...shorthands.padding(tokens.spacingVerticalS),
        ...shorthands.borderBottom(tokens.strokeWidthThin, 'solid', tokens.colorNeutralStroke1),
    },
    body: {
        overflowY: 'auto',
        height: '100%',
        maxHeight: '100%',
    },
});

interface ConversationFileListProps {
    conversationFiles: ConversationFile[];
    hideCloseButton?: boolean;
    onFileSelect?: (file: ConversationFile) => void;
}

export const ConversationFileList: React.FC<ConversationFileListProps> = (props) => {
    const { conversationFiles, hideCloseButton, onFileSelect } = props;
    const classes = useClasses();
    const dispatch = useAppDispatch();

    return (
        <div className={classes.root}>
            <div className={classes.header}>
                <div className={classes.headerContent}>
                    {!hideCloseButton && (
                        <Button
                            appearance="secondary"
                            icon={<BookInformation24Regular />}
                            onClick={() => {
                                dispatch(setInspector({ open: false }));
                            }}
                        />
                    )}
                </div>
            </div>
            <div className={classes.body}>
                {conversationFiles.map((file) => (
                    <div key={file.name} onClick={() => onFileSelect && onFileSelect(file)}>
                        {file.name}
                    </div>
                ))}
            </div>
        </div>
    );
};
