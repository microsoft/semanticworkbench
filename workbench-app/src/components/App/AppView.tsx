// Copyright (c) Microsoft. All rights reserved.
import { makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Constants } from '../../Constants';
import { useAppSelector } from '../../redux/app/hooks';
import { AppFooter } from './AppFooter';
import { AppHeader } from './AppHeader';

const useClasses = makeStyles({
    documentBody: {
        backgroundImage: `url('/assets/background-1.jpg')`,
    },
    root: {
        display: 'grid',
        gridTemplateRows: 'auto 1fr auto',
        height: '100vh',
    },
    content: {
        overflowY: 'auto',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        maxWidth: `${Constants.app.maxContentWidth}px`,
        boxSizing: 'border-box',
        width: '100%',
        gap: tokens.spacingVerticalM,
        ...shorthands.margin('0', 'auto'),
        ...shorthands.padding(tokens.spacingVerticalM),
    },
    fullSize: {
        ...shorthands.padding(0),
        maxWidth: '100%',
    },
});

interface AppViewProps {
    title: string | React.ReactNode;
    actions?: {
        items: React.ReactNode[];
        replaceExisting?: boolean;
        hideProfileSettings?: boolean;
    };
    fullSizeContent?: boolean;
    children?: React.ReactNode;
}

export const AppView: React.FC<AppViewProps> = (props) => {
    const { title, actions, fullSizeContent, children } = props;
    const classes = useClasses();
    const { completedFirstRun } = useAppSelector((state) => state.app);
    const navigate = useNavigate();

    React.useLayoutEffect(() => {
        document.body.className = classes.documentBody;
        return () => {
            document.body.className = '';
        };
    }, [classes.documentBody]);

    React.useEffect(() => {
        if (!completedFirstRun?.app && window.location.pathname !== '/terms') {
            navigate('/terms');
        }
    }, [completedFirstRun, navigate]);

    return (
        <div id="app" className={classes.root}>
            <AppHeader title={title} actions={actions} />
            <div className={fullSizeContent ? mergeClasses(classes.content, classes.fullSize) : classes.content}>
                {children}
            </div>
            <AppFooter />
        </div>
    );
};
