// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    MessageBar,
    MessageBarActions,
    MessageBarBody,
    MessageBarGroup,
    MessageBarTitle,
    makeStyles,
    mergeClasses,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import { DismissRegular } from '@fluentui/react-icons';
import React from 'react';
import { useAppDispatch, useAppSelector } from '../../redux/app/hooks';
import { RootState } from '../../redux/app/store';
import { removeError } from '../../redux/features/app/appSlice';

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

interface ErrorListProps {
    className?: string;
}

export const ErrorList: React.FC<ErrorListProps> = (props) => {
    const { className } = props;
    const classes = useClasses();
    const { errors } = useAppSelector((state: RootState) => state.app);
    const dispatch = useAppDispatch();

    if (!errors || errors.length === 0) {
        return null;
    }

    return (
        <MessageBarGroup className={mergeClasses(classes.root, className)}>
            {errors.map((error) => (
                <MessageBar key={error.id} intent="error" layout="multiline">
                    <MessageBarBody>
                        <MessageBarTitle>{error.title ?? 'Error'}:</MessageBarTitle>
                        {error.message}
                    </MessageBarBody>
                    <MessageBarActions
                        containerAction={
                            <Button
                                appearance="transparent"
                                icon={<DismissRegular />}
                                onClick={() => dispatch(removeError(error.id))}
                            />
                        }
                    />
                </MessageBar>
            ))}
        </MessageBarGroup>
    );
};