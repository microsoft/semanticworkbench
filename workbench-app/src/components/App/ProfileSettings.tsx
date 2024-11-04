// Copyright (c) Microsoft. All rights reserved.

import { useIsAuthenticated, useMsal } from '@azure/msal-react';
import {
    Label,
    Link,
    Persona,
    Popover,
    PopoverSurface,
    PopoverTrigger,
    makeStyles,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { AuthHelper } from '../../libs/AuthHelper';
import { useMicrosoftGraph } from '../../libs/useMicrosoftGraph';
import { useAppDispatch, useAppSelector } from '../../redux/app/hooks';
import { setUserPhoto } from '../../redux/features/app/appSlice';

const useClasses = makeStyles({
    popoverSurface: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingHorizontalM,
    },
    accountInfo: {
        display: 'flex',
        flexDirection: 'column',
    },
});

export const ProfileSettings: React.FC = () => {
    const classes = useClasses();
    const { instance } = useMsal();
    const isAuthenticated = useIsAuthenticated();
    const microsoftGraph = useMicrosoftGraph();
    const { localUser, userPhoto } = useAppSelector((state) => state.app);
    const dispatch = useAppDispatch();

    // FIXME: prevent multiple calls before the setUserPhoto is updated
    // If not wrapped in a useEffect, an error is thrown when the state is updated
    // while other components are still rendering. Putting in a useEffect
    // prevents the error from being thrown, but then the photo may get fetched
    // multiple times when multiple components are rendering at the same time
    // and the state update has not yet been processed. Not the end of the world,
    // as it tends to be just a few calls, but it's not ideal.
    React.useEffect(() => {
        if (isAuthenticated && !userPhoto.src && !userPhoto.isLoading) {
            dispatch(setUserPhoto({ isLoading: true, src: undefined }));
            (async () => {
                const photo = await microsoftGraph.getMyPhotoAsync();
                dispatch(
                    setUserPhoto({
                        isLoading: false,
                        src: photo,
                    }),
                );
            })();
        }
    }, [dispatch, isAuthenticated, microsoftGraph, userPhoto.isLoading, userPhoto.src]);

    const handleSignOut = () => {
        void AuthHelper.logoutAsync(instance);
    };

    const handleSignIn = () => {
        void AuthHelper.loginAsync(instance);
    };

    return (
        <Popover positioning="below-end">
            <PopoverTrigger>
                <Persona className="user-avatar" avatar={localUser?.avatar} presence={{ status: 'available' }} />
            </PopoverTrigger>
            <PopoverSurface>
                <div className={classes.popoverSurface}>
                    {isAuthenticated && localUser ? (
                        <>
                            <div className={classes.accountInfo}>
                                <Label>{localUser.name}</Label>
                                <Label size="small">{localUser.email}</Label>
                            </div>
                            <Link onClick={handleSignOut}>Sign Out</Link>
                        </>
                    ) : (
                        <Link onClick={handleSignIn}>Sign In</Link>
                    )}
                </div>
            </PopoverSurface>
        </Popover>
    );
};
