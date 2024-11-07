// Copyright (c) Microsoft. All rights reserved.

import { DatabaseRegular } from '@fluentui/react-icons';
import React from 'react';
import { Assistant } from '../../models/Assistant';
import { CommandButton } from '../App/CommandButton';
import { AssistantServiceMetadata } from './AssistantServiceMetadata';

interface AssistantServiceInfoProps {
    assistant: Assistant;
    iconOnly?: boolean;
    disabled?: boolean;
    simulateMenuItem?: boolean;
}

export const AssistantServiceInfo: React.FC<AssistantServiceInfoProps> = (props) => {
    const { assistant, iconOnly, disabled, simulateMenuItem } = props;

    return (
        <CommandButton
            icon={<DatabaseRegular />}
            simulateMenuItem={simulateMenuItem}
            label="Service Info"
            iconOnly={iconOnly}
            description="View assistant service info"
            disabled={disabled}
            dialogContent={{
                title: `"${assistant.name}" Service Info`,
                content: <AssistantServiceMetadata assistantServiceId={assistant.assistantServiceId} />,
                closeLabel: 'Close',
            }}
        />
    );
};
