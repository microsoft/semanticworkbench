// Copyright (c) Microsoft. All rights reserved.

import { Spinner, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { Constants } from '../../Constants';

const useClasses = makeStyles({
    root: {
        ...shorthands.margin(tokens.spacingVerticalM),
    },
});

export const Loading: React.FC = () => {
    const classes = useClasses();
    const [showSpinner, setShowSpinner] = React.useState(false);

    React.useEffect(() => {
        const timer = setTimeout(() => {
            setShowSpinner(true);
        }, Constants.app.loaderDelayMs);

        return () => clearTimeout(timer);
    }, []);

    return showSpinner ? <Spinner className={classes.root} size="medium" label="Loading..." /> : null;
};
