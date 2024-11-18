// Copyright (c) Microsoft. All rights reserved.

import { Button, Title3, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import { ArrowLeft24Regular, Home24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Link } from 'react-router-dom';
import { AppMenu } from './AppMenu';
import { ErrorListFromAppState } from './ErrorListFromAppState';
import { ProfileSettings } from './ProfileSettings';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: tokens.colorNeutralBackground1,
    },
    content: {
        display: 'flex',
        flexDirection: 'row',
        backgroundColor: tokens.colorBrandBackground,
        alignItems: 'center',
        justifyContent: 'space-between',
        ...shorthands.padding(tokens.spacingVerticalS),
    },
    title: {
        color: tokens.colorNeutralForegroundOnBrand,
    },
    actions: {
        display: 'flex',
        flexDirection: 'row',
        gap: tokens.spacingHorizontalS,
    },
});

interface AppHeaderProps {
    title: string | React.ReactNode;
    actions?: {
        items: React.ReactNode[];
        replaceExisting?: boolean;
        hideProfileSettings?: boolean;
    };
}

export const AppHeader: React.FC<AppHeaderProps> = (props) => {
    const { title, actions } = props;
    const classes = useClasses();

    const actionItems = [];

    // Custom actions from the caller
    if (actions && actions?.items.length > 0) {
        actionItems.push(...actions.items.map((item, index) => <React.Fragment key={index}>{item}</React.Fragment>));
    }

    // Default navigation and other global actions
    if (!actions?.replaceExisting) {
        // Back button
        if (window.history.length > 1) {
            actionItems.push(<Button key="back" icon={<ArrowLeft24Regular />} onClick={() => window.history.back()} />);
        }

        // Home button
        if (window.location.pathname !== '/') {
            actionItems.push(
                <Link key="home" to="/">
                    <Button icon={<Home24Regular />} />
                </Link>,
            );
        }

        // Global menu
        actionItems.push(<AppMenu key="menu" />);
    }

    // Display current user's profile settings
    if (!actions?.hideProfileSettings) {
        actionItems.push(<ProfileSettings key="profile" />);
    }

    return (
        <div className={classes.root}>
            <div className={classes.content}>
                {title && typeof title === 'string' ? <Title3 className={classes.title}>{title}</Title3> : title}
                <div className={classes.actions}>{actionItems}</div>
            </div>
            <ErrorListFromAppState />
        </div>
    );
};
