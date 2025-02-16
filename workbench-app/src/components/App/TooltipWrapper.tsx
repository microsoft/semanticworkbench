import { Tooltip } from '@fluentui/react-components';
import React from 'react';

interface TooltipWrapperProps {
    content: string;
    children: React.ReactElement;
}

// Use forwardRef to allow it to still be used within a DialogTrigger
export const TooltipWrapper = React.forwardRef((props: TooltipWrapperProps, forwardedRef) => {
    const { content, children, ...rest } = props;

    // rest will include any props passed by DialogTrigger,
    // e.g. onClick, aria-expanded, data-dialog-trigger, etc.

    const onlyChild = React.Children.only(children);

    // Merge and forward everything onto the actual child (button, link, etc.)
    const childWithAllProps = React.cloneElement(onlyChild, {
        ...onlyChild.props,
        ...rest,
        ref: forwardedRef,
    });

    return (
        <Tooltip content={content} relationship="label">
            {childWithAllProps}
        </Tooltip>
    );
});

TooltipWrapper.displayName = 'TooltipWrapper';
