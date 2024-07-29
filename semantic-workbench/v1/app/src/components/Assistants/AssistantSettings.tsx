// Copyright (c) Microsoft. All rights reserved.

import { Edit24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Link } from 'react-router-dom';
import { Assistant } from '../../models/Assistant';
import { CommandButton } from '../App/CommandButton';

interface AssistantSettingsProps {
    assistant: Assistant;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const AssistantSettings: React.FC<AssistantSettingsProps> = (props) => {
    const { assistant, iconOnly, asToolbarButton } = props;

    return (
        <Link to={`/assistant/${assistant.id}/edit`}>
            <CommandButton
                description="Edit assistant settings"
                icon={<Edit24Regular />}
                iconOnly={iconOnly}
                asToolbarButton={asToolbarButton}
                label="Settings"
            />
        </Link>
    );
};
