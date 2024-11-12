// Copyright (c) Microsoft. All rights reserved.

import { PayloadAction, createSlice } from '@reduxjs/toolkit';
import { ChatCanvasState } from './ChatCanvasState';

const localStorageKey = {
    chatCanvasOpen: 'chatCanvasOpen',
    chatCanvasMode: 'chatCanvasMode',
    chatCanvasSelectedAssistantId: 'chatCanvasSelectedAssistantId',
    chatCanvasSelectedAssistantStateId: 'chatCanvasSelectedAssistantStateId',
};

const initialState: ChatCanvasState = {
    open: localStorage.getItem(localStorageKey.chatCanvasOpen) === 'true',
    mode: (localStorage.getItem(localStorageKey.chatCanvasMode) as ChatCanvasState['mode']) ?? 'conversation',
    selectedAssistantId: localStorage.getItem(localStorageKey.chatCanvasSelectedAssistantId) ?? undefined,
    selectedAssistantStateId: localStorage.getItem(localStorageKey.chatCanvasSelectedAssistantStateId) ?? undefined,
};

export const chatCanvasSlice = createSlice({
    name: 'chatCanvas',
    initialState,
    reducers: {
        setChatCanvasOpen: (state: ChatCanvasState, action: PayloadAction<boolean>) => {
            state.open = action.payload;
            persistState(state);
        },
        setChatCanvasMode: (state: ChatCanvasState, action: PayloadAction<ChatCanvasState['mode']>) => {
            state.mode = action.payload;
            persistState(state);
        },
        setChatCanvasAssistantId: (state: ChatCanvasState, action: PayloadAction<string | undefined>) => {
            state.selectedAssistantId = action.payload;
            persistState(state);
        },
        setChatCanvasAssistantStateId: (state: ChatCanvasState, action: PayloadAction<string | undefined>) => {
            state.selectedAssistantStateId = action.payload;
            persistState(state);
        },
        setChatCanvasState: (state: ChatCanvasState, action: PayloadAction<ChatCanvasState>) => {
            Object.assign(state, action.payload);
            persistState(state);
        },
    },
});

const persistState = (state: ChatCanvasState) => {
    localStorage.setItem(localStorageKey.chatCanvasOpen, state.open.toString());
    localStorage.setItem(localStorageKey.chatCanvasMode, state.mode);
    if (state.selectedAssistantId) {
        localStorage.setItem(localStorageKey.chatCanvasSelectedAssistantId, state.selectedAssistantId);
    } else {
        localStorage.removeItem(localStorageKey.chatCanvasSelectedAssistantId);
    }
    if (state.selectedAssistantStateId) {
        localStorage.setItem(localStorageKey.chatCanvasSelectedAssistantStateId, state.selectedAssistantStateId);
    } else {
        localStorage.removeItem(localStorageKey.chatCanvasSelectedAssistantStateId);
    }
};

export const {
    setChatCanvasOpen,
    setChatCanvasMode,
    setChatCanvasAssistantId,
    setChatCanvasAssistantStateId,
    setChatCanvasState,
} = chatCanvasSlice.actions;

export default chatCanvasSlice.reducer;
