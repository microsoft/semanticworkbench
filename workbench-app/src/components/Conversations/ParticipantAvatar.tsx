import { Persona } from '@fluentui/react-components';
import React from 'react';
import { useParticipantUtility } from '../../libs/useParticipantUtility';
import { ConversationParticipant } from '../../models/ConversationParticipant';

interface ParticipantAvatarProps {
    size?: 'extra-small' | 'small' | 'medium' | 'large' | 'extra-large' | 'huge';
    hideName?: boolean;
    participant: ConversationParticipant;
}

export const ParticipantAvatar: React.FC<ParticipantAvatarProps> = (props) => {
    const { size, hideName, participant } = props;
    const { getAvatarData } = useParticipantUtility();

    return (
        <Persona
            size={size ?? 'extra-small'}
            name={hideName ? undefined : participant.name}
            avatar={getAvatarData(participant)}
        />
    );
};
