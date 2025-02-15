import { Tooltip } from '@fluentui/react-components';
import React from 'react';

interface TooltipWrapperProps {
    content: string;
    children: React.ReactElement;
}

export const TooltipWrapper: React.FC<TooltipWrapperProps> = (props) => {
    const { content, children } = props;
    return (
        <Tooltip content={content} relationship="label">
            {children}
        </Tooltip>
    );
};
