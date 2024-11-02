// Copyright (c) Microsoft. All rights reserved.
import { useAccount, useIsAuthenticated } from '@azure/msal-react';
import React from 'react';
import { useAppDispatch, useAppSelector } from '../redux/app/hooks';
import { setUserPhoto } from '../redux/features/app/appSlice';
import { useMicrosoftGraph } from './useMicrosoftGraph';

export const useLocalUser = () => {
    const account = useAccount();
    const { userPhoto } = useAppSelector((state) => state.app);
    const microsoftGraph = useMicrosoftGraph();
    const isAuthenticated = useIsAuthenticated();
    const dispatch = useAppDispatch();

    // update the app state to indicate that the user photo is being loaded
    // so that we don't try to load it multiple times
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

    const getUserId = React.useCallback(() => {
        // AAD accountID is <objectId>.<tenantId>, while the participantId is <tenantId>.<objectId>
        const userId = (account?.homeAccountId || '').split('.').reverse().join('.');

        if (!userId) {
            throw new Error('User ID is not available.');
        }

        return userId;
    }, [account]);

    const localUser = React.useMemo(
        () => ({
            id: getUserId(),
            name: account?.name,
            email: account?.username,
            avatar: {
                name: account?.name,
                image: userPhoto.src ? { src: userPhoto.src } : undefined,
            },
        }),
        [account?.name, account?.username, getUserId, userPhoto.src],
    );

    return localUser;
};
