// Copyright (c) Microsoft. All rights reserved.

import { PayloadAction, createSlice } from '@reduxjs/toolkit';
import { AppStorage } from '../../../libs/AppStorage';
import { LocalUserState } from './LocalUserState';

const storageKeys = {
    id: 'local-user.id',
    name: 'local-user.name',
    email: 'local-user.email',
    avatarName: 'local-user.avatar.name',
    avatarImage: 'local-user.avatar.image',
};

const initialState: LocalUserState = {
    id: AppStorage.getInstance().loadObject<string>(storageKeys.id),
    name: AppStorage.getInstance().loadObject<string>(storageKeys.name),
    email: AppStorage.getInstance().loadObject<string>(storageKeys.email),
    avatar: {
        name: AppStorage.getInstance().loadObject<string>(storageKeys.avatarName),
        image: AppStorage.getInstance().loadObject<{
            src: string;
        }>(storageKeys.avatarImage),
    },
};

export const localUserSlice = createSlice({
    name: 'localUser',
    initialState,
    reducers: {
        setLocalUser: (state: LocalUserState, action: PayloadAction<LocalUserState>) => {
            Object.assign(state, action.payload);
            AppStorage.getInstance().saveObject(storageKeys.id, state.id);
            AppStorage.getInstance().saveObject(storageKeys.name, state.name);
            AppStorage.getInstance().saveObject(storageKeys.email, state.email);
            AppStorage.getInstance().saveObject(storageKeys.avatarName, state.avatar.name);
            AppStorage.getInstance().saveObject(storageKeys.avatarImage, state.avatar.image);
        },
    },
});

export const { setLocalUser } = localUserSlice.actions;

export default localUserSlice.reducer;
