import { AvatarProps } from '@fluentui/react-components';
import { AppGenericRegular, BotRegular, PersonRegular } from '@fluentui/react-icons';
import React from 'react';
import { ConversationParticipant } from '../models/ConversationParticipant';
import { useAppSelector } from '../redux/app/hooks';

export const useParticipantUtility = () => {
    const localUserState = useAppSelector((state) => state.localUser);

    const getAvatarData = React.useCallback(
        (participant: ConversationParticipant | 'localUser') => {
            if (participant === 'localUser') {
                return localUserState.avatar;
            }

            const { id, name, image, role } = participant;

            if (id === localUserState.id) {
                return localUserState.avatar;
            }

            let avatar: AvatarProps = {
                name: role === 'user' ? name : '',
                color: role !== 'user' ? 'neutral' : undefined,
                icon: {
                    user: <PersonRegular />,
                    assistant: <BotRegular />,
                    service: <AppGenericRegular />,
                }[role],
            };

            if (image) {
                avatar = { ...avatar, image: { src: image } };
            }

            return avatar;
        },
        [localUserState.avatar, localUserState.id],
    );

    const sortParticipants = React.useCallback((participants: ConversationParticipant[], includeInactive?: boolean) => {
        return participants
            .filter((participant) => includeInactive || participant.active)
            .sort((a, b) => a.name.localeCompare(b.name));
    }, []);

    return {
        getAvatarData,
        sortParticipants,
    };
};
