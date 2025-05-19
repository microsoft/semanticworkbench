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
    SplitButton,
    Title3,
    tokens,
} from '@fluentui/react-components';
import { ChatAdd24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useConversationUtility } from '../../../libs/useConversationUtility';
import { useCreateConversation } from '../../../libs/useCreateConversation';
import { Assistant } from '../../../models/Assistant';
import { useGetAssistantServiceInfosQuery } from '../../../services/workbench';
import { MarkdownContentRenderer } from '../../Conversations/ContentRenderers/MarkdownContentRenderer';

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
    cardHeaderNoContent: {
        padding: tokens.spacingHorizontalM,
        borderRadius: tokens.borderRadiusMedium,
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

interface AssistantCardProps {
    assistantServiceId: string;
    templateId: string;
    newConversationMetadata?: { [key: string]: any };
    hideContent?: boolean;
    includeAssistantIds?: string[];
    requireEnabled?: boolean;
}

export const AssistantCard: React.FC<AssistantCardProps> = (props) => {
    const {
        assistantServiceId,
        templateId,
        hideContent,
        newConversationMetadata,
        includeAssistantIds,
        requireEnabled,
    } = props;
    const { isFetching: createConversationIsFetching, assistants } = useCreateConversation();
    const {
        data: assistantServices,
        isLoading: assistantServicesIsLoading,
        isError: assistantServicesIsError,
    } = useGetAssistantServiceInfosQuery({ userIds: ['me'] });
    const { navigateToConversation } = useConversationUtility();
    const { createConversation } = useCreateConversation();
    const [submitted, setSubmitted] = React.useState(false);

    const classes = useClasses();

    const createConversationWithAssistant = React.useCallback(
        (assistantId: string) => {
            return async () => {
                setSubmitted(true);
                try {
                    const { conversation } = await createConversation({
                        assistantId,
                        conversationMetadata: newConversationMetadata,
                        additionalAssistantIds: includeAssistantIds,
                    });
                    navigateToConversation(conversation.id);
                } finally {
                    setSubmitted(false);
                }
            };
        },
        [createConversation, navigateToConversation, newConversationMetadata, includeAssistantIds],
    );

    const quickAssistantCreateButton = React.useCallback(
        (assistants: Assistant[]) => {
            if (assistants.length === 0) {
                return null;
            }

            if (assistants.length === 1) {
                return (
                    <Button
                        onClick={createConversationWithAssistant(assistants[0].id)}
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
                                    onClick: createConversationWithAssistant(assistants[0].id),
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
                                    onClick={createConversationWithAssistant(assistant.id)}
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
        [createConversationWithAssistant, submitted],
    );

    const assistantInstances = React.useMemo(() => {
        if (createConversationIsFetching) {
            return [];
        }

        const matches = assistants?.filter(
            (assistant) => assistant.assistantServiceId === assistantServiceId && assistant.templateId === templateId,
        );

        if (matches && matches.length > 0) {
            return matches;
        }
        return [];
    }, [assistantServiceId, assistants, createConversationIsFetching, templateId]);

    const dashboardCard: DashboardCardConfig | undefined = React.useMemo(() => {
        if (
            assistantServicesIsLoading ||
            assistantServicesIsError ||
            !assistantServices ||
            !assistantInstances ||
            assistantInstances.length === 0
        ) {
            return undefined;
        }
        const service = assistantServices.find(
            (service) =>
                service.metadata._dashboard_card &&
                service.assistantServiceId === assistantServiceId &&
                service.metadata._dashboard_card[templateId] &&
                (!requireEnabled || service.metadata._dashboard_card[templateId].enabled),
        );

        if (!service) {
            return undefined;
        }
        const templateConfig = service.metadata._dashboard_card[templateId];
        const cardConfig = {
            templateId: templateId,
            assistantServiceId: service.assistantServiceId,
            name: service.templates.find((template) => template.id === templateId)?.name || service.assistantServiceId,
            icon: templateConfig.icon,
            backgroundColor: templateConfig.background_color,
            cardContent: {
                contentType: templateConfig.card_content.content_type,
                content: templateConfig.card_content.content,
            },
        };
        return cardConfig;
    }, [
        assistantServicesIsLoading,
        assistantServicesIsError,
        assistantServices,
        assistantInstances,
        templateId,
        assistantServiceId,
        requireEnabled,
    ]);

    if (!dashboardCard) {
        return null;
    }

    return (
        <Card className={classes.card} appearance="filled">
            <CardHeader
                image={<img src={dashboardCard.icon} alt="Assistant Icon" />}
                header={
                    <div className={classes.cardHeaderBody}>
                        <Title3>{dashboardCard.name}</Title3>

                        {quickAssistantCreateButton(assistantInstances)}
                    </div>
                }
                className={hideContent ? classes.cardHeaderNoContent : classes.cardHeader}
                style={{ backgroundColor: dashboardCard.backgroundColor }}
            ></CardHeader>
            {!hideContent && (
                <CardPreview className={classes.cardPreview}>
                    {dashboardCard.cardContent.contentType === 'text/markdown' ? (
                        <MarkdownContentRenderer content={dashboardCard.cardContent.content} />
                    ) : (
                        dashboardCard.cardContent.content
                    )}
                </CardPreview>
            )}
        </Card>
    );
};
