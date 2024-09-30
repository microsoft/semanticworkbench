// Copyright (c) Microsoft. All rights reserved.

import { Caption1, Link, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'row',
        backgroundColor: tokens.colorNeutralBackgroundAlpha,
        alignItems: 'center',
        justifyContent: 'center',
        gap: tokens.spacingVerticalM,
        ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
    },
});

export const AppFooter: React.FC = () => {
    const classes = useClasses();

    return (
        <div className={classes.root}>
            <Link href="https://go.microsoft.com/fwlink/?LinkId=521839" target="_blank">
                Privacy &amp; Cookies
            </Link>{' '}
            |{' '}
            <Link href="https://go.microsoft.com/fwlink/?linkid=2259814" target="_blank">
                Consumer Health Privacy
            </Link>{' '}
            |{' '}
            <Link href="https://go.microsoft.com/fwlink/?LinkID=246338" target="_blank">
                Terms of Use
            </Link>{' '}
            |{' '}
            <Link
                href="https://www.microsoft.com/en-us/legal/intellectualproperty/Trademarks/EN-US.aspx"
                target="_blank"
            >
                Trademarks
            </Link>{' '}
            |{' '}
            <Link
                href="https://github.com/microsoft/semanticworkbench"
                target="_blank"
            >
                @GitHub
            </Link>{' '}
            | <Caption1>© Microsoft 2024</Caption1>
        </div>
    );
};
