// Copyright (c) Microsoft. All rights reserved.

import { generateUuid } from '@azure/ms-rest-js';
import { PayloadAction, createSlice } from '@reduxjs/toolkit';
import { Constants } from '../../../Constants';
import { AppStorage } from '../../../libs/AppStorage';
import { AppState } from './AppState';

const localStorageKey = {
    devMode: 'devMode',
    chatWidthPercent: 'chatWidthPercent',
    completedFirstRunApp: 'completedFirstRun:app',
    completedFirstRunExperimental: 'completedFirstRun:experimental',
    completedFirstRunWorkflow: 'completedFirstRun:workflow',
};

const initialState: AppState = {
    devMode: localStorage.getItem(localStorageKey.devMode) === 'true',
    errors: [],
    chatWidthPercent:
        AppStorage.getInstance().loadObject<number>(localStorageKey.chatWidthPercent) ??
        Constants.app.defaultChatWidthPercent,
    completedFirstRun: {
        app: AppStorage.getInstance().loadObject<boolean>(localStorageKey.completedFirstRunApp) ?? false,
        experimental:
            AppStorage.getInstance().loadObject<boolean>(localStorageKey.completedFirstRunExperimental) ?? false,
        workflow: AppStorage.getInstance().loadObject<boolean>(localStorageKey.completedFirstRunWorkflow) ?? false,
    },
};

export const appSlice = createSlice({
    name: 'app',
    initialState,
    reducers: {
        toggleDevMode: (state: AppState) => {
            state.devMode = !state.devMode;
            localStorage.setItem(localStorageKey.devMode, state.devMode.toString());
        },
        setIsDraggingOverBody: (state: AppState, action: PayloadAction<boolean>) => {
            state.isDraggingOverBody = action.payload;
        },
        addError: (state: AppState, action: PayloadAction<{ title?: string; message?: string }>) => {
            state.errors?.push({
                id: generateUuid(),
                title: action.payload.title,
                message: action.payload.message,
            });
        },
        removeError: (state: AppState, action: PayloadAction<string>) => {
            state.errors = state.errors?.filter((error) => error.id !== action.payload);
        },
        clearErrors: (state: AppState) => {
            state.errors = [];
        },
        setChatWidthPercent: (state: AppState, action: PayloadAction<number>) => {
            AppStorage.getInstance().saveObject(localStorageKey.chatWidthPercent, action.payload);
            state.chatWidthPercent = action.payload;
        },
        setCompletedFirstRun: (
            state: AppState,
            action: PayloadAction<{ app?: boolean; experimental?: boolean; workflow?: boolean }>,
        ) => {
            if (action.payload.app !== undefined) {
                AppStorage.getInstance().saveObject(localStorageKey.completedFirstRunApp, action.payload.app);
                if (!state.completedFirstRun) {
                    state.completedFirstRun = {};
                }
                state.completedFirstRun.app = action.payload.app;
            }
            if (action.payload.experimental !== undefined) {
                AppStorage.getInstance().saveObject(
                    localStorageKey.completedFirstRunExperimental,
                    action.payload.experimental,
                );
                if (!state.completedFirstRun) {
                    state.completedFirstRun = {};
                }
                state.completedFirstRun.experimental = action.payload.experimental;
            }
            if (action.payload.workflow !== undefined) {
                AppStorage.getInstance().saveObject(localStorageKey.completedFirstRunWorkflow, action.payload.workflow);
                if (!state.completedFirstRun) {
                    state.completedFirstRun = {};
                }
                state.completedFirstRun.workflow = action.payload.workflow;
            }
        },
        setConversationCanvasState: (
            state: AppState,
            action: PayloadAction<{
                open?: boolean | null;
                mode?: 'conversation' | 'assistant';
                assistantId?: string | null;
                assistantStateId?: string | null;
            }>,
        ) => {
            // only update the properties that are provided
            if (!state.conversationCanvasState) {
                state.conversationCanvasState = {};
            }

            if (action.payload.open !== undefined) {
                state.conversationCanvasState.open = action.payload.open ?? false;
            }

            if (action.payload.mode !== undefined) {
                state.conversationCanvasState.mode = action.payload.mode;
            }

            if (action.payload.assistantId !== undefined) {
                state.conversationCanvasState.assistantId = action.payload.assistantId ?? undefined;
            }

            if (action.payload.assistantStateId !== undefined) {
                state.conversationCanvasState.assistantStateId = action.payload.assistantStateId ?? undefined;
            }
        },
    },
});

export const {
    toggleDevMode,
    setIsDraggingOverBody,
    addError,
    removeError,
    clearErrors,
    setChatWidthPercent,
    setCompletedFirstRun,
    setConversationCanvasState,
} = appSlice.actions;

export default appSlice.reducer;
