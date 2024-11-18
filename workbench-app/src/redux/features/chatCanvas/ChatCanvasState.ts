// Copyright (c) Microsoft. All rights reserved.

export interface ChatCanvasState {
    // persisted
    open: boolean;
    mode: 'conversation' | 'assistant';
    selectedAssistantId?: string;
    selectedAssistantStateId?: string;
}
