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
import { useLocalUserAccount } from '../../libs/useLocalUserAccount';
import { useMicrosoftGraph } from '../../libs/useMicrosoftGraph';
import { useAppDispatch, useAppSelector } from '../../redux/app/hooks';
import { setUser } from '../../redux/features/app/appSlice';

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
    const microsoftGraph = useMicrosoftGraph();
    const isAuthenticated = useIsAuthenticated();
    const { getUserId, getUserName } = useLocalUserAccount();
    const { user } = useAppSelector((state) => state.app);
    const dispatch = useAppDispatch();

    const account = instance.getActiveAccount();
    const userId = getUserId();
    const userName = getUserName();

    React.useEffect(() => {
        if (isAuthenticated && userId && userName && !user?.image) {
            (async () => {
                const photo = await microsoftGraph.getMyPhotoAsync();
                dispatch(
                    setUser({
                        id: userId,
                        name: userName,
                        image: photo,
                    }),
                );
            })();
        }
    }, [isAuthenticated, microsoftGraph, userId, userName, user?.image, dispatch]);

    const avatar = user?.image
        ? {
              name: userName,
              image: { src: user.image },
          }
        : { name: userName };

    const handleSignOut = () => {
        void AuthHelper.logoutAsync(instance);
    };

    const handleSignIn = () => {
        void AuthHelper.loginAsync(instance);
    };

    return (
        <Popover positioning="below-end">
            <PopoverTrigger>
                <Persona className="user-avatar" avatar={avatar} presence={{ status: 'available' }} />
            </PopoverTrigger>
            <PopoverSurface>
                <div className={classes.popoverSurface}>
                    {account && (
                        <>
                            <div className={classes.accountInfo}>
                                <Label>{account.name}</Label>
                                <Label size="small">{account.username}</Label>
                            </div>
                            <Link onClick={handleSignOut}>Sign Out</Link>
                        </>
                    )}
                    {!account && <Link onClick={handleSignIn}>Sign In</Link>}
                </div>
            </PopoverSurface>
        </Popover>
    );
};
