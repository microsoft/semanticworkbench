// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Divider,
    Menu,
    MenuItem,
    MenuList,
    MenuPopover,
    MenuTrigger,
    makeStyles,
} from '@fluentui/react-components';
import { Bot24Regular, BotAddRegular, Sparkle24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Assistant } from '../../models/Assistant';
import { useGetAssistantsQuery } from '../../services/workbench';
import { Loading } from '../App/Loading';
import { AssistantCreate } from './AssistantCreate';

const useClasses = makeStyles({
    menuList: {
        maxHeight: 'calc(100vh - 200px)',
    },
});

interface AssistantAddProps {
    exceptAssistantIds?: string[];
    onAdd: (assistant: Assistant) => void;
    disabled?: boolean;
}

export const AssistantAdd: React.FC<AssistantAddProps> = (props) => {
    const { exceptAssistantIds, onAdd, disabled } = props;
    const classes = useClasses();
    const { data: assistants, error: getAssistantsError, isLoading: isLoadingAssistants } = useGetAssistantsQuery();
    const [assistantCreateOpen, setAssistantCreateOpen] = React.useState(false);

    if (getAssistantsError) {
        const errorMessage = JSON.stringify(getAssistantsError);
        throw new Error(`Error loading assistants: ${errorMessage}`);
    }

    if (isLoadingAssistants) {
        return <Loading />;
    }

    if (!assistants) {
        throw new Error(`Assistants not found`);
    }

    const handleNewAssistant = () => {
        setAssistantCreateOpen(true);
    };

    const handleAssistantAdd = async (assistant: Assistant) => {
        onAdd(assistant);
    };

    const unusedAssistants = assistants.filter((assistant) => !exceptAssistantIds?.includes(assistant.id));

    return (
        <div>
            <AssistantCreate
                open={assistantCreateOpen}
                onOpenChange={(open) => setAssistantCreateOpen(open)}
                onCreate={(assistant) => handleAssistantAdd(assistant)}
            />
            <Menu>
                <MenuTrigger disableButtonEnhancement>
                    <Button disabled={disabled} icon={<BotAddRegular />}>
                        Add assistant
                    </Button>
                </MenuTrigger>
                <MenuPopover className={classes.menuList}>
                    <MenuList>
                        {unusedAssistants.length === 0 && <MenuItem>No assistants available</MenuItem>}
                        {unusedAssistants
                            .sort((a, b) => a.name.toLocaleLowerCase().localeCompare(b.name.toLocaleLowerCase()))
                            .map((assistant) => (
                                <MenuItem
                                    key={assistant.id}
                                    icon={<Bot24Regular />}
                                    onClick={() => handleAssistantAdd(assistant)}
                                >
                                    {assistant.name}
                                </MenuItem>
                            ))}
                    </MenuList>
                    <Divider />
                    <MenuItem icon={<Sparkle24Regular />} onClick={handleNewAssistant}>
                        Create new assistant
                    </MenuItem>
                </MenuPopover>
            </Menu>
        </div>
    );
};
