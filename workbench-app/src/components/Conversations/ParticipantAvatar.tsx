import { Avatar } from '@fluentui/react-components';
import React from 'react';
import { useParticipantUtility } from '../../libs/useParticipantUtility';
import { ConversationParticipant } from '../../models/ConversationParticipant';

interface ParticipantAvatarProps {
    participant: ConversationParticipant;
}

export const ParticipantAvatar: React.FC<ParticipantAvatarProps> = (props) => {
    const { participant } = props;
    const { getAvatarData } = useParticipantUtility();

    const avatarData = getAvatarData(participant);
    return <Avatar image={avatarData.image} name={avatarData.name} />;
};
