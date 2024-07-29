// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    ButtonProps,
    Dialog,
    DialogActions,
    DialogBody,
    DialogContent,
    DialogOpenChangeData,
    DialogOpenChangeEvent,
    DialogSurface,
    DialogTitle,
    DialogTrigger,
    ToolbarButton,
    Tooltip,
} from '@fluentui/react-components';
import React from 'react';

type CommandButtonProps = ButtonProps & {
    trigger?: React.ReactElement;
    label?: string;
    description?: string;
    onClick?: () => void;
    dialogContent?: {
        title: string;
        content: React.ReactNode;
        closeLabel?: string;
        additionalActions?: React.ReactElement[];
        onOpenChange?: (event: DialogOpenChangeEvent, data: DialogOpenChangeData) => void;
    };
    iconOnly?: boolean;
    asToolbarButton?: boolean;
};

export const CommandButton: React.FC<CommandButtonProps> = (props) => {
    const {
        as,
        trigger,
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

    if (trigger && dialogContent) {
        if (description) {
            commandButton = (
                <Tooltip content={description} relationship="label">
                    {trigger}
                </Tooltip>
            );
        } else {
            commandButton = trigger;
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
    }

    if (!dialogContent) {
        return commandButton;
    }

    return (
        <Dialog onOpenChange={dialogContent.onOpenChange}>
            <DialogTrigger>{commandButton}</DialogTrigger>
            <DialogSurface>
                <DialogBody>
                    <DialogTitle>{dialogContent?.title}</DialogTitle>
                    <DialogContent>{dialogContent?.content}</DialogContent>
                    <DialogActions>
                        <DialogTrigger>
                            <Button>{dialogContent.closeLabel ?? 'Close'}</Button>
                        </DialogTrigger>
                        {dialogContent?.additionalActions?.map((action, index) => (
                            <DialogTrigger key={index}>{action}</DialogTrigger>
                        ))}
                    </DialogActions>
                </DialogBody>
            </DialogSurface>
        </Dialog>
    );
};
