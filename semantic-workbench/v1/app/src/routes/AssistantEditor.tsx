// Copyright (c) Microsoft. All rights reserved.

import { Card, Divider, Text, Title3, Toolbar, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { useParams } from 'react-router-dom';
import { AppView } from '../components/App/AppView';
import { Loading } from '../components/App/Loading';
import { AssistantDelete } from '../components/Assistants/AssistantDelete';
import { AssistantDuplicate } from '../components/Assistants/AssistantDuplicate';
import { AssistantEdit } from '../components/Assistants/AssistantEdit';
import { AssistantExport } from '../components/Assistants/AssistantExport';
import { AssistantRename } from '../components/Assistants/AssistantRename';
import { AssistantServiceMetadata } from '../components/Assistants/AssistantServiceMetadata';
import { MyConversations } from '../components/Conversations/MyConversations';
import { useSiteUtility } from '../libs/useSiteUtility';
import { Assistant } from '../models/Assistant';
import { Conversation } from '../models/Conversation';
import {
    useAddConversationParticipantMutation,
    useCreateConversationMessageMutation,
    useGetAssistantConversationsQuery,
    useGetAssistantQuery,
    useUpdateAssistantMutation,
} from '../services/workbench';

const useClasses = makeStyles({
    root: {
        display: 'grid',
        gridTemplateRows: '1fr auto',
        height: '100%',
        gap: tokens.spacingVerticalM,
    },
    card: {
        backgroundImage: `linear-gradient(to right, ${tokens.colorNeutralBackground1}, ${tokens.colorBrandBackground2})`,
    },
    title: {
        color: tokens.colorNeutralForegroundOnBrand,
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: tokens.spacingHorizontalM,
    },
    content: {
        overflowY: 'auto',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
        ...shorthands.padding(0, tokens.spacingHorizontalM),
    },
    toolbar: {
        backgroundColor: tokens.colorNeutralBackgroundAlpha,
        borderRadius: tokens.borderRadiusMedium,
    },
});

export const AssistantEditor: React.FC = () => {
    const { assistantId } = useParams();
    if (!assistantId) {
        throw new Error('Assistant ID is required');
    }

    const classes = useClasses();
    const {
        data: assistantConversations,
        error: assistantConversationsError,
        isLoading: isLoadingAssistantConversations,
    } = useGetAssistantConversationsQuery(assistantId);
    const { data: assistant, error: assistantError, isLoading: isLoadingAssistant } = useGetAssistantQuery(assistantId);
    const [updateAssistant] = useUpdateAssistantMutation();
    const [addConversationParticipant] = useAddConversationParticipantMutation();
    const [createConversationMessage] = useCreateConversationMessageMutation();
    const siteUtility = useSiteUtility();

    if (assistantConversationsError) {
        const errorMessage = JSON.stringify(assistantConversationsError);
        throw new Error(`Error loading assistant conversations: ${errorMessage}`);
    }

    if (assistantError) {
        const errorMessage = JSON.stringify(assistantError);
        throw new Error(`Error loading assistant: ${errorMessage}`);
    }

    React.useEffect(() => {
        if (isLoadingAssistant) return;
        if (!assistant) {
            throw new Error(`Assistant with ID ${assistantId} not found`);
        }
        siteUtility.setDocumentTitle(`Edit ${assistant.name}`);
    }, [assistantId, assistant, isLoadingAssistant, siteUtility]);

    const handleRename = React.useCallback(
        async (newName: string) => {
            if (!assistant) {
                throw new Error('Assistant is not set, unable to update name');
            }
            await updateAssistant({ ...assistant, name: newName } as Assistant);
        },
        [assistant, updateAssistant],
    );

    const handleDelete = React.useCallback(() => {
        // navigate to site root
        siteUtility.forceNavigateTo('/');
    }, [siteUtility]);

    const handleDuplicate = (assistant: Assistant) => {
        siteUtility.forceNavigateTo(`/assistant/${assistant.id}/edit`);
    };

    const handleConversationCreate = async (conversation: Conversation) => {
        // add assistant to conversation
        await addConversationParticipant({ conversationId: conversation.id, participantId: assistantId });

        await createConversationMessage({
            conversationId: conversation.id,
            content: `${assistant?.name} added to conversation`,
            messageType: 'notice',
        });
    };

    if (isLoadingAssistant || isLoadingAssistantConversations || !assistant) {
        return (
            <AppView title="Edit Assistant">
                <Loading />
            </AppView>
        );
    }

    return (
        <AppView
            title={
                <div className={classes.title}>
                    <AssistantRename value={assistant.name} onRename={handleRename} />
                    <Title3>{assistant.name}</Title3>
                </div>
            }
        >
            <div className={classes.root}>
                <div className={classes.content}>
                    <AssistantServiceMetadata assistantServiceId={assistant.assistantServiceId} />
                    <MyConversations
                        title="Conversations"
                        conversations={assistantConversations}
                        participantId={assistantId}
                        hideInstruction
                        onCreate={handleConversationCreate}
                    />
                    <Card className={classes.card}>
                        <Text size={400} weight="semibold">
                            Assistant Configuration
                        </Text>
                        <Text size={300} italic color="neutralSecondary">
                            Please practice Responsible AI when configuring your assistant. See the{' '}
                            <a
                                href="https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/system-message"
                                target="_blank"
                                rel="noreferrer"
                            >
                                Microsoft Azure OpenAI Service: System message templates
                            </a>{' '}
                            page for suggestions regarding content for the prompts below.
                        </Text>
                        <Divider />
                        <AssistantEdit assistant={assistant} />
                    </Card>
                </div>
                <Toolbar className={classes.toolbar}>
                    <AssistantDelete asToolbarButton assistant={assistant} onDelete={handleDelete} />
                    <AssistantExport asToolbarButton assistantId={assistant.id} />
                    <AssistantDuplicate asToolbarButton assistant={assistant} onDuplicate={handleDuplicate} />
                </Toolbar>
            </div>
        </AppView>
    );
};
