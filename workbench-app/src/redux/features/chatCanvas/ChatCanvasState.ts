// Copyright (c) Microsoft. All rights reserved.

export interface ChatCanvasState {
    open: boolean;
    mode: 'conversation' | 'assistant';
    selectedAssistantId?: string;
    selectedAssistantStateId?: string;
}
