// Copyright (c) Microsoft. All rights reserved.

import { PayloadAction, createSlice } from '@reduxjs/toolkit';
import { LocalUserState } from './LocalUserState';

const initialState: LocalUserState = {
    avatar: {},
};

export const localUserSlice = createSlice({
    name: 'localUser',
    initialState,
    reducers: {
        setLocalUser: (state: LocalUserState, action: PayloadAction<LocalUserState>) => {
            Object.assign(state, action.payload);
        },
    },
});

export const { setLocalUser } = localUserSlice.actions;

export default localUserSlice.reducer;
