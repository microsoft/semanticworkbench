// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { ConversationList } from './Controls/ConversationList';

const useClasses = makeStyles({
    root: {
        flex: '1 1 auto',
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
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
    },
});

interface GlobalContentProps {
    headerBefore?: React.ReactNode;
    headerAfter?: React.ReactNode;
}

export const GlobalContent: React.FC<GlobalContentProps> = (props) => {
    const { headerBefore, headerAfter } = props;
    const classes = useClasses();

    const conversationList = React.useMemo(() => <ConversationList hideChildConversations />, []);

    return (
        <div className={classes.root}>
            <div className={classes.header}>
                {headerBefore}
                {headerAfter}
            </div>
            <div className={classes.content}>{conversationList}</div>
        </div>
    );
};
