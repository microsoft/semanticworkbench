// Copyright (c) Microsoft. All rights reserved.

import { Spinner, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';

const useClasses = makeStyles({
    root: {
        ...shorthands.margin(tokens.spacingVerticalM),
    },
});

export const Loading: React.FC = () => {
    const classes = useClasses();

    return <Spinner className={classes.root} size="medium" label="Loading..." />;
};
