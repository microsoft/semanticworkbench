// Copyright (c) Microsoft. All rights reserved.

import { Text } from '@fluentui/react-components';
import { QuestionCircle16Regular } from '@fluentui/react-icons';
import React from 'react';
import { TooltipWrapper } from './TooltipWrapper';

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
                <TooltipWrapper content={description}>
                    <QuestionCircle16Regular fontWeight={100} />
                </TooltipWrapper>
            )}
        </div>
    );
};
