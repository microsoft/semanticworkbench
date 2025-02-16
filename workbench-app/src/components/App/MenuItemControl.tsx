// Copyright (c) Microsoft. All rights reserved.

import { ButtonProps, MenuItem } from '@fluentui/react-components';
import React from 'react';
import { TooltipWrapper } from './TooltipWrapper';

type MenuItemControlProps = ButtonProps & {
    label?: string;
    description?: string;
    onClick?: () => void;
    iconOnly?: boolean;
};

export const MenuItemControl: React.FC<MenuItemControlProps> = (props) => {
    const { disabled, icon, label, description, onClick, iconOnly } = props;

    let menuItem = null;

    if (iconOnly) {
        if (description) {
            menuItem = (
                <TooltipWrapper content={description}>
                    <MenuItem disabled={disabled} icon={icon} onClick={onClick} />
                </TooltipWrapper>
            );
        } else {
            menuItem = <MenuItem disabled={disabled} icon={icon} onClick={onClick} />;
        }
    } else {
        menuItem = (
            <MenuItem disabled={disabled} icon={icon} onClick={onClick}>
                {label}
            </MenuItem>
        );
        if (description) {
            menuItem = <TooltipWrapper content={description}>{menuItem}</TooltipWrapper>;
        }
    }
    return menuItem;
};
