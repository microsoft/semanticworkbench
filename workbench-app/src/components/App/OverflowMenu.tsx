import {
    Button,
    makeStyles,
    Menu,
    MenuItem,
    MenuList,
    MenuPopover,
    MenuTrigger,
    Slot,
    tokens,
    useIsOverflowItemVisible,
    useOverflowMenu,
} from '@fluentui/react-components';
import { MoreHorizontalRegular } from '@fluentui/react-icons';
import React from 'react';

const useClasses = makeStyles({
    menu: {
        backgroundColor: tokens.colorNeutralBackground1,
    },
    menuButton: {
        alignSelf: 'center',
    },
});

export interface OverflowMenuItemData {
    id: string;
    icon?: Slot<'span'>;
    name?: string;
}

interface OverflowMenuItemProps {
    item: OverflowMenuItemData;
    onClick: (event: React.MouseEvent, id: string) => void;
}

export const OverflowMenuItem: React.FC<OverflowMenuItemProps> = (props) => {
    const { item, onClick } = props;
    const isVisible = useIsOverflowItemVisible(item.id);

    if (isVisible) {
        return null;
    }

    return (
        <MenuItem key={item.id} icon={item.icon} onClick={(event) => onClick(event, item.id)}>
            {item.name}
        </MenuItem>
    );
};

interface OverflowMenuProps {
    items: OverflowMenuItemData[];
    onItemSelect: (id: string) => void;
}

export const OverflowMenu: React.FC<OverflowMenuProps> = (props) => {
    const { items, onItemSelect } = props;
    const classes = useClasses();
    const { ref, isOverflowing, overflowCount } = useOverflowMenu<HTMLButtonElement>();

    const handleItemClick = (_event: React.MouseEvent, id: string) => {
        onItemSelect(id);
    };

    if (!isOverflowing) {
        return null;
    }

    return (
        <Menu hasIcons={items.find((item) => item.icon !== undefined) !== undefined}>
            <MenuTrigger disableButtonEnhancement>
                <Button
                    className={classes.menuButton}
                    appearance="transparent"
                    ref={ref}
                    icon={<MoreHorizontalRegular />}
                    aria-label={`${overflowCount} more options`}
                    role="tab"
                />
            </MenuTrigger>
            <MenuPopover>
                <MenuList className={classes.menu}>
                    {items.map((item) => (
                        <OverflowMenuItem key={item.id} item={item} onClick={handleItemClick}></OverflowMenuItem>
                    ))}
                </MenuList>
            </MenuPopover>
        </Menu>
    );
};
