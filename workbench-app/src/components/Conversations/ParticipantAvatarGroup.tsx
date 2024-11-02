import {
    AvatarGroup,
    AvatarGroupItem,
    AvatarGroupPopover,
    partitionAvatarGroupItems,
} from '@fluentui/react-components';
import React from 'react';
import { useParticipantUtility } from '../../libs/useParticipantUtility';
import { ConversationParticipant } from '../../models/ConversationParticipant';

interface ParticipantAvatarGroupProps {
    participants: ConversationParticipant[];
    layout?: 'pie' | 'spread' | 'stack';
}

export const ParticipantAvatarGroup: React.FC<ParticipantAvatarGroupProps> = (props) => {
    const { participants, layout } = props;
    const { getAvatarData } = useParticipantUtility();

    const avatarLayout = layout ?? 'pie';

    const partitionedParticipants = partitionAvatarGroupItems({
        items: participants.map((participant) => participant.name),
        layout: avatarLayout,
    });

    return (
        <AvatarGroup layout={avatarLayout}>
            {partitionedParticipants.inlineItems.map((_, index) => (
                <AvatarGroupItem key={index} avatar={getAvatarData(participants[index])} />
            ))}
            <AvatarGroupPopover>
                {partitionedParticipants.overflowItems?.map((_, index) => (
                    <AvatarGroupItem
                        key={index}
                        name={participants[index].name}
                        avatar={getAvatarData(participants[index])}
                    />
                ))}
            </AvatarGroupPopover>
        </AvatarGroup>
    );
};
