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
    const [profileImage, setProfileImage] = React.useState<string>();

    React.useEffect(() => {
        if (isAuthenticated && !profileImage) {
            void (async () => {
                const photo = await microsoftGraph.getMyPhotoAsync();
                setProfileImage(photo);
            })();
        }
    }, [isAuthenticated, profileImage, microsoftGraph]);

    const account = instance.getActiveAccount();
    const avatar = profileImage ? { image: { src: profileImage } } : undefined;

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
