// Copyright (c) Microsoft. All rights reserved.

import { PayloadAction, createSlice } from '@reduxjs/toolkit';
import { AppStorage } from '../../../libs/AppStorage';
import { ChatCanvasState } from './ChatCanvasState';

const localStorageKey = {
    chatCanvasOpen: 'chat-canvas.open',
    chatCanvasMode: 'chat-canvas.mode',
    chatCanvasSelectedAssistantId: 'chat-canvas.selected-assistant-id',
    chatCanvasSelectedAssistantStateId: 'chat-canvas.selected-assistant-state-id',
};

const initialState: ChatCanvasState = {
    open: localStorage.getItem(localStorageKey.chatCanvasOpen) === 'true',
    mode: localStorage.getItem(localStorageKey.chatCanvasMode) === 'assistant' ? 'assistant' : 'conversation',
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
    AppStorage.getInstance().saveObject(localStorageKey.chatCanvasOpen, state.open);
    AppStorage.getInstance().saveObject(localStorageKey.chatCanvasMode, state.mode);
    AppStorage.getInstance().saveObject(localStorageKey.chatCanvasSelectedAssistantId, state.selectedAssistantId);
    AppStorage.getInstance().saveObject(
        localStorageKey.chatCanvasSelectedAssistantStateId,
        state.selectedAssistantStateId,
    );
};

export const {
    setChatCanvasOpen,
    setChatCanvasMode,
    setChatCanvasAssistantId,
    setChatCanvasAssistantStateId,
    setChatCanvasState,
} = chatCanvasSlice.actions;

export default chatCanvasSlice.reducer;
