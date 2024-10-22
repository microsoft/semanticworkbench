// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, shorthands, Title3, tokens } from '@fluentui/react-components';
import React from 'react';
import { useAppSelector } from '../../redux/app/hooks';
import { Chat } from './Chat/Chat';

const useClasses = makeStyles({
    root: {
        flex: '1 1 auto',
        display: 'flex',
        flexDirection: 'column',
    },
    header: {
        flex: '0 0 auto',
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
    },
    content: {
        flex: '1 1 auto',
        overflow: 'auto',
        padding: tokens.spacingHorizontalM,
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
});

interface MainContentProps {
    headerBefore?: React.ReactNode;
    headerAfter?: React.ReactNode;
}

export const MainContent: React.FC<MainContentProps> = (props) => {
    const { headerBefore, headerAfter } = props;
    const { activeConversationId } = useAppSelector((state) => state.app);
    const classes = useClasses();

    if (activeConversationId) {
        return <Chat conversationId={activeConversationId} headerBefore={headerBefore} headerAfter={headerAfter} />;
    }

    return (
        <div className={classes.root}>
            {activeConversationId ? (
                <Chat conversationId={activeConversationId} headerBefore={headerBefore} headerAfter={headerAfter} />
            ) : (
                <>
                    <div className={classes.header}>
                        {headerBefore}
                        {headerAfter}
                    </div>
                    <div className={classes.content}>
                        <Title3>Select or create a new conversation</Title3>
                    </div>
                </>
            )}
        </div>
    );
};
