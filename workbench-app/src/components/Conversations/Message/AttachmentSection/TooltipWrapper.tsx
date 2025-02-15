import { Tooltip } from '@fluentui/react-components';
import React from 'react';

interface TooltipWrapperProps {
    content: string;
    children: React.ReactElement;
}

/**
 * Wraps child elements with a Fluent UI Tooltip.
 *
 * @param content - The text content of the tooltip.
 * @param children - The React element to wrap with the tooltip.
 */
export const TooltipWrapper: React.FC<TooltipWrapperProps> = (props) => {
    const { content, children } = props;
    return (
        <Tooltip content={content} relationship="label">
            {children}
        </Tooltip>
    );
};
