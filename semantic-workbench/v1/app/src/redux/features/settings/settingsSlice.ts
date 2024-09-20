// Copyright (c) Microsoft. All rights reserved.

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Constants } from '../../../Constants';
import { AppStorage } from '../../../libs/AppStorage';
import { SettingsState } from './SettingsState';

const storageKeys = {
    theme: 'theme',
    environmentId: 'environment-id',
    speechKey: 'speech-key',
    speechRegion: 'speech-region',
};

const initialState: SettingsState = {
    theme: AppStorage.getInstance().loadObject<string>(storageKeys.theme) ?? Constants.app.defaultTheme,
    environmentId:
        AppStorage.getInstance().loadObject<string>(storageKeys.environmentId) ??
        Constants.service.defaultEnvironmentId,
    speechKey: AppStorage.getInstance().loadObject<string>(storageKeys.speechKey),
    speechRegion: AppStorage.getInstance().loadObject<string>(storageKeys.speechRegion),
};

export const settingsSlice = createSlice({
    name: 'settings',
    initialState,
    reducers: {
        setTheme: (state: SettingsState, action: PayloadAction<string>) => {
            AppStorage.getInstance().saveObject(storageKeys.theme, action.payload);
            state.theme = action.payload;
        },
        setEnvironmentId: (state: SettingsState, action: PayloadAction<string>) => {
            const needsReload = state.environmentId !== action.payload;
            if (action.payload === Constants.service.defaultEnvironmentId) {
                AppStorage.getInstance().saveObject(storageKeys.environmentId, undefined);
            } else {
                AppStorage.getInstance().saveObject(storageKeys.environmentId, action.payload);
            }
            state.environmentId = action.payload;
            if (needsReload) {
                window.location.reload();
            }
        },
        setSpeechKey: (state: SettingsState, action: PayloadAction<string>) => {
            AppStorage.getInstance().saveObject(storageKeys.speechKey, action.payload);
            state.speechKey = action.payload;
        },
        setSpeechRegion: (state: SettingsState, action: PayloadAction<string>) => {
            AppStorage.getInstance().saveObject(storageKeys.speechRegion, action.payload);
            state.speechRegion = action.payload;
        },
    },
});

export const { setTheme, setEnvironmentId, setSpeechKey, setSpeechRegion } = settingsSlice.actions;

export default settingsSlice.reducer;
