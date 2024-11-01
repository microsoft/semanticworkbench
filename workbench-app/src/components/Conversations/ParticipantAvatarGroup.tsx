import {
    AvatarGroup,
    AvatarGroupItem,
    AvatarGroupPopover,
    partitionAvatarGroupItems,
} from '@fluentui/react-components';
import React from 'react';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { useAppSelector } from '../../redux/app/hooks';

interface ParticipantAvatarGroupProps {
    participants: ConversationParticipant[];
    layout?: 'pie' | 'spread' | 'stack';
}

export const ParticipantAvatarGroup: React.FC<ParticipantAvatarGroupProps> = (props) => {
    const { participants, layout } = props;
    const { user } = useAppSelector((state) => state.app);

    const getAvatar = React.useCallback(
        (participant: ConversationParticipant) => {
            const { id, name, image } = participant;
            let avatar: Record<string, any> = { name };

            if (image) {
                avatar = { ...avatar, image: { src: image } };
            } else if (user && user.id === id && user.image) {
                avatar = { ...avatar, image: { src: user.image } };
            }

            return avatar;
        },
        [user],
    );

    const avatarLayout = layout ?? 'pie';

    const partitionedParticipants = partitionAvatarGroupItems({
        items: participants.map((participant) => participant.name),
        layout: avatarLayout,
    });

    return (
        <AvatarGroup layout={avatarLayout}>
            {partitionedParticipants.inlineItems.map((_, index) => (
                <AvatarGroupItem key={index} avatar={getAvatar(participants[index])} />
            ))}
            <AvatarGroupPopover>
                {partitionedParticipants.overflowItems?.map((_, index) => (
                    <AvatarGroupItem
                        key={index}
                        name={participants[index].name}
                        avatar={getAvatar(participants[index])}
                    />
                ))}
            </AvatarGroupPopover>
        </AvatarGroup>
    );
};
