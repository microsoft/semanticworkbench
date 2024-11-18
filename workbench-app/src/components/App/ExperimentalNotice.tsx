// Copyright (c) Microsoft. All rights reserved.

import { FirstRunProgressIndicator } from '@fluentui-copilot/react-copilot';
import {
    Button,
    Dialog,
    DialogSurface,
    DialogTrigger,
    Image,
    Link,
    MessageBar,
    MessageBarActions,
    MessageBarBody,
    MessageBarTitle,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import { DismissRegular } from '@fluentui/react-icons';
import React from 'react';
import { useAppDispatch, useAppSelector } from '../../redux/app/hooks';
import { setCompletedFirstRun, setHideExperimentalNotice } from '../../redux/features/app/appSlice';

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
    warning: {
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

interface ExperimentalNoticeProps {
    className?: string;
    containerAction?: React.ReactElement;
    actions?: React.ReactElement | React.ReactElement[];
}

export const ExperimentalNotice: React.FC<ExperimentalNoticeProps> = (props) => {
    const { className, containerAction, actions } = props;
    const classes = useClasses();
    const { completedFirstRun, hideExperimentalNotice } = useAppSelector((state) => state.app);
    const dispatch = useAppDispatch();
    const [showDialog, setShowDialog] = React.useState(!completedFirstRun?.experimental);
    const [currentIndex, setCurrentIndex] = React.useState(0);

    const NearButton = () => {
        return (
            <Button disabled={currentIndex === 0} onClick={() => setCurrentIndex(currentIndex - 1)}>
                Previous
            </Button>
        );
    };

    const FarButton = () => {
        return currentIndex === contentItems.length - 1 ? (
            <DialogTrigger disableButtonEnhancement>
                <Button appearance="primary">Got it!</Button>
            </DialogTrigger>
        ) : (
            <Button appearance="primary" onClick={() => setCurrentIndex(currentIndex + 1)}>
                Next
            </Button>
        );
    };

    const handleShowDialog = () => {
        setCurrentIndex(0);
        setShowDialog(true);
    };

    const handleDialogClose = () => {
        if (!completedFirstRun?.experimental) {
            dispatch(setCompletedFirstRun({ experimental: true }));
        }
        setShowDialog(false);
    };

    const contentItems: ContentItem[] = [
        {
            image: '/assets/experimental-feature.jpg',
            header: 'EXPERIMENTAL FEATURE',
            text: (
                <>
                    <p>
                        This application is a development tool for exploring ideas and concepts. It is not intended for
                        production use. The application may contain experimental features that are not fully tested and
                        may not be fully functional. Use at your own risk.
                    </p>
                    <p className={classes.warning}>
                        Data is not guaranteed to be secure or private. Do not use real or sensitive data in this
                        application. Do not use this application to collect, store, or process personal data. Any
                        information you enter into this application may be visible to others and may be lost or
                        corrupted. Do not upload or input anything you would not put on a company-wide file share.
                    </p>
                </>
            ),
        },
        {
            image: '/assets/workflow-designer-1.jpg',
            header: 'FREQUENT CHANGES',
            text: (
                <>
                    <p>
                        This application is under active development and <em>will</em> change frequently. Features may
                        be added, removed, or changed at any time. The application may be unavailable or unstable during
                        updates. Some or all data <em>will be</em> lost or corrupted during some of these updates. Use
                        at your own risk.
                    </p>
                    <p className={classes.warning}>
                        If you need something more stable or want to leverage this work to build your own demos,
                        consider checking out a specific commit of the code and running it either locally or in your own
                        environment.
                    </p>
                </>
            ),
        },
    ];

    const defaultContainerAction = (
        <Button
            appearance="transparent"
            onClick={() => dispatch(setHideExperimentalNotice(true))}
            icon={<DismissRegular />}
        />
    );

    if (hideExperimentalNotice) {
        return null;
    }

    return (
        <Dialog
            open={showDialog}
            modalType={!completedFirstRun?.experimental ? 'alert' : undefined}
            onOpenChange={(_event, data) => {
                if (!data.open) {
                    handleDialogClose();
                } else {
                    handleShowDialog();
                }
            }}
        >
            <DialogTrigger>
                <MessageBar className={className} intent="warning" layout="multiline">
                    <MessageBarBody>
                        <MessageBarTitle>Experimental App Reminder:</MessageBarTitle>
                        features <em>will</em> break, data <em>will</em> be lost, data <em>is not</em> secure. &nbsp;
                        <Link>[details]</Link>
                    </MessageBarBody>
                    <MessageBarActions containerAction={containerAction ?? defaultContainerAction}>
                        {actions}
                    </MessageBarActions>
                </MessageBar>
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
