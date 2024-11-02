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
import { useLocalUser } from '../../libs/useLocalUser';

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
    const localUser = useLocalUser();
    const { instance } = useMsal();
    const isAuthenticated = useIsAuthenticated();

    const handleSignOut = () => {
        void AuthHelper.logoutAsync(instance);
    };

    const handleSignIn = () => {
        void AuthHelper.loginAsync(instance);
    };

    return (
        <Popover positioning="below-end">
            <PopoverTrigger>
                <Persona className="user-avatar" avatar={localUser.avatar} presence={{ status: 'available' }} />
            </PopoverTrigger>
            <PopoverSurface>
                <div className={classes.popoverSurface}>
                    {isAuthenticated ? (
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
