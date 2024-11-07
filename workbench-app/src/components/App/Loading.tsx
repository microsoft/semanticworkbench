// Copyright (c) Microsoft. All rights reserved.

import { Spinner, makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { Constants } from '../../Constants';

const useClasses = makeStyles({
    root: {
        ...shorthands.margin(tokens.spacingVerticalM),
    },
});

interface LoadingProps {
    className?: string;
}

export const Loading: React.FC<LoadingProps> = (props) => {
    const { className } = props;
    const classes = useClasses();
    const [showSpinner, setShowSpinner] = React.useState(false);

    React.useEffect(() => {
        const timer = setTimeout(() => {
            setShowSpinner(true);
        }, Constants.app.loaderDelayMs);

        return () => clearTimeout(timer);
    }, []);

    return showSpinner ? (
        <Spinner className={mergeClasses(classes.root, className)} size="medium" label="Loading..." />
    ) : null;
};
