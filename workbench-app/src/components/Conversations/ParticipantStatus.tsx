// Copyright (c) Microsoft. All rights reserved.

import { LatencyLoader } from '@fluentui-copilot/react-copilot';
import { Text, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { useLocalUser } from '../../libs/useLocalUser';
import { ConversationParticipant } from '../../models/ConversationParticipant';

const useClasses = makeStyles({
    root: {
        ...shorthands.padding(tokens.spacingVerticalM, 0, 0, tokens.spacingHorizontalXS),
    },
    item: {
        width: 'fit-content',
        paddingBottom: tokens.spacingVerticalM,
    },
});

interface ParticipantStatusProps {
    participants: ConversationParticipant[];
    onChange?: () => void;
}

export const ParticipantStatus: React.FC<ParticipantStatusProps> = (props) => {
    const { participants, onChange } = props;
    const classes = useClasses();
    const localUser = useLocalUser();

    const statusItems = participants
        ?.map((participant) => {
            // if the participant is offline and assistant, set status to indicate that
            if (participant.online === false && participant.role === 'assistant') {
                return {
                    ...participant,
                    status: 'assistant is currently offline',
                };
            } else {
                return participant;
            }
        })
        .filter((participant) => {
            // don't show the current user's status
            if (participant.id === localUser.id) return false;
            // don't show inactive participants
            if (!participant.active) return false;
            // don't show participants without a status
            if (participant.status === null) return false;
            return true;
        })
        .map((participant) => ({
            id: participant.id,
            name: participant.name,
            status: participant.status,
            statusTimestamp: participant.statusTimestamp,
        }))
        .sort((a, b) => {
            if (a === null || a.statusTimestamp === null) return 1;
            if (b == null || b.statusTimestamp === null) return -1;
            return a.statusTimestamp.localeCompare(b.statusTimestamp);
        }) as { id: string; name: string; status: string }[];

    // if the status has changed, call the onChange callback
    React.useEffect(() => {
        if (onChange) onChange();
    }, [onChange, statusItems]);

    // don't show anything if there are no statuses, but always return something
    // or the virtuoso component will complain about a zero-sized item
    if (statusItems.length === 0) {
        return <div>&nbsp;</div>;
    }

    return (
        <div className={classes.root}>
            {statusItems.map((item) => {
                return (
                    <div key={item.id} className={classes.item}>
                        <LatencyLoader
                            header={
                                <>
                                    <Text weight="semibold">{item.name}</Text>
                                    <Text>
                                        :&nbsp;
                                        {item.status}
                                    </Text>
                                </>
                            }
                        />
                    </div>
                );
            })}
        </div>
    );
};
