// Copyright (c) Microsoft. All rights reserved.

import { Card, Text, Title3, makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { PresenceMotionList } from '../App/PresenceMotionList';

const useClasses = makeStyles({
    root: {
        backgroundImage: `linear-gradient(to right, ${tokens.colorNeutralBackground1}, ${tokens.colorBrandBackground2})`,
    },
    actions: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: tokens.spacingVerticalS,
    },
});

interface MyItemsManagerProps {
    items?: JSX.Element[];
    title: string;
    itemLabel: string;
    hideInstruction?: boolean;
    actions: JSX.Element;
}

export const MyItemsManager: React.FC<MyItemsManagerProps> = (props) => {
    const { items, title, itemLabel, hideInstruction, actions } = props;
    const classes = useClasses();

    return (
        <Card className={classes.root}>
            <Text size={400} weight="semibold">
                {title}
            </Text>
            <div className={classes.actions}>{actions}</div>
            {items?.length === 0 && !hideInstruction && (
                <>
                    <Title3>No {itemLabel.toLowerCase()}s found.</Title3>
                    <Text>
                        Create a new {itemLabel.toLowerCase()} by clicking the <strong>New {itemLabel}</strong> button
                        above.
                    </Text>
                </>
            )}
            <PresenceMotionList items={items} />
        </Card>
    );
};
