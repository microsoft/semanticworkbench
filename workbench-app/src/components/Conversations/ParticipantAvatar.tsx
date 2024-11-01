import { Avatar } from '@fluentui/react-components';
import React from 'react';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { useAppSelector } from '../../redux/app/hooks';

interface ParticipantAvatarProps {
    participant: ConversationParticipant;
}

export const ParticipantAvatar: React.FC<ParticipantAvatarProps> = (props) => {
    const { participant } = props;
    const { user } = useAppSelector((state) => state.app);
    const { id, name, image } = participant;

    const getImage = React.useCallback(() => {
        if (image) {
            return { src: image };
        }

        if (user && user.id === id && user.image) {
            return { src: user.image };
        }

        return undefined;
    }, [image, user, id]);

    return <Avatar name={name} image={getImage()} />;
};
