// Copyright (c) Microsoft. All rights reserved.

import { FirstRunProgressIndicator } from '@fluentui-copilot/react-copilot';
import {
    Button,
    Dialog,
    DialogSurface,
    DialogTrigger,
    Image,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import { Question24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useAppDispatch, useAppSelector } from '../../../redux/app/hooks';
import { setCompletedFirstRun } from '../../../redux/features/app/appSlice';
import { CommandButton } from '../../App/CommandButton';

const useClasses = makeStyles({
    surface: {
        overflow: 'hidden',
        ...shorthands.padding(0),
        ...shorthands.border('none'),
    },
    page: {
        display: 'flex',
        flexDirection: 'column',
    },
    image: {
        height: '324px',
        width: '600px',
    },
    body: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
        ...shorthands.padding(tokens.spacingVerticalXXL, tokens.spacingHorizontalXXL),
    },
    header: {
        fontSize: tokens.fontSizeBase500,
        fontWeight: tokens.fontWeightSemibold,
    },
    content: {
        fontWeight: tokens.fontWeightRegular,
    },
    footer: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
    },
});

export const WorkflowHelp: React.FC = () => {
    const classes = useClasses();
    const { completedFirstRun } = useAppSelector((state) => state.app);
    const dispatch = useAppDispatch();
    const [showHelp, setShowHelp] = React.useState(!completedFirstRun?.workflow);
    const [currentIndex, setCurrentIndex] = React.useState(0);

    const NearButton = () => {
        return currentIndex === 0 ? (
            <DialogTrigger disableButtonEnhancement>
                <Button>Not Now</Button>
            </DialogTrigger>
        ) : (
            <Button onClick={() => setCurrentIndex(currentIndex - 1)}>Previous</Button>
        );
    };

    const FarButton = () => {
        return currentIndex === contentItems.length - 1 ? (
            <DialogTrigger disableButtonEnhancement>
                <Button appearance="primary">Try It Now!</Button>
            </DialogTrigger>
        ) : (
            <Button appearance="primary" onClick={() => setCurrentIndex(currentIndex + 1)}>
                Next
            </Button>
        );
    };

    const handleShowHelp = () => {
        setCurrentIndex(0);
        setShowHelp(true);
    };

    const handleWorkflowHelpClose = () => {
        if (!completedFirstRun?.workflow) {
            dispatch(setCompletedFirstRun({ workflow: true }));
        }
        setShowHelp(false);
    };

    return (
        <Dialog
            open={showHelp}
            onOpenChange={(_event, data) => {
                if (!data.open) {
                    handleWorkflowHelpClose();
                } else {
                    handleShowHelp();
                }
            }}
        >
            <DialogTrigger>
                <CommandButton description="Help" iconOnly icon={<Question24Regular />} />
            </DialogTrigger>
            <DialogSurface className={classes.surface}>
                {/* // TODO: Replace with actual FirstRunExperience component
                // right now it does not show the content on initial load, try again
                // in the future */}
                {/* <FirstRunExperience footer={<FirstRunFooter nearContent={<NearButton />} farContent={<FarButton />} />}>
                    <FirstRunContent
                        image={<Image src="./stories/onenote-01@1x.webp" width={600} height={324} alt="Copilot logo" />}
                        header="Welcome to Copilot"
                        text="Explore new ways to work smarter and faster using the power of AI. Copilot can help you create, catch up, find info buried in files, and more."
                    />
                    <FirstRunContent
                        image={<Image src="./stories/onenote-01@1x.webp" width={600} height={324} alt="Copilot logo" />}
                        header="Welcome to Copilot"
                        text="Explore new ways to work smarter and faster using the power of AI. Copilot can help you create, catch up, find info buried in files, and more."
                    />
                </FirstRunExperience> */}
                <div className={classes.page}>
                    <div className={classes.image}>
                        <Image fit="cover" src={contentItems[currentIndex].image} />
                    </div>
                    <div className={classes.body}>
                        <div className={classes.header}>{contentItems[currentIndex].header}</div>
                        <div className={classes.content}>{contentItems[currentIndex].text}</div>
                        <div className={classes.footer}>
                            <NearButton />
                            <FirstRunProgressIndicator
                                selectedStep={currentIndex}
                                numberOfsteps={contentItems.length}
                            />
                            <FarButton />
                        </div>
                    </div>
                </div>
            </DialogSurface>
        </Dialog>
    );
};

interface ContentItem {
    image: string;
    header: React.ReactNode;
    text: React.ReactNode;
}

const contentItems: ContentItem[] = [
    {
        image: '/assets/experimental-feature.jpg',
        header: 'EXPERIMENTAL FEATURE',
        text: (
            <>
                <p>
                    The workflow feature is currently in development and is missing some of the planned functionality.
                    Feel free to explore, but in the current state it may be possible to create workflows that are
                    invalid or that cause the assistant to get stuck or behave unexpectedly or in a way that is not
                    intended. You can build workflows that may do &quot;weird&quot; things.
                </p>
            </>
        ),
    },
    {
        image: '/assets/workflow-designer-1.jpg',
        header: 'Workflow Designer',
        text: (
            <>
                <p>
                    The workflow designer allows you to create and edit workflows for your assistant. Workflows are a
                    series of steps that the assistant will follow to complete a task. Each step in the workflow defines
                    a state for the assistant to be in, and the assistant will transition between states based on the
                    user&apos;s input and the assistant&apos;s responses.
                </p>
            </>
        ),
    },
    {
        image: '/assets/workflow-designer-1.jpg',
        header: 'Experiment With Instructions',
        text: (
            <>
                <p>
                    Experiment with the natural language instructions you provide within the workflow designer. We have
                    provided some examples to get you started, but it is early enough that we have not yet found best
                    practices for writing these instructions. You may need to experiment to find the right balance of
                    specificity and generality for your use case.
                </p>
            </>
        ),
    },
    {
        image: '/assets/workflow-designer-states.jpg',
        header: 'Workflow States',
        text: (
            <>
                <p>
                    Start by creating additional states for your assistant to be in. Each state allows for overriding
                    assistant configuration to better control the behavior of the assistant for a specific subtask. For
                    example, you can create a state for the assistant to ask for the user&apos;s location, and another
                    state for the assistant to ask for the user&apos;s name.
                </p>
            </>
        ),
    },
    {
        image: '/assets/workflow-designer-outlets.jpg',
        header: 'Workflow State Outlets',
        text: (
            <>
                <p>
                    Each state can have one or more outlets, which are the possible next states that the assistant can
                    transition to. Each outlet has a condition that must be met for the assistant to transition to that
                    state. The condition is expressed in natural language and will be evaluated based on the user&apos;s
                    input and the assistant&apos;s responses.
                </p>
            </>
        ),
    },
    {
        image: '/assets/workflow-designer-transitions.jpg',
        header: 'Workflow State Transitions',
        text: (
            <>
                <p>
                    The assistant will automatically transition between states based on the user&apos;s input and the
                    assistant&apos;s responses. You can also manually transition the assistant to a specific state using
                    the workflow control in the conversation view. This can be useful for testing and debugging your
                    workflow.
                </p>
            </>
        ),
    },
];
