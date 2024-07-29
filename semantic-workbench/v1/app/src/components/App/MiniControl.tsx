// Copyright (c) Microsoft. All rights reserved.

import { Card, Label, Tooltip, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { Link } from 'react-router-dom';

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
}

export const MiniControl: React.FC<MiniControlProps> = (props) => {
    const { icon, label, linkUrl, actions } = props;
    const classes = useClasses();

    return (
        <Card>
            <div className={classes.body}>
                <Link className={classes.header} to={linkUrl}>
                    <Tooltip content="Workflow" relationship="label">
                        {icon}
                    </Tooltip>
                    <Label className={classes.link} size="large">
                        {label}
                    </Label>
                </Link>
                <div className={classes.actions}>{actions}</div>
            </div>
        </Card>
    );
};
