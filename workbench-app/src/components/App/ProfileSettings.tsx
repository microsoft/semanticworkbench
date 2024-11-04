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
import { setLocalUser } from '../../redux/features/localUser/localUserSlice';

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
    const localUserState = useAppSelector((state) => state.localUser);
    const dispatch = useAppDispatch();

    React.useEffect(() => {
        (async () => {
            if (!isAuthenticated || !account?.name || localUserState.id) {
                return;
            }

            const photo = await microsoftGraph.getMyPhotoAsync();

            dispatch(
                setLocalUser({
                    id: (account.homeAccountId || '').split('.').reverse().join('.'),
                    name: account.name,
                    email: account.username,
                    avatar: {
                        name: account.name,
                        image: photo ? { src: photo } : undefined,
                    },
                }),
            );
        })();
    }, [account, dispatch, isAuthenticated, localUserState.id, microsoftGraph]);

    const handleSignOut = () => {
        void AuthHelper.logoutAsync(instance);
    };

    const handleSignIn = () => {
        void AuthHelper.loginAsync(instance);
    };

    return (
        <Popover positioning="below-end">
            <PopoverTrigger>
                <Persona className="user-avatar" avatar={localUserState.avatar} presence={{ status: 'available' }} />
            </PopoverTrigger>
            <PopoverSurface>
                <div className={classes.popoverSurface}>
                    {isAuthenticated ? (
                        <>
                            <div className={classes.accountInfo}>
                                <Label>{localUserState.name}</Label>
                                <Label size="small">{localUserState.email}</Label>
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
