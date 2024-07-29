// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Card,
    Drawer,
    DrawerBody,
    DrawerHeader,
    DrawerHeaderTitle,
    Text,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import { Dismiss24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Constants } from '../../Constants';
import { Conversation } from '../../models/Conversation';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { ConversationTranscript } from './ConversationTranscript';
import { FileList } from './FileList';
import { FileUpload } from './FileUpload';
import { ParticipantList } from './ParticipantList';

const useClasses = makeStyles({
    root: {
        display: 'grid',
        gridTemplateColumns: '1fr auto',
        gridTemplateRows: '1fr',
        height: '100%',
    },
    main: {
        position: 'relative',
        display: 'grid',
        gridTemplateColumns: '1fr',
        gridTemplateRows: '1fr auto',
        height: '100%',
    },
    history: {
        position: 'relative',
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'center',
        gap: tokens.spacingVerticalM,
    },
    controls: {
        position: 'absolute',
        top: 0,
        left: 0,
        bottom: 0,
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'stretch',
        zIndex: 1000,
    },
    drawer: {
        '& > .fui-DrawerBody': {
            backgroundImage: `linear-gradient(to right, ${tokens.colorNeutralBackground1}, ${tokens.colorBrandBackground2})`,
            backgroundSize: '100%',
        },
    },
    drawerHeader: {
        ...shorthands.borderBottom(tokens.strokeWidthThick, 'solid', tokens.colorNeutralStroke3),
    },
    drawerBody: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
    },
    drawerButton: {
        position: 'absolute',
        ...shorthands.padding(tokens.spacingVerticalS),
    },
    card: {},
    resizer: {
        ...shorthands.borderLeft(tokens.strokeWidthThin, 'solid', tokens.colorNeutralBackground5),
        width: '8px',
        position: 'absolute',
        top: 0,
        bottom: 0,
        left: 0,
        cursor: 'col-resize',
        resize: 'horizontal',
        ':hover': {
            borderLeftWidth: '4px',
        },
    },
    resizerActive: {
        borderLeftWidth: '4px',
        borderLeftColor: tokens.colorNeutralBackground5Pressed,
    },
    inspectorButton: {
        position: 'absolute',
        top: 0,
        right: 0,
        ...shorthands.padding(tokens.spacingVerticalS),
        zIndex: 1000,
    },
    inspectors: {
        position: 'relative',
        backgroundColor: tokens.colorNeutralBackgroundAlpha,
        height: '100%',
        overflowY: 'auto',
    },
    input: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'center',
        backgroundImage: `linear-gradient(to right, ${tokens.colorNeutralBackground1}, ${tokens.colorBrandBackground2})`,
        ...shorthands.borderTop(tokens.strokeWidthThick, 'solid', tokens.colorNeutralStroke3),
        ...shorthands.borderBottom(tokens.strokeWidthThick, 'solid', tokens.colorNeutralStroke3),
    },
    historyContent: {
        // do not use flexbox here, it breaks the virtuoso
        width: '100%',
        maxWidth: `${Constants.app.maxContentWidth}px`,
        ...shorthands.padding(0, tokens.spacingHorizontalXXXL),
    },
    historyContentWithInspector: {
        paddingRight: tokens.spacingHorizontalNone,
    },
});

interface ConversationControlsProps {
    conversation: Conversation;
    participants: ConversationParticipant[];
    preventAssistantModifyOnParticipantIds?: string[];
    onOpenChange?: (open: boolean) => void;
}

export const ConversationControls: React.FC<ConversationControlsProps> = (props) => {
    const { conversation, participants, preventAssistantModifyOnParticipantIds, onOpenChange } = props;
    const classes = useClasses();

    return (
        <Drawer
            className={classes.drawer}
            type="overlay"
            separator
            open
            onOpenChange={(_event, { open }) => onOpenChange?.(open)}
        >
            <DrawerHeader className={classes.drawerHeader}>
                <DrawerHeaderTitle
                    action={
                        <Button appearance="subtle" icon={<Dismiss24Regular />} onClick={() => onOpenChange?.(false)} />
                    }
                >
                    Conversation
                </DrawerHeaderTitle>
            </DrawerHeader>
            <DrawerBody className={classes.drawerBody}>
                <Card className={classes.card}>
                    <Text size={400} weight="semibold">
                        Participants
                    </Text>
                    <ParticipantList
                        conversation={conversation}
                        participants={participants}
                        preventAssistantModifyOnParticipantIds={preventAssistantModifyOnParticipantIds}
                    />
                </Card>
                <Card className={classes.card}>
                    <Text size={400} weight="semibold">
                        Transcript
                    </Text>
                    <ConversationTranscript conversation={conversation} participants={participants} />
                </Card>
                <Card className={classes.card}>
                    <Text size={400} weight="semibold">
                        Files
                    </Text>
                    <FileUpload conversationId={conversation.id} />
                    <FileList conversationId={conversation.id} />
                </Card>
            </DrawerBody>
        </Drawer>
    );
};
