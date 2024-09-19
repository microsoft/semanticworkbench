// Copyright (c) Microsoft. All rights reserved.

import { Button, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import { BookInformation24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Conversation } from '../../../models/Conversation';
import { ConversationFile } from '../../../models/ConversationFile';
import { useAppDispatch } from '../../../redux/app/hooks';
import { setInspector } from '../../../redux/features/app/appSlice';
import { ConversationFileList } from './ConversationFileList';
import { ConversationFileViewer } from './ConversationFileViewer';

const useClasses = makeStyles({
    noFiles: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        ...shorthands.padding(tokens.spacingVerticalS),
    },
    headerContent: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: tokens.spacingHorizontalM,
        ...shorthands.padding(tokens.spacingVerticalS),
    },
});

interface ConversationFilesProps {
    conversation: Conversation;
    conversationFiles: ConversationFile[];
}

export const ConversationFiles: React.FC<ConversationFilesProps> = (props) => {
    const { conversation, conversationFiles } = props;
    const classes = useClasses();
    const dispatch = useAppDispatch();
    const [selectedConversationFile, setSelectedConversationFile] = React.useState<ConversationFile | null>(null);

    return (
        <>
            {conversationFiles.length > 0 && (
                <div className={classes.noFiles}>
                    No conversation files found.
                    <Button
                        appearance="secondary"
                        onClick={() => dispatch(setInspector({ open: false }))}
                        icon={<BookInformation24Regular />}
                    />
                </div>
            )}
            {(conversationFiles.length === 1 || selectedConversationFile) && (
                <ConversationFileViewer
                    conversation={conversation}
                    conversationFile={selectedConversationFile ?? conversationFiles[0]}
                />
            )}
            {conversationFiles.length > 1 && (
                <ConversationFileList
                    conversationFiles={conversationFiles}
                    onFileSelect={setSelectedConversationFile}
                />
            )}
        </>
    );
};
