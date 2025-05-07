// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Card,
    CardHeader,
    CardPreview,
    makeStyles,
    Menu,
    MenuButtonProps,
    MenuItem,
    MenuList,
    MenuPopover,
    MenuTrigger,
    shorthands,
    SplitButton,
    Subtitle2,
    Title3,
    tokens,
} from '@fluentui/react-components';
import { ChatAdd24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Constants } from '../../Constants';
import { useConversationUtility } from '../../libs/useConversationUtility';
import { useCreateConversation } from '../../libs/useCreateConversation';
import { useSiteUtility } from '../../libs/useSiteUtility';
import { Assistant } from '../../models/Assistant';
import { useAppSelector } from '../../redux/app/hooks';
import { useGetAssistantServiceInfosQuery } from '../../services/workbench';
import { ExperimentalNotice } from '../App/ExperimentalNotice';
import { Loading } from '../App/Loading';
import { MarkdownContentRenderer } from '../Conversations/ContentRenderers/MarkdownContentRenderer';
import { ConversationsImport } from '../Conversations/ConversationsImport';
import { Chat } from './Chat/Chat';
import { NewConversationForm } from './Controls/NewConversationForm';

interface CardContent {
    contentType: string;
    content: string;
}

interface DashboardCardConfig {
    assistantServiceId: string;
    templateId: string;
    name: string;
    backgroundColor: string;
    cardContent: CardContent;
    icon: string;
}

const useClasses = makeStyles({
    root: {
        flex: '1 1 auto',
        display: 'flex',
        flexDirection: 'column',
    },
    header: {
        flex: '0 0 auto',
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
    },
    body: {
        flex: '1 1 auto',
        display: 'flex',
        justifyContent: 'center',
        height: '90vh',
        marginBottom: tokens.spacingVerticalL,
        overflowY: 'auto',
    },
    content: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
        width: '100%',
        maxWidth: '900px',
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
        height: '100%',
    },
    assistantHeader: {
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        alignItems: 'center',
        width: '100%',
        gap: tokens.spacingHorizontalM,
        marginTop: tokens.spacingVerticalL,
    },
    form: {
        marginTop: tokens.spacingVerticalL,
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
    actions: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: tokens.spacingHorizontalM,
    },
    cards: {
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'center',
        gap: tokens.spacingVerticalL,
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
    },
    card: {
        padding: 0,
        width: '420px',
    },
    cardHeader: {
        padding: tokens.spacingHorizontalM,
        borderRadius: tokens.borderRadiusMedium,
        borderBottomRightRadius: 0,
        borderBottomLeftRadius: 0,
    },
    cardHeaderBody: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxSizing: 'border-box',
        width: '100%',
    },
    cardPreview: {
        padding: tokens.spacingHorizontalM,
        paddingBottom: tokens.spacingVerticalL,
        margin: '0 !important',
        width: '100%',
        boxSizing: 'border-box',
        wordWrap: 'break-word',
        overflowWrap: 'break-word',
        '& ul': {
            boxSizing: 'border-box',
        },
    },
});

interface MainContentProps {
    headerBefore?: React.ReactNode;
    headerAfter?: React.ReactNode;
}

export const MainContent: React.FC<MainContentProps> = (props) => {
    const { headerBefore, headerAfter } = props;
    const activeConversationId = useAppSelector((state) => state.app.activeConversationId);
    const { createConversation } = useCreateConversation();
    const [isValid, setIsValid] = React.useState(false);
    const [assistantId, setAssistantId] = React.useState<string>();
    const [name, setName] = React.useState<string>();
    const [assistantServiceId, setAssistantServiceId] = React.useState<string>();
    const [templateId, setTemplateId] = React.useState<string>();
    const [submitted, setSubmitted] = React.useState(false);
    const { navigateToConversation } = useConversationUtility();
    const siteUtility = useSiteUtility();
    const { isFetching: createConversationIsFetching, assistants } = useCreateConversation();
    const {
        data: assistantServices,
        isLoading: assistantServicesIsLoading,
        isError: assistantServicesIsError,
    } = useGetAssistantServiceInfosQuery({ userIds: ['me'] });

    const classes = useClasses();

    React.useEffect(() => {
        if (!activeConversationId && document.title !== Constants.app.name) {
            siteUtility.setDocumentTitle();
        }
    }, [activeConversationId, siteUtility]);

    const createConversationWithAssistant = React.useCallback(
        async (
            assistantInfo:
                | { assistantId: string }
                | { name: string; assistantServiceId: string; templateId: string; image?: string },
        ) => {
            setSubmitted(true);
            try {
                const { conversation } = await createConversation(assistantInfo);
                navigateToConversation(conversation.id);
            } finally {
                setSubmitted(false);
            }
        },
        [createConversation, navigateToConversation],
    );

    const handleCreate = React.useCallback(async () => {
        if (submitted || !isValid || !assistantId) {
            return;
        }

        // ensure we have a valid assistant info
        let assistantInfo:
            | { assistantId: string }
            | { name: string; assistantServiceId: string; templateId: string }
            | undefined;
        if (assistantId === 'new' && name && assistantServiceId && templateId) {
            assistantInfo = { name, assistantServiceId, templateId };
        } else {
            assistantInfo = { assistantId };
        }

        if (!assistantInfo) {
            return;
        }

        await createConversationWithAssistant(assistantInfo);
    }, [assistantId, assistantServiceId, createConversationWithAssistant, isValid, name, submitted, templateId]);

    const handleImport = React.useCallback(
        (conversationIds: string[]) => {
            if (conversationIds.length > 0) {
                navigateToConversation(conversationIds[0]);
            }
        },
        [navigateToConversation],
    );

    const handleQuickCreate = React.useCallback(
        (assistant: Assistant) => {
            return async () => {
                await createConversationWithAssistant({
                    assistantId: assistant.id,
                });
            };
        },
        [createConversationWithAssistant],
    );

    const quickAssistantCreateButton = React.useCallback(
        (assistants: Assistant[] | undefined) => {
            if (!assistants || assistants.length === 0) {
                return <></>;
            }
            if (assistants.length === 1) {
                return (
                    <Button
                        onClick={handleQuickCreate(assistants[0])}
                        disabled={submitted}
                        icon={<ChatAdd24Regular />}
                    ></Button>
                );
            }
            return (
                <Menu positioning="below-end">
                    <MenuTrigger disableButtonEnhancement>
                        {(triggerProps: MenuButtonProps) => (
                            <SplitButton
                                menuButton={triggerProps}
                                primaryActionButton={{
                                    onClick: handleQuickCreate(assistants[0]),
                                }}
                                disabled={submitted}
                                icon={<ChatAdd24Regular />}
                            ></SplitButton>
                        )}
                    </MenuTrigger>

                    <MenuPopover>
                        <MenuList>
                            {assistants.map((assistant) => (
                                <MenuItem
                                    key={assistant.id}
                                    onClick={handleQuickCreate(assistant)}
                                    disabled={submitted}
                                >
                                    {assistant.name}
                                </MenuItem>
                            ))}
                        </MenuList>
                    </MenuPopover>
                </Menu>
            );
        },
        [handleQuickCreate, submitted],
    );

    const getAssistants = React.useCallback(
        (serviceId: string, templateId: string) => {
            const matches = assistants?.filter(
                (assistant) => assistant.assistantServiceId === serviceId && assistant.templateId === templateId,
            );

            if (matches && matches.length > 0) {
                return matches;
            }
            return undefined;
        },
        [assistants],
    );

    const dashboardCards: DashboardCardConfig[] = React.useMemo(() => {
        if (assistantServicesIsLoading || assistantServicesIsError || !assistantServices) {
            return [];
        }
        return assistantServices
            .filter((service) => service.metadata._dashboard_card)
            .flatMap((service) => {
                const templateConfigs = service.metadata._dashboard_card;
                const results = Object.keys(templateConfigs)
                    .filter((templateId) => templateConfigs[templateId].enabled)
                    .map((templateId) => {
                        const cardConfig = {
                            templateId: templateId,
                            assistantServiceId: service.assistantServiceId,
                            name:
                                service.templates.find((template) => template.id === templateId)?.name ||
                                service.assistantServiceId,
                            icon: templateConfigs[templateId].icon,
                            backgroundColor: templateConfigs[templateId].background_color,
                            cardContent: {
                                contentType: templateConfigs[templateId].card_content.content_type,
                                content: templateConfigs[templateId].card_content.content,
                            },
                        };
                        return cardConfig;
                    });
                return results;
            })
            .sort((a, b) => a.name.localeCompare(b.name));
    }, [assistantServices, assistantServicesIsLoading, assistantServicesIsError]);

    if (activeConversationId) {
        return <Chat conversationId={activeConversationId} headerBefore={headerBefore} headerAfter={headerAfter} />;
    }

    if (createConversationIsFetching) {
        return <Loading />;
    }

    return (
        <div className={classes.root}>
            <>
                <div className={classes.header}>
                    {headerBefore}
                    <ExperimentalNotice />
                    {headerAfter}
                </div>
                <div className={classes.body}>
                    <div className={classes.content}>
                        <div className={classes.assistantHeader}>
                            <Title3>Choose an assistant</Title3>
                        </div>
                        <div className={classes.cards}>
                            {dashboardCards.map((card) => {
                                if (!getAssistants(card.assistantServiceId, card.templateId)) return null;
                                return (
                                    <Card
                                        key={card.assistantServiceId + '/' + card.templateId}
                                        className={classes.card}
                                        appearance="filled"
                                    >
                                        <CardHeader
                                            image={<img src={card.icon} alt="Assistant Icon" />}
                                            header={
                                                <div className={classes.cardHeaderBody}>
                                                    <Title3>{card.name}</Title3>

                                                    {quickAssistantCreateButton(
                                                        getAssistants(card.assistantServiceId, card.templateId),
                                                    )}
                                                </div>
                                            }
                                            className={classes.cardHeader}
                                            style={{ backgroundColor: card.backgroundColor }}
                                        ></CardHeader>
                                        <CardPreview className={classes.cardPreview}>
                                            {card.cardContent.contentType === 'text/markdown' ? (
                                                <MarkdownContentRenderer content={card.cardContent.content} />
                                            ) : (
                                                card.cardContent.content
                                            )}
                                        </CardPreview>
                                    </Card>
                                );
                            })}
                        </div>
                        <div className={classes.form}>
                            <Subtitle2>Or pick from your list of assistants:</Subtitle2>
                            <NewConversationForm
                                assistantFieldLabel=""
                                onSubmit={handleCreate}
                                onChange={(isValid, data) => {
                                    setIsValid(isValid);
                                    setAssistantId(data.assistantId);
                                    setAssistantServiceId(data.assistantServiceId);
                                    setTemplateId(data.templateId);
                                    setName(data.name);
                                }}
                                disabled={submitted}
                            />
                            <div className={classes.actions}>
                                <ConversationsImport
                                    appearance="outline"
                                    onImport={handleImport}
                                    disabled={submitted}
                                />
                                <Button appearance="primary" onClick={handleCreate} disabled={!isValid || submitted}>
                                    Create
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>
            </>
        </div>
    );
};
