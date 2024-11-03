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
