// Copyright (c) Microsoft. All rights reserved.

import { PayloadAction, createSlice } from '@reduxjs/toolkit';
import { ChatCanvasState } from './ChatCanvasState';

const initialState: ChatCanvasState = {
    open: false,
    mode: 'conversation',
};

export const chatCanvasSlice = createSlice({
    name: 'chatCanvas',
    initialState,
    reducers: {
        setChatCanvasOpen: (state: ChatCanvasState, action: PayloadAction<boolean>) => {
            state.open = action.payload;
        },
        setChatCanvasMode: (state: ChatCanvasState, action: PayloadAction<ChatCanvasState['mode']>) => {
            state.mode = action.payload;
        },
        setChatCanvasAssistantId: (state: ChatCanvasState, action: PayloadAction<string | undefined>) => {
            state.selectedAssistantId = action.payload;
        },
        setChatCanvasAssistantStateId: (state: ChatCanvasState, action: PayloadAction<string | undefined>) => {
            state.selectedAssistantStateId = action.payload;
        },
        setChatCanvasState: (state: ChatCanvasState, action: PayloadAction<ChatCanvasState>) => {
            Object.assign(state, action.payload);
        },
    },
});

export const {
    setChatCanvasOpen,
    setChatCanvasMode,
    setChatCanvasAssistantId,
    setChatCanvasAssistantStateId,
    setChatCanvasState,
} = chatCanvasSlice.actions;

export default chatCanvasSlice.reducer;
