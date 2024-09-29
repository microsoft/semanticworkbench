// Copyright (c) Microsoft. All rights reserved.

import { BotRegular } from '@fluentui/react-icons';
import React from 'react';
import { AssistantServiceRegistration } from '../../models/AssistantServiceRegistration';
import { useGetAssistantServiceRegistrationsQuery } from '../../services/workbench';
import { AssistantServiceRegistrationCreate } from '../AssistantServiceRegistrations/AssistantServiceRegistrationCreate';
import { AssistantServiceRegistrationRemove } from '../AssistantServiceRegistrations/AssistantServiceRegistrationRemove';
import { CommandButton } from './CommandButton';
import { MiniControl } from './MiniControl';
import { MyItemsManager } from './MyItemsManager';

interface MyAssistantServiceRegistrationsProps {
    assistantServiceRegistrations?: AssistantServiceRegistration[];
    title?: string;
    hideInstruction?: boolean;
    onCreate?: (assistantServiceRegistration: AssistantServiceRegistration) => void;
}

export const MyAssistantServiceRegistrations: React.FC<MyAssistantServiceRegistrationsProps> = (props) => {
    const { assistantServiceRegistrations, title, hideInstruction, onCreate } = props;
    const { refetch: refetchAssistantServiceRegistrations } = useGetAssistantServiceRegistrationsQuery({
        userIds: ['me'],
    });
    const [assistantServiceRegistrationCreateOpen, setAssistantServiceRegistrationCreateOpen] = React.useState(false);

    const handleAssistantServiceRegistrationCreate = async (
        assistantServiceRegistration: AssistantServiceRegistration,
    ) => {
        await refetchAssistantServiceRegistrations();
        onCreate?.(assistantServiceRegistration);
    };

    return (
        <MyItemsManager
            items={assistantServiceRegistrations
                ?.toSorted((a, b) => a.name.localeCompare(b.name))
                .map((assistantServiceRegistration) => (
                    <MiniControl
                        key={assistantServiceRegistration.assistantServiceId}
                        icon={<BotRegular />}
                        label={assistantServiceRegistration.name}
                        linkUrl={`/assistant-service-registration/${encodeURIComponent(
                            assistantServiceRegistration.assistantServiceId,
                        )}/edit`}
                        actions={
                            <>
                                {/* <Link to={`/assistant/${assistantServiceRegistration.id}/edit`}>
                                    <Button icon={<EditRegular />} />
                                </Link> */}
                                <AssistantServiceRegistrationRemove
                                    assistantServiceRegistration={assistantServiceRegistration}
                                    iconOnly
                                />
                            </>
                        }
                    />
                ))}
            title={title ?? 'My Assistant Service Registrations'}
            itemLabel="Assistant Service Registration"
            hideInstruction={hideInstruction}
            actions={
                <>
                    <CommandButton
                        icon={<BotRegular />}
                        label={`New Assistant Service Registration`}
                        description={`Create a new assistant service registration`}
                        onClick={() => setAssistantServiceRegistrationCreateOpen(true)}
                    />
                    <AssistantServiceRegistrationCreate
                        open={assistantServiceRegistrationCreateOpen}
                        onOpenChange={(open) => setAssistantServiceRegistrationCreateOpen(open)}
                        onCreate={handleAssistantServiceRegistrationCreate}
                    />
                </>
            }
        />
    );
};
