// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, shorthands, tokens } from '@fluentui/react-components';
import dayjs from 'dayjs';
import timezone from 'dayjs/plugin/timezone';
import utc from 'dayjs/plugin/utc';
import React from 'react';
import { ConversationList } from './ConversationList';

dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.tz.guess();

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
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
    // footer: {
    //     flex: '0 0 auto',
    //     display: 'flex',
    //     flexDirection: 'column',
    //     gap: tokens.spacingVerticalS,
    //     backgroundColor: tokens.colorNeutralBackground3,
    //     padding: tokens.spacingHorizontalM,
    // },
});

interface GlobalContentProps {
    headerBefore?: React.ReactNode;
    headerAfter?: React.ReactNode;
}

export const GlobalContent: React.FC<GlobalContentProps> = (props) => {
    const { headerBefore, headerAfter } = props;
    const classes = useClasses();
    return (
        <div className={classes.root}>
            <div className={classes.header}>
                {headerBefore}
                {headerAfter}
            </div>
            <div className={classes.content}>
                <ConversationList />
            </div>
            {/* <div className={classes.footer}></div> */}
        </div>
    );
};
