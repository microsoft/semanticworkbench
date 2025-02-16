// Copyright (c) Microsoft. All rights reserved.

import { Button, ButtonProps, makeStyles, mergeClasses, tokens, ToolbarButton } from '@fluentui/react-components';
import React from 'react';
import { DialogControl, DialogControlContent } from './DialogControl';
import { TooltipWrapper } from './TooltipWrapper';

const useClasses = makeStyles({
    menuItem: {
        paddingLeft: tokens.spacingHorizontalXS,
        paddingRight: tokens.spacingHorizontalXS,
        justifyContent: 'flex-start',
        fontWeight: 'normal',
    },
});

type CommandButtonProps = ButtonProps & {
    className?: string;
    label?: string;
    description?: string;
    onClick?: () => void;
    dialogContent?: DialogControlContent;
    open?: boolean;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
    simulateMenuItem?: boolean;
};

export const CommandButton: React.FC<CommandButtonProps> = (props) => {
    const {
        as,
        className,
        disabled,
        icon,
        label,
        description,
        onClick,
        dialogContent,
        open,
        iconOnly,
        asToolbarButton,
        appearance,
        size,
        simulateMenuItem,
    } = props;
    const classes = useClasses();

    let commandButton = null;

    if (dialogContent?.trigger) {
        if (description) {
            commandButton = <TooltipWrapper content={description}>{dialogContent.trigger}</TooltipWrapper>;
        } else {
            commandButton = dialogContent.trigger;
        }
    } else if (simulateMenuItem) {
        commandButton = (
            <Button
                as={as}
                className={mergeClasses(classes.menuItem, className)}
                appearance={appearance ?? 'subtle'}
                size={size}
                disabled={disabled}
                icon={icon}
                onClick={onClick}
            >
                {label}
            </Button>
        );
    } else if (iconOnly) {
        if (description) {
            commandButton = (
                <TooltipWrapper content={description}>
                    <Button
                        as={as}
                        className={className}
                        appearance={appearance}
                        size={size}
                        disabled={disabled}
                        icon={icon}
                        onClick={onClick}
                    />
                </TooltipWrapper>
            );
        } else {
            commandButton = (
                <Button
                    as={as}
                    className={className}
                    appearance={appearance}
                    size={size}
                    disabled={disabled}
                    icon={icon}
                    onClick={onClick}
                />
            );
        }
    } else if (asToolbarButton) {
        commandButton = (
            <ToolbarButton className={className} disabled={disabled} icon={icon} onClick={onClick}>
                {label}
            </ToolbarButton>
        );
    } else {
        commandButton = (
            <Button
                as={as}
                className={className}
                disabled={disabled}
                icon={icon}
                appearance={appearance}
                size={size}
                onClick={onClick}
            >
                {label}
            </Button>
        );
        if (description) {
            commandButton = <TooltipWrapper content={description}>{commandButton}</TooltipWrapper>;
        }
    }

    if (!dialogContent) {
        return commandButton;
    }

    return (
        <DialogControl
            trigger={commandButton}
            classNames={dialogContent.classNames}
            open={open}
            title={dialogContent.title}
            content={dialogContent.content}
            closeLabel={dialogContent.closeLabel}
            hideDismissButton={dialogContent.hideDismissButton}
            additionalActions={dialogContent.additionalActions}
            onOpenChange={dialogContent.onOpenChange}
        />
    );
};
