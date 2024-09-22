// Copyright (c) Microsoft. All rights reserved.

import { Bot24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Assistant } from '../../models/Assistant';
import { useGetAssistantsQuery } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';
import { MiniControl } from '../App/MiniControl';
import { MyItemsManager } from '../App/MyItemsManager';
import { AssistantCreate } from './AssistantCreate';
import { AssistantDelete } from './AssistantDelete';
import { AssistantDuplicate } from './AssistantDuplicate';
import { AssistantExport } from './AssistantExport';
import { AssistantImport } from './AssistantImport';

interface MyAssistantsProps {
    assistants?: Assistant[];
    title?: string;
    hideInstruction?: boolean;
    onCreate?: (assistant: Assistant) => void;
}

export const MyAssistants: React.FC<MyAssistantsProps> = (props) => {
    const { assistants, title, hideInstruction, onCreate } = props;
    const { refetch: refetchAssistants } = useGetAssistantsQuery();
    const [assistantCreateOpen, setAssistantCreateOpen] = React.useState(false);

    const handleAssistantCreate = async (assistant: Assistant) => {
        await refetchAssistants();
        onCreate?.(assistant);
    };

    const handleAssistantImport = async (result: { assistantIds: string[]; conversationIds: string[] }) => {
        (await refetchAssistants().unwrap())
            .filter((assistant) => result.assistantIds.includes(assistant.id))
            .forEach((assistant) => onCreate?.(assistant));
    };

    return (
        <MyItemsManager
            items={assistants
                ?.filter((assistant) => assistant.metadata?.workflow_run_id === undefined)
                .toSorted((a, b) => a.name.localeCompare(b.name))
                .map((assistant) => (
                    <MiniControl
                        key={assistant.id}
                        icon={<Bot24Regular />}
                        label={assistant?.name}
                        linkUrl={`/assistant/${encodeURIComponent(assistant.id)}/edit`}
                        actions={
                            <>
                                <AssistantExport assistantId={assistant.id} iconOnly />
                                <AssistantDuplicate assistant={assistant} iconOnly />
                                <AssistantDelete assistant={assistant} iconOnly />
                            </>
                        }
                    />
                ))}
            title={title ?? 'My Assistants'}
            itemLabel="Assistant"
            hideInstruction={hideInstruction}
            actions={
                <>
                    <CommandButton
                        icon={<Bot24Regular />}
                        label={`New Assistant`}
                        description={`Create a new assistant`}
                        onClick={() => setAssistantCreateOpen(true)}
                    />
                    <AssistantCreate
                        open={assistantCreateOpen}
                        onOpenChange={(open) => setAssistantCreateOpen(open)}
                        onCreate={handleAssistantCreate}
                        onImport={handleAssistantImport}
                    />
                    <AssistantImport onImport={handleAssistantImport} />
                </>
            }
        />
    );
};
