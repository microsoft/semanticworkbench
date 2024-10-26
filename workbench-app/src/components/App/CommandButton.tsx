// Copyright (c) Microsoft. All rights reserved.

import { Button, ButtonProps, ToolbarButton, Tooltip } from '@fluentui/react-components';
import React from 'react';
import { DialogControl, DialogControlContent } from './DialogControl';

type CommandButtonProps = ButtonProps & {
    label?: string;
    description?: string;
    onClick?: () => void;
    dialogContent?: DialogControlContent;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
};

export const CommandButton: React.FC<CommandButtonProps> = (props) => {
    const {
        as,
        disabled,
        icon,
        label,
        description,
        onClick,
        dialogContent,
        iconOnly,
        asToolbarButton,
        appearance,
        size,
    } = props;

    let commandButton = null;

    if (dialogContent?.trigger) {
        if (description) {
            commandButton = (
                <Tooltip content={description} relationship="label">
                    {dialogContent.trigger}
                </Tooltip>
            );
        } else {
            commandButton = dialogContent.trigger;
        }
    } else if (iconOnly) {
        if (description) {
            commandButton = (
                <Tooltip content={description} relationship="label">
                    <Button as={as} disabled={disabled} icon={icon} onClick={onClick} />
                </Tooltip>
            );
        } else {
            commandButton = <Button as={as} disabled={disabled} icon={icon} onClick={onClick} />;
        }
    } else if (asToolbarButton) {
        commandButton = (
            <ToolbarButton disabled={disabled} icon={icon} onClick={onClick}>
                {label}
            </ToolbarButton>
        );
    } else {
        commandButton = (
            <Button as={as} disabled={disabled} icon={icon} appearance={appearance} size={size} onClick={onClick}>
                {label}
            </Button>
        );
        if (description) {
            commandButton = (
                <Tooltip content={description} relationship="label">
                    {commandButton}
                </Tooltip>
            );
        }
    }

    if (!dialogContent) {
        return commandButton;
    }

    return (
        <DialogControl
            trigger={commandButton}
            classNames={dialogContent.classNames}
            title={dialogContent.title}
            content={dialogContent.content}
            closeLabel={dialogContent.closeLabel}
            additionalActions={dialogContent.additionalActions}
            onOpenChange={dialogContent.onOpenChange}
        />
    );
};
