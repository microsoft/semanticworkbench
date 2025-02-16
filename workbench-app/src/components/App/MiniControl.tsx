// Copyright (c) Microsoft. All rights reserved.

import { Card, Label, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { Link } from 'react-router-dom';
import { TooltipWrapper } from './TooltipWrapper';

const useClasses = makeStyles({
    header: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        color: 'inherit',
        gap: tokens.spacingHorizontalS,
        ...shorthands.textDecoration('none'),
    },
    link: {
        cursor: 'pointer',
    },
    body: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: tokens.spacingVerticalM,
    },
    actions: {
        display: 'flex',
        flexDirection: 'row',
        gap: tokens.spacingHorizontalS,
    },
});

interface MiniControlProps {
    icon: JSX.Element;
    label: string;
    linkUrl: string;
    actions?: JSX.Element;
    tooltip?: string;
}

export const MiniControl: React.FC<MiniControlProps> = (props) => {
    const { icon, label, linkUrl, actions, tooltip } = props;
    const classes = useClasses();

    const link = (
        <Link className={classes.header} to={linkUrl}>
            {icon}
            <Label className={classes.link} size="large">
                {label}
            </Label>
        </Link>
    );

    return (
        <Card>
            <div className={classes.body}>
                {tooltip ? <TooltipWrapper content={tooltip}>{link}</TooltipWrapper> : link}
                <div className={classes.actions}>{actions}</div>
            </div>
        </Card>
    );
};
