// Copyright (c) Microsoft. All rights reserved.

import { useAccount, useIsAuthenticated, useMsal } from '@azure/msal-react';
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
import { setLocalUser, setUserPhoto } from '../../redux/features/app/appSlice';

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
    const account = useAccount();
    const microsoftGraph = useMicrosoftGraph();
    const { localUser, userPhoto } = useAppSelector((state) => state.app);
    const dispatch = useAppDispatch();

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

    React.useEffect(() => {
        if (!isAuthenticated || localUser || !account?.name) {
            return;
        }

        dispatch(
            setLocalUser({
                id: (account.homeAccountId || '').split('.').reverse().join('.'),
                name: account.name,
                email: account.username,
                avatar: {
                    name: account.name,
                    image: userPhoto.src ? { src: userPhoto.src } : undefined,
                },
            }),
        );
    }, [account, dispatch, isAuthenticated, localUser, userPhoto.src]);

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
