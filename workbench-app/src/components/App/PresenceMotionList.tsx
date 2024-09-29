// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, tokens } from '@fluentui/react-components';
import { PresenceGroup, createPresenceComponent, motionTokens } from '@fluentui/react-motions-preview';
import React from 'react';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
});

const ItemMotion = createPresenceComponent({
    enter: {
        keyframes: [{ opacity: 0 }, { opacity: 1 }],

        easing: motionTokens.easingEasyEase,
        duration: motionTokens.durationUltraSlow,
    },
    exit: {
        keyframes: [{ opacity: 1 }, { opacity: 0 }],

        easing: motionTokens.easingEasyEase,
        duration: motionTokens.durationUltraSlow,
    },
});

interface PresenceMotionListProps {
    items?: React.ReactNode[];
}

export const PresenceMotionList: React.FC<PresenceMotionListProps> = (props) => {
    const { items } = props;
    const classes = useClasses();

    return (
        <div className={classes.root}>
            <PresenceGroup>
                {items?.map((item, index) => (
                    <ItemMotion key={index}>
                        <div>{item}</div>
                    </ItemMotion>
                ))}
            </PresenceGroup>
        </div>
    );
};
