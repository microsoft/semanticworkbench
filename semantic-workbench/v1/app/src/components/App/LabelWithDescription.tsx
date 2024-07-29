// Copyright (c) Microsoft. All rights reserved.

import { Text, Tooltip } from '@fluentui/react-components';
import { QuestionCircle16Regular } from '@fluentui/react-icons';
import React from 'react';

interface LabelWithDescriptionProps {
    label: string;
    description?: string;
}

export const LabelWithDescription: React.FC<LabelWithDescriptionProps> = (props) => {
    const { label, description } = props;

    return (
        <div>
            <Text weight="semibold">{label}</Text>
            {description && (
                <Tooltip content={description} relationship="description">
                    <QuestionCircle16Regular fontWeight={100} />
                </Tooltip>
            )}
        </div>
    );
};
