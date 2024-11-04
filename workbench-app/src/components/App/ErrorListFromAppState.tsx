// Copyright (c) Microsoft. All rights reserved.

import { MessageBarGroup, makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { useAppDispatch, useAppSelector } from '../../redux/app/hooks';
import { RootState } from '../../redux/app/store';
import { removeError } from '../../redux/features/app/appSlice';
import { ErrorMessageBar } from './ErrorMessageBar';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: tokens.colorPaletteRedBackground2,
        gap: tokens.spacingVerticalM,
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
    },
});

interface ErrorListFromAppStateProps {
    className?: string;
}

export const ErrorListFromAppState: React.FC<ErrorListFromAppStateProps> = (props) => {
    const { className } = props;
    const classes = useClasses();
    const errors = useAppSelector((state: RootState) => state.app.errors);
    const dispatch = useAppDispatch();

    if (!errors || errors.length === 0) {
        return null;
    }

    return (
        <MessageBarGroup className={mergeClasses(classes.root, className)}>
            {errors.map((error) => (
                <ErrorMessageBar
                    key={error.id}
                    title={error.title}
                    error={error.message}
                    onDismiss={() => dispatch(removeError(error.id))}
                />
            ))}
        </MessageBarGroup>
    );
};
