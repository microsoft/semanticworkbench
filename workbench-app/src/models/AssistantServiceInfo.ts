// Copyright (c) Microsoft. All rights reserved.

import { Config } from './Config';

export interface AssistantTemplate {
    id: string;
    name: string;
    description: string;
    defaultConfig: Config;
}

export interface AssistantServiceInfo {
    assistantServiceId: string;
    templates: AssistantTemplate[];
    metadata: {
        [key: string]: any;
    };
}
