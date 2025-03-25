// Copyright (c) Microsoft. All rights reserved.

export interface ConversationFile {
    name: string;
    created: string;
    updated: string;
    size: number;
    version: number;
    contentType: string;
    metadata: {
        [key: string]: any;
    };
}
