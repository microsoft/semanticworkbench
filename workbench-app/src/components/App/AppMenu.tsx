// Copyright (c) Microsoft. All rights reserved.

import { Button, Menu, MenuItem, MenuList, MenuPopover, MenuTrigger } from '@fluentui/react-components';
import { MoreHorizontal24Regular, Settings24Regular, Share24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useNavigate } from 'react-router-dom';

export const AppMenu: React.FC = () => {
    const navigate = useNavigate();

    return (
        <Menu>
            <MenuTrigger disableButtonEnhancement>
                <Button icon={<MoreHorizontal24Regular />} />
            </MenuTrigger>
            <MenuPopover>
                <MenuList>
                    <MenuItem
                        icon={<Share24Regular />}
                        onClick={() => {
                            navigate('/shares');
                        }}
                    >
                        Shares
                    </MenuItem>
                    <MenuItem
                        icon={<Settings24Regular />}
                        onClick={() => {
                            navigate('/settings');
                        }}
                    >
                        Settings
                    </MenuItem>
                </MenuList>
            </MenuPopover>
        </Menu>
    );
};
