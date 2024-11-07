// Copyright (c) Microsoft. All rights reserved.

import { ButtonProps, MenuItem, Tooltip } from '@fluentui/react-components';
import React from 'react';

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
                <Tooltip content={description} relationship="label">
                    <MenuItem disabled={disabled} icon={icon} onClick={onClick} />
                </Tooltip>
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
            menuItem = (
                <Tooltip content={description} relationship="label">
                    {menuItem}
                </Tooltip>
            );
        }
    }
    return menuItem;
};
