// Copyright (c) Microsoft. All rights reserved.

import { WidgetProps } from '@rjsf/utils';
import React from 'react';
import { DebugInspector } from '../../Conversations/DebugInspector';

export const InspectableWidget: React.FC<WidgetProps> = (props) => {
    const { value } = props;

    let jsonValue = undefined;
    try {
        jsonValue = JSON.parse(value as string);
    } catch (e) {
        return null;
    }

    return <DebugInspector debug={jsonValue} />;
};
