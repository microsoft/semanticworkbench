import {
    Button,
    Caption1,
    Card,
    CardHeader,
    makeStyles,
    Menu,
    MenuItem,
    MenuList,
    MenuPopover,
    MenuTrigger,
    mergeClasses,
    Text,
    tokens,
    Tooltip,
} from '@fluentui/react-components';
import {
    ArrowDownloadRegular,
    EditRegular,
    MoreHorizontalRegular,
    PlugDisconnectedRegular,
    SaveCopyRegular,
    ShareRegular,
} from '@fluentui/react-icons';
import React from 'react';
import { useLocalUserAccount } from '../../../libs/useLocalUserAccount';
import { Utility } from '../../../libs/Utility';
import { Conversation } from '../../../models/Conversation';

const useClasses = makeStyles({
    root: {},
    header: {
        display: 'flex',
        flexDirection: 'row',
        flex: 1,
        gap: tokens.spacingHorizontalM,
        alignItems: 'center',
        justifyContent: 'space-between',
        width: '260px',
    },
    title: {
        flexGrow: 1,
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
        minWidth: 0,
    },
    date: {
        flexShrink: 0,

        '&.hidden': {
            visibility: 'hidden',
        },
    },
    description: {
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        maxWidth: '260px',

        '&.unread': {
            fontWeight: 'semibold',
        },
    },
});

interface ConversationItemProps {
    conversation: Conversation;
    owned?: boolean;
    selected?: boolean;
    onSelect?: (conversation: Conversation) => void;
    onExport?: (conversation: Conversation) => void;
    onRename?: (conversation: Conversation) => void;
    onDuplicate?: (conversation: Conversation) => void;
    onShare?: (conversation: Conversation) => void;
    onRemove?: (conversation: Conversation) => void;
}

export const ConversationItem: React.FC<ConversationItemProps> = (props) => {
    const { conversation, owned, selected, onSelect, onExport, onRename, onDuplicate, onShare, onRemove } = props;
    const classes = useClasses();
    const [isHovered, setIsHovered] = React.useState(false);
    const { getUserId } = useLocalUserAccount();
    const userId = getUserId();

    const isUnread = React.useMemo(() => {
        const lastRead: Array<{ participantId: string; timestamp: string }> = conversation.metadata?.lastRead ?? [];
        const lastReadByUser = lastRead.find((lr) => lr.participantId === userId);
        const latestMessageTimestamp = conversation.latest_message?.timestamp ?? conversation.created;

        return !lastReadByUser || lastReadByUser.timestamp < latestMessageTimestamp;
    }, [conversation.metadata, conversation.latest_message, conversation.created, userId]);

    const action = React.useMemo(() => {
        if (!onExport && !onRename && !onDuplicate && !onShare && !onRemove) {
            return undefined;
        }

        const handleMenuItemClick = (
            event: React.MouseEvent<HTMLDivElement>,
            handler?: (conversation: Conversation) => void,
        ) => {
            event.stopPropagation();
            setIsHovered(false);
            handler?.(conversation);
        };

        return (
            <Menu key={conversation.id} positioning="below-end">
                <MenuTrigger disableButtonEnhancement>
                    <Tooltip content="More options" relationship="label">
                        <Button appearance="transparent" icon={<MoreHorizontalRegular />} />
                    </Tooltip>
                </MenuTrigger>
                <MenuPopover>
                    <MenuList>
                        {onRename && (
                            <MenuItem
                                icon={<EditRegular />}
                                onClick={(event) => handleMenuItemClick(event, onRename)}
                                disabled={!owned}
                            >
                                Rename
                            </MenuItem>
                        )}
                        {onExport && (
                            <MenuItem
                                icon={<ArrowDownloadRegular />}
                                onClick={(event) => handleMenuItemClick(event, onExport)}
                            >
                                Export
                            </MenuItem>
                        )}
                        {onDuplicate && (
                            <MenuItem
                                icon={<SaveCopyRegular />}
                                onClick={(event) => handleMenuItemClick(event, onDuplicate)}
                            >
                                Duplicate
                            </MenuItem>
                        )}
                        {onShare && (
                            <MenuItem icon={<ShareRegular />} onClick={(event) => handleMenuItemClick(event, onShare)}>
                                Share
                            </MenuItem>
                        )}
                        {onRemove && (
                            <MenuItem
                                icon={<PlugDisconnectedRegular />}
                                onClick={(event) => handleMenuItemClick(event, onRemove)}
                                disabled={selected}
                            >
                                {selected ? (
                                    <Tooltip content="Cannot remove currently active conversation" relationship="label">
                                        <Text>Remove</Text>
                                    </Tooltip>
                                ) : (
                                    'Remove'
                                )}
                            </MenuItem>
                        )}
                    </MenuList>
                </MenuPopover>
            </Menu>
        );
    }, [conversation, owned, selected, onExport, onRename, onDuplicate, onShare, onRemove]);

    const header = React.useMemo(() => {
        const formattedDate = Utility.toSimpleDateString(
            conversation.latest_message?.timestamp ?? conversation.created,
        );

        return (
            <div className={classes.header}>
                <Text className={classes.title} weight={isUnread ? 'bold' : 'semibold'}>
                    {conversation.title}
                </Text>
                <Caption1 className={mergeClasses(classes.date, isHovered ? 'hidden' : undefined)}>
                    {formattedDate}
                </Caption1>
            </div>
        );
    }, [
        conversation.latest_message?.timestamp,
        conversation.created,
        conversation.title,
        classes.header,
        classes.title,
        classes.date,
        isHovered,
        isUnread,
    ]);

    const description = React.useMemo(() => {
        if (!conversation.latest_message) {
            return undefined;
        }

        const participantId = conversation.latest_message.sender.participantId;
        const sender = conversation.participants.find((p) => p.id === participantId);
        const content = conversation.latest_message.content;

        return (
            <Caption1 className={mergeClasses(classes.description, isUnread ? 'unread' : undefined)}>
                {sender ? `${sender.name}: ${content}` : content}
            </Caption1>
        );
    }, [conversation.latest_message, conversation.participants, classes.description, isUnread]);

    return (
        <Card
            className={classes.root}
            size="small"
            appearance="subtle"
            selected={selected}
            onSelectionChange={() => onSelect?.(conversation)}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            floatingAction={isHovered ? action : undefined}
        >
            <CardHeader header={header} description={description} />
        </Card>
    );
};
