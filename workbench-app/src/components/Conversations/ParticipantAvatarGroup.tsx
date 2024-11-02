import {
    AvatarGroup,
    AvatarGroupItem,
    AvatarGroupPopover,
    makeStyles,
    partitionAvatarGroupItems,
    Persona,
    Popover,
    PopoverSurface,
    PopoverTrigger,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { useParticipantUtility } from '../../libs/useParticipantUtility';
import { ConversationParticipant } from '../../models/ConversationParticipant';

const useClasses = makeStyles({
    popover: {
        display: 'flex',
        flexDirection: 'row',
        gap: tokens.spacingHorizontalM,
        alignItems: 'center',
    },
});

interface ParticipantAvatarGroupProps {
    participants: ConversationParticipant[];
    layout?: 'pie' | 'spread' | 'stack';
    maxInlineItems?: number;
}

interface ParticipantAvatarGroupItemProps {
    participant: ConversationParticipant;
    enablePopover?: boolean;
}

const ParticipantAvatarGroupItem: React.FC<ParticipantAvatarGroupItemProps> = (props) => {
    const { participant, enablePopover } = props;
    const classes = useClasses();
    const { getAvatarData } = useParticipantUtility();

    const avatar = getAvatarData(participant);

    if (!enablePopover) {
        return <AvatarGroupItem name={participant.name} avatar={avatar} />;
    }

    return (
        <Popover>
            <PopoverTrigger>
                <AvatarGroupItem name={participant.name} avatar={avatar} />
            </PopoverTrigger>
            <PopoverSurface className={classes.popover}>
                <Persona name={participant.name} avatar={avatar} textAlignment="center" />
            </PopoverSurface>
        </Popover>
    );
};

export const ParticipantAvatarGroup: React.FC<ParticipantAvatarGroupProps> = (props) => {
    const { participants, layout, maxInlineItems } = props;
    const classes = useClasses();

    const avatarLayout = layout ?? 'pie';

    const partitionedParticipants = partitionAvatarGroupItems({
        items: participants.map((participant) => participant.name),
        layout: avatarLayout,
        maxInlineItems:
            maxInlineItems ??
            {
                pie: 0,
                spread: 3,
                stack: 3,
            }[avatarLayout],
    });

    return (
        <AvatarGroup layout={avatarLayout}>
            {partitionedParticipants.inlineItems.map((_, index) => (
                <ParticipantAvatarGroupItem
                    key={index}
                    participant={participants[index]}
                    enablePopover={layout !== 'pie'}
                />
            ))}
            {partitionedParticipants.overflowItems && (
                <AvatarGroupPopover>
                    {partitionedParticipants.overflowItems.map((_, index) => (
                        <ParticipantAvatarGroupItem key={index} participant={participants[index]} />
                    ))}
                </AvatarGroupPopover>
            )}
        </AvatarGroup>
    );
};
