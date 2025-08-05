# workbench-app/src

[collect-files]

**Search:** ['workbench-app/src']
**Exclude:** ['.venv', 'node_modules', '*.lock', '.git', '__pycache__', '*.pyc', '*.ruff_cache', 'logs', 'output', '*.svg', '*.png', '*.jpg']
**Include:** ['package.json', 'tsconfig.json', 'vite.config.ts']
**Date:** 8/5/2025, 4:43:26 PM
**Files:** 207

=== File: workbench-app/src/Constants.ts ===
// Allow static build of React code to access env vars
// SEE https://create-react-app.dev/docs/title-and-meta-tags/#injecting-data-from-the-server-into-the-page
const serviceUrl =
    window.VITE_SEMANTIC_WORKBENCH_SERVICE_URL && window.VITE_SEMANTIC_WORKBENCH_SERVICE_URL.startsWith('https://')
        ? window.VITE_SEMANTIC_WORKBENCH_SERVICE_URL
        : import.meta.env.VITE_SEMANTIC_WORKBENCH_SERVICE_URL
        ? import.meta.env.VITE_SEMANTIC_WORKBENCH_SERVICE_URL
        : 'http://127.0.0.1:3000';

export const Constants = {
    app: {
        name: 'Semantic Workbench',
        defaultTheme: 'light',
        defaultBrand: 'local',
        autoScrollThreshold: 100,
        maxContentWidth: 900,
        maxInputLength: 2000000, // 2M tokens, effectively unlimited
        conversationListMinWidth: '250px',
        conversationHistoryMinWidth: '270px',
        resizableCanvasDrawerMinWidth: '200px',
        get resizableCanvasDrawerMaxWidth() {
            return `calc(100vw - ${this.conversationListMinWidth} - ${this.conversationHistoryMinWidth})`;
        },
        defaultChatWidthPercent: 33,
        maxFileAttachmentsPerMessage: 10,
        loaderDelayMs: 100,
        responsiveBreakpoints: {
            chatCanvas: '900px',
        },
        speechIdleTimeoutMs: 4000,
        azureSpeechTokenRefreshIntervalMs: 540000, // 540000 ms = 9 minutes
        globalToasterId: 'global',
    },
    service: {
        defaultEnvironmentId: 'local',
        environments: [
            {
                id: 'local',
                name: 'Semantic Workbench backend service on localhost or GitHub Codespaces',
                // Can be overridden by env var VITE_SEMANTIC_WORKBENCH_SERVICE_URL
                url: serviceUrl,
                brand: 'light',
            },
            // {
            //     id: 'remote',
            //     name: 'Remote',
            //     url: 'https://<YOUR WORKBENCH DEPLOYMENT>.azurewebsites.net',
            //     brand: 'orange',
            // },
        ],
    },
    assistantCategories: {
        Recommended: ['explorer-assistant.made-exploration-team', 'guided-conversation-assistant.made-exploration'],
        'Example Implementations': [
            'python-01-echo-bot.workbench-explorer',
            'python-02-simple-chatbot.workbench-explorer',
            'python-03-multimodel-chatbot.workbench-explorer',
            'canonical-assistant.semantic-workbench',
        ],
        Experimental: ['prospector-assistant.made-exploration'],
    },
    msal: {
        method: 'redirect', // 'redirect' | 'popup'
        auth: {
            // Semantic Workbench GitHub sample app registration
            // The same value is set also in AuthSettings in
            // "semantic_workbench_service.config.py" in the backend
            // Can be overridden by env var VITE_SEMANTIC_WORKBENCH_CLIENT_ID
            clientId: import.meta.env.VITE_SEMANTIC_WORKBENCH_CLIENT_ID || '22cb77c3-ca98-4a26-b4db-ac4dcecba690',

            // Specific tenant only:     'https://login.microsoftonline.com/<tenant>/',
            // Personal accounts only:   'https://login.microsoftonline.com/consumers',
            // Work + School accounts:   'https://login.microsoftonline.com/organizations',
            // Work + School + Personal: 'https://login.microsoftonline.com/common'
            // Can be overridden by env var VITE_SEMANTIC_WORKBENCH_AUTHORITY
            authority: import.meta.env.VITE_SEMANTIC_WORKBENCH_AUTHORITY || 'https://login.microsoftonline.com/common',
        },
        cache: {
            cacheLocation: 'localStorage',
            storeAuthStateInCookie: false,
        },
        // Enable the ones you need
        msGraphScopes: [
            // 'Calendars.ReadWrite',
            // 'Calendars.Read.Shared',
            // 'ChannelMessage.Read.All',
            // 'Chat.Read',
            // 'Contacts.Read',
            // 'Contacts.Read.Shared',
            // 'email',
            // 'Files.Read',
            // 'Files.Read.All',
            // 'Files.Read.Selected',
            // 'Group.Read.All',
            // 'Mail.Read',
            // 'Mail.Read.Shared',
            // 'MailboxSettings.Read',
            // 'Notes.Read',
            // 'Notes.Read.All',
            // 'offline_access',
            // 'OnlineMeetingArtifact.Read.All',
            // 'OnlineMeetings.Read',
            'openid',
            // 'People.Read',
            // 'Presence.Read.All',
            'offline_access',
            'profile',
            // 'Sites.Read.All',
            // 'Tasks.Read',
            // 'Tasks.Read.Shared',
            // 'TeamSettings.Read.All',
            'User.Read',
            // 'User.Read.all',
            // 'User.ReadBasic.All',
        ],
    },
    debug: {
        root: 'semantic-workbench',
    },
};


=== File: workbench-app/src/Root.tsx ===
import { Link, Popover, PopoverSurface, PopoverTrigger, Toaster } from '@fluentui/react-components';
import debug from 'debug';
import React from 'react';
import { Outlet } from 'react-router-dom';
import { Constants } from './Constants';
import useDragAndDrop from './libs/useDragAndDrop';
import { useKeySequence } from './libs/useKeySequence';
import { useNotify } from './libs/useNotify';
import { useAppDispatch, useAppSelector } from './redux/app/hooks';
import { setIsDraggingOverBody, toggleDevMode } from './redux/features/app/appSlice';

const log = debug(Constants.debug.root).extend('Root');

export const Root: React.FC = () => {
    const isDraggingOverBody = useAppSelector((state) => state.app.isDraggingOverBody);
    const dispatch = useAppDispatch();
    useKeySequence(
        [
            'ArrowUp',
            'ArrowUp',
            'ArrowDown',
            'ArrowDown',
            'ArrowLeft',
            'ArrowRight',
            'ArrowLeft',
            'ArrowRight',
            'b',
            'a',
            'Enter',
        ],
        () => dispatch(toggleDevMode()),
    );
    const { notifyError } = useNotify();

    const globalErrorHandler = React.useCallback(
        (event: PromiseRejectionEvent) => {
            log('Unhandled promise rejection', event.reason);
            notifyError({
                id: ['unhandledrejection', event.reason.message, event.reason.stack].join(':'),
                title: 'Unhandled error',
                message: event.reason.message,
                additionalActions: [
                    <Popover key="popover">
                        <PopoverTrigger disableButtonEnhancement>
                            <Link>More info</Link>
                        </PopoverTrigger>
                        <PopoverSurface>
                            <pre>{event.reason.stack}</pre>
                        </PopoverSurface>
                    </Popover>,
                ],
            });
        },
        [notifyError],
    );

    React.useEffect(() => {
        // add a global error handler to catch unhandled promise rejections
        window.addEventListener('unhandledrejection', globalErrorHandler);

        return () => {
            window.removeEventListener('unhandledrejection', globalErrorHandler);
        };
    }, [globalErrorHandler]);

    // ignore file drop events at the document level as this prevents the browser from
    // opening the file in the window if the drop event is not handled or the user misses
    const ignoreFileDrop = true;
    const isDraggingOver = useDragAndDrop(document.body, log, ignoreFileDrop);

    React.useEffect(() => {
        if (isDraggingOver !== isDraggingOverBody) {
            dispatch(setIsDraggingOverBody(isDraggingOver));
        }
    }, [isDraggingOver, isDraggingOverBody, dispatch]);

    return (
        <>
            <Outlet />
            <Toaster toasterId={Constants.app.globalToasterId} pauseOnHover pauseOnWindowBlur />
        </>
    );
};


=== File: workbench-app/src/components/App/AppFooter.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Caption1, Link, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'row',
        backgroundColor: tokens.colorNeutralBackgroundAlpha,
        alignItems: 'center',
        justifyContent: 'center',
        gap: tokens.spacingVerticalM,
        ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
    },
});

export const AppFooter: React.FC = () => {
    const classes = useClasses();

    return (
        <div className={classes.root}>
            <Link href="https://go.microsoft.com/fwlink/?LinkId=521839" target="_blank">
                Privacy &amp; Cookies
            </Link>{' '}
            |{' '}
            <Link href="https://go.microsoft.com/fwlink/?linkid=2259814" target="_blank">
                Consumer Health Privacy
            </Link>{' '}
            |{' '}
            <Link href="https://go.microsoft.com/fwlink/?LinkID=246338" target="_blank">
                Terms of Use
            </Link>{' '}
            |{' '}
            <Link
                href="https://www.microsoft.com/en-us/legal/intellectualproperty/Trademarks/EN-US.aspx"
                target="_blank"
            >
                Trademarks
            </Link>{' '}
            |{' '}
            <Link href="https://github.com/microsoft/semanticworkbench" target="_blank">
                @GitHub
            </Link>{' '}
            | <Caption1>© Microsoft 2024</Caption1>
        </div>
    );
};


=== File: workbench-app/src/components/App/AppHeader.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button, Title3, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import { ArrowLeft24Regular, Home24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Link } from 'react-router-dom';
import { AppMenu } from './AppMenu';
import { ErrorListFromAppState } from './ErrorListFromAppState';
import { ProfileSettings } from './ProfileSettings';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: tokens.colorNeutralBackground1,
    },
    content: {
        display: 'flex',
        flexDirection: 'row',
        backgroundColor: tokens.colorBrandBackground,
        alignItems: 'center',
        justifyContent: 'space-between',
        ...shorthands.padding(tokens.spacingVerticalS),
    },
    title: {
        color: tokens.colorNeutralForegroundOnBrand,
    },
    actions: {
        display: 'flex',
        flexDirection: 'row',
        gap: tokens.spacingHorizontalS,
    },
});

interface AppHeaderProps {
    title: string | React.ReactNode;
    actions?: {
        items: React.ReactNode[];
        replaceExisting?: boolean;
        hideProfileSettings?: boolean;
    };
}

export const AppHeader: React.FC<AppHeaderProps> = (props) => {
    const { title, actions } = props;
    const classes = useClasses();

    const actionItems = [];

    // Custom actions from the caller
    if (actions && actions?.items.length > 0) {
        actionItems.push(...actions.items.map((item, index) => <React.Fragment key={index}>{item}</React.Fragment>));
    }

    // Default navigation and other global actions
    if (!actions?.replaceExisting) {
        // Back button
        if (window.history.length > 1) {
            actionItems.push(<Button key="back" icon={<ArrowLeft24Regular />} onClick={() => window.history.back()} />);
        }

        // Home button
        if (window.location.pathname !== '/') {
            actionItems.push(
                <Link key="home" to="/">
                    <Button icon={<Home24Regular />} />
                </Link>,
            );
        }

        // Global menu
        actionItems.push(<AppMenu key="menu" />);
    }

    // Display current user's profile settings
    if (!actions?.hideProfileSettings) {
        actionItems.push(<ProfileSettings key="profile" />);
    }

    return (
        <div className={classes.root}>
            <div className={classes.content}>
                {title && typeof title === 'string' ? <Title3 className={classes.title}>{title}</Title3> : title}
                <div className={classes.actions}>{actionItems}</div>
            </div>
            <ErrorListFromAppState />
        </div>
    );
};


=== File: workbench-app/src/components/App/AppMenu.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button, Menu, MenuItem, MenuList, MenuPopover, MenuTrigger } from '@fluentui/react-components';
import { MoreHorizontal24Regular, Settings24Regular, Share24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useNavigate } from 'react-router-dom';

export const AppMenu: React.FC = () => {
    const navigate = useNavigate();

    return (
        <Menu>
            <MenuTrigger disableButtonEnhancement>
                <Button icon={<MoreHorizontal24Regular />} />
            </MenuTrigger>
            <MenuPopover>
                <MenuList>
                    <MenuItem
                        icon={<Share24Regular />}
                        onClick={() => {
                            navigate('/shares');
                        }}
                    >
                        Shares
                    </MenuItem>
                    <MenuItem
                        icon={<Settings24Regular />}
                        onClick={() => {
                            navigate('/settings');
                        }}
                    >
                        Settings
                    </MenuItem>
                </MenuList>
            </MenuPopover>
        </Menu>
    );
};


=== File: workbench-app/src/components/App/AppView.tsx ===
// Copyright (c) Microsoft. All rights reserved.
import { makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Constants } from '../../Constants';
import { useAppSelector } from '../../redux/app/hooks';
import { AppFooter } from './AppFooter';
import { AppHeader } from './AppHeader';

const useClasses = makeStyles({
    documentBody: {
        // backgroundImage: `url('/assets/background-1.jpg')`,
        backgroundImage: `linear-gradient(to right, #FFFFFF, #E6EEFF)`,
    },
    root: {
        display: 'grid',
        gridTemplateRows: 'auto 1fr auto',
        height: '100vh',
    },
    content: {
        overflowY: 'auto',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        maxWidth: `${Constants.app.maxContentWidth}px`,
        boxSizing: 'border-box',
        width: '100%',
        gap: tokens.spacingVerticalM,
        ...shorthands.margin('0', 'auto'),
        ...shorthands.padding(tokens.spacingVerticalM),
    },
    fullSize: {
        ...shorthands.padding(0),
        maxWidth: '100%',
    },
});

interface AppViewProps {
    title: string | React.ReactNode;
    actions?: {
        items: React.ReactNode[];
        replaceExisting?: boolean;
        hideProfileSettings?: boolean;
    };
    fullSizeContent?: boolean;
    children?: React.ReactNode;
}

export const AppView: React.FC<AppViewProps> = (props) => {
    const { title, actions, fullSizeContent, children } = props;
    const classes = useClasses();
    const completedFirstRun = useAppSelector((state) => state.app.completedFirstRun);
    const navigate = useNavigate();

    React.useLayoutEffect(() => {
        document.body.className = classes.documentBody;
        return () => {
            document.body.className = '';
        };
    }, [classes.documentBody]);

    React.useEffect(() => {
        if (!completedFirstRun?.app && window.location.pathname !== '/terms') {
            navigate('/terms', { state: { redirectTo: window.location.pathname } });
        }
    }, [completedFirstRun, navigate]);

    return (
        <div id="app" className={classes.root}>
            <AppHeader title={title} actions={actions} />
            <div className={fullSizeContent ? mergeClasses(classes.content, classes.fullSize) : classes.content}>
                {children}
            </div>
            <AppFooter />
        </div>
    );
};


=== File: workbench-app/src/components/App/CodeLabel.tsx ===
import { makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';

const useClasses = makeStyles({
    root: {
        ...shorthands.border(tokens.strokeWidthThin, 'solid', tokens.colorNeutralStroke2),
        borderRadius: tokens.borderRadiusMedium,
        backgroundColor: tokens.colorNeutralBackground3,
        ...shorthands.padding(tokens.spacingVerticalXXS, tokens.spacingHorizontalS),
    },
});

interface CodeLabelProps {
    children?: React.ReactNode;
}

export const CodeLabel: React.FC<CodeLabelProps> = (props) => {
    const { children } = props;
    const classes = useClasses();

    return <span className={classes.root}>{children}</span>;
};


=== File: workbench-app/src/components/App/CommandButton.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button, ButtonProps, makeStyles, mergeClasses, tokens, ToolbarButton } from '@fluentui/react-components';
import React from 'react';
import { DialogControl, DialogControlContent } from './DialogControl';
import { TooltipWrapper } from './TooltipWrapper';

const useClasses = makeStyles({
    menuItem: {
        paddingLeft: tokens.spacingHorizontalXS,
        paddingRight: tokens.spacingHorizontalXS,
        justifyContent: 'flex-start',
        fontWeight: 'normal',
    },
});

type CommandButtonProps = ButtonProps & {
    className?: string;
    label?: string;
    description?: string;
    onClick?: () => void;
    dialogContent?: DialogControlContent;
    open?: boolean;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
    simulateMenuItem?: boolean;
};

export const CommandButton: React.FC<CommandButtonProps> = (props) => {
    const {
        as,
        className,
        disabled,
        icon,
        label,
        description,
        onClick,
        dialogContent,
        open,
        iconOnly,
        asToolbarButton,
        appearance,
        size,
        simulateMenuItem,
    } = props;
    const classes = useClasses();

    let commandButton = null;

    if (dialogContent?.trigger) {
        if (description) {
            commandButton = <TooltipWrapper content={description}>{dialogContent.trigger}</TooltipWrapper>;
        } else {
            commandButton = dialogContent.trigger;
        }
    } else if (simulateMenuItem) {
        commandButton = (
            <Button
                as={as}
                className={mergeClasses(classes.menuItem, className)}
                appearance={appearance ?? 'subtle'}
                size={size}
                disabled={disabled}
                icon={icon}
                onClick={onClick}
            >
                {label}
            </Button>
        );
    } else if (iconOnly) {
        if (description) {
            commandButton = (
                <TooltipWrapper content={description}>
                    <Button
                        as={as}
                        className={className}
                        appearance={appearance}
                        size={size}
                        disabled={disabled}
                        icon={icon}
                        onClick={onClick}
                    />
                </TooltipWrapper>
            );
        } else {
            commandButton = (
                <Button
                    as={as}
                    className={className}
                    appearance={appearance}
                    size={size}
                    disabled={disabled}
                    icon={icon}
                    onClick={onClick}
                />
            );
        }
    } else if (asToolbarButton) {
        commandButton = (
            <ToolbarButton className={className} disabled={disabled} icon={icon} onClick={onClick}>
                {label}
            </ToolbarButton>
        );
    } else {
        commandButton = (
            <Button
                as={as}
                className={className}
                disabled={disabled}
                icon={icon}
                appearance={appearance}
                size={size}
                onClick={onClick}
            >
                {label}
            </Button>
        );
        if (description) {
            commandButton = <TooltipWrapper content={description}>{commandButton}</TooltipWrapper>;
        }
    }

    if (!dialogContent) {
        return commandButton;
    }

    return (
        <DialogControl
            trigger={commandButton}
            classNames={dialogContent.classNames}
            open={open}
            title={dialogContent.title}
            content={dialogContent.content}
            closeLabel={dialogContent.closeLabel}
            hideDismissButton={dialogContent.hideDismissButton}
            additionalActions={dialogContent.additionalActions}
            onOpenChange={dialogContent.onOpenChange}
        />
    );
};


=== File: workbench-app/src/components/App/ConfirmLeave.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { unstable_usePrompt } from 'react-router-dom';

interface ConfirmLeaveProps {
    isDirty: boolean;
    onConfirm?: () => void;
}

export const ConfirmLeave: React.FC<ConfirmLeaveProps> = (props) => {
    const { isDirty } = props;

    const alertUser = (event: BeforeUnloadEvent) => {
        event.preventDefault();
        event.returnValue = '';
    };

    unstable_usePrompt({
        when: isDirty,
        message: 'Changes you made may not be saved.',
    });

    React.useEffect(() => {
        if (isDirty) {
            window.addEventListener('beforeunload', alertUser);
        } else {
            window.removeEventListener('beforeunload', alertUser);
        }
        return () => {
            window.removeEventListener('beforeunload', alertUser);
        };
    }, [isDirty]);

    return null;
};


=== File: workbench-app/src/components/App/ContentExport.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { ArrowDownload24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useExportUtility } from '../../libs/useExportUtility';
import { CommandButton } from './CommandButton';

interface ContentExportProps {
    id: string;
    contentTypeLabel: string;
    exportFunction: (id: string) => Promise<{ blob: Blob; filename: string }>;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const ContentExport: React.FC<ContentExportProps> = (props) => {
    const { id, contentTypeLabel, exportFunction, iconOnly, asToolbarButton } = props;
    const { exportContent } = useExportUtility();
    const [exporting, setExporting] = React.useState(false);

    const handleExport = React.useCallback(async () => {
        if (exporting) {
            return;
        }
        setExporting(true);

        try {
            await exportContent(id, exportFunction);
        } finally {
            setExporting(false);
        }
    }, [exporting, exportContent, id, exportFunction]);

    return (
        <CommandButton
            description={`Export ${contentTypeLabel}`}
            icon={<ArrowDownload24Regular />}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
            label={exporting ? 'Exporting...' : 'Export'}
            onClick={handleExport}
            disabled={exporting}
        />
    );
};


=== File: workbench-app/src/components/App/ContentImport.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { ArrowUploadRegular } from '@fluentui/react-icons';
import React from 'react';
import { CommandButton } from '../App/CommandButton';

interface ContentImportProps<T> {
    contentTypeLabel: string;
    importFunction: (file: File) => Promise<T>;
    onImport?: (value: T) => void;
    onError?: (error: Error) => void;
    disabled?: boolean;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
    appearance?: 'primary' | 'secondary' | 'outline' | 'subtle' | 'transparent';
    size?: 'small' | 'medium' | 'large';
}

export const ContentImport = <T extends unknown>(props: ContentImportProps<T>) => {
    const {
        contentTypeLabel,
        importFunction,
        onImport,
        onError,
        disabled,
        iconOnly,
        asToolbarButton,
        appearance,
        size,
    } = props;
    const [uploading, setUploading] = React.useState(false);
    const fileInputRef = React.useRef<HTMLInputElement>(null);

    const onFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files) {
            setUploading(true);
            try {
                const file = event.target.files[0];
                const content = await importFunction(file);
                onImport?.(content);
            } catch (error) {
                onError?.(error as Error);
            }
            setUploading(false);
        }

        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const onUpload = async () => {
        fileInputRef.current?.click();
    };

    return (
        <div>
            <input hidden ref={fileInputRef} type="file" onChange={onFileChange} />
            <CommandButton
                disabled={uploading || disabled}
                description={`Import ${contentTypeLabel}`}
                icon={<ArrowUploadRegular />}
                iconOnly={iconOnly}
                asToolbarButton={asToolbarButton}
                appearance={appearance}
                size={size}
                label={uploading ? 'Uploading...' : 'Import'}
                onClick={onUpload}
            />
        </div>
    );
};


=== File: workbench-app/src/components/App/CopyButton.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button, Slot, makeStyles, tokens } from '@fluentui/react-components';
import { Checkmark24Regular, CopyRegular } from '@fluentui/react-icons';
import React from 'react';
import { TooltipWrapper } from './TooltipWrapper';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        alignItems: 'center',
        gap: tokens.spacingHorizontalS,
    },
});

interface CopyButtonProps {
    data: string | (() => Promise<string>);
    icon?: Slot<'span'>;
    appearance?: 'secondary' | 'primary' | 'outline' | 'subtle' | 'transparent';
    tooltip?: string;
    size?: 'small' | 'medium' | 'large';
}

export const CopyButton: React.FC<CopyButtonProps> = (props) => {
    const { data, icon, appearance, tooltip, size } = props;
    const classes = useClasses();
    const [copying, setCopying] = React.useState(false);
    const [copied, setCopied] = React.useState(false);

    const handleCopy = React.useCallback(async () => {
        setCopying(true);
        try {
            const text = typeof data === 'function' ? await data() : data;
            await navigator.clipboard.writeText(text);
        } finally {
            setCopying(false);
        }
        setCopied(true);
        setTimeout(() => {
            setCopied(false);
        }, 2000);
    }, [data, setCopying]);

    const copyIcon = React.useCallback(() => {
        return copied ? <Checkmark24Regular /> : icon ?? <CopyRegular />;
    }, [copied, icon]);

    const button = (
        <Button as="a" appearance={appearance} size={size} disabled={copying} icon={copyIcon()} onClick={handleCopy} />
    );

    const content = tooltip ? <TooltipWrapper content={tooltip}>{button}</TooltipWrapper> : button;

    return <div className={classes.root}>{content}</div>;
};


=== File: workbench-app/src/components/App/DialogControl.tsx ===
import {
    Button,
    Dialog,
    DialogActions,
    DialogBody,
    DialogContent,
    DialogOpenChangeData,
    DialogOpenChangeEvent,
    DialogSurface,
    DialogTitle,
    DialogTrigger,
    makeStyles,
    mergeClasses,
    tokens,
} from '@fluentui/react-components';
import React from 'react';

const useClasses = makeStyles({
    dialogContent: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
});

export interface DialogControlContent {
    open?: boolean;
    defaultOpen?: boolean;
    trigger?: React.ReactElement;
    classNames?: {
        dialogSurface?: string;
        dialogContent?: string;
    };
    title?: string;
    content?: React.ReactNode;
    closeLabel?: string;
    hideDismissButton?: boolean;
    dismissButtonDisabled?: boolean;
    additionalActions?: React.ReactElement[];
    onOpenChange?: (event: DialogOpenChangeEvent, data: DialogOpenChangeData) => void;
}

export const DialogControl: React.FC<DialogControlContent> = (props) => {
    const {
        open,
        defaultOpen,
        trigger,
        classNames,
        title,
        content,
        closeLabel,
        dismissButtonDisabled,
        hideDismissButton,
        additionalActions,
        onOpenChange,
    } = props;

    const classes = useClasses();

    return (
        <Dialog open={open} defaultOpen={defaultOpen} onOpenChange={onOpenChange} inertTrapFocus={true}>
            <DialogTrigger disableButtonEnhancement>{trigger}</DialogTrigger>
            <DialogSurface className={classNames?.dialogSurface}>
                <DialogBody>
                    {title && <DialogTitle>{title}</DialogTitle>}
                    {content && (
                        <DialogContent className={mergeClasses(classes.dialogContent, classNames?.dialogContent)}>
                            {content}
                        </DialogContent>
                    )}
                    <DialogActions fluid>
                        {!hideDismissButton && (
                            <DialogTrigger disableButtonEnhancement action="close">
                                <Button
                                    appearance={additionalActions ? 'secondary' : 'primary'}
                                    disabled={dismissButtonDisabled}
                                >
                                    {closeLabel ?? 'Close'}
                                </Button>
                            </DialogTrigger>
                        )}
                        {additionalActions}
                    </DialogActions>
                </DialogBody>
            </DialogSurface>
        </Dialog>
    );
};


=== File: workbench-app/src/components/App/DynamicIframe.tsx ===
import React from 'react';

interface DynamicIframeProps {
    source: string;
}

const DynamicIframe: React.FC<DynamicIframeProps> = (props) => {
    const { source } = props;
    const iframeRef = React.useRef<HTMLIFrameElement>(null);

    React.useEffect(() => {
        if (!iframeRef.current) {
            return;
        }

        const iframe = iframeRef.current;
        const contentWindow = iframe.contentWindow;

        if (!contentWindow) {
            return;
        }

        const resizeIframe = () => {
            const body = contentWindow.document.body;
            const html = contentWindow.document.documentElement;

            // Calculate the height including margins, padding, etc.
            const height = Math.max(
                body.scrollHeight,
                body.offsetHeight,
                html.clientHeight,
                html.scrollHeight,
                html.offsetHeight,
            );

            iframe.style.height = height + 'px';
        };

        const onLoad = () => {
            resizeIframe();

            const observer = new MutationObserver(resizeIframe);
            observer.observe(contentWindow.document.body, {
                childList: true,
                subtree: true,
                attributes: true,
            });
        };

        if (iframe) {
            iframe.addEventListener('load', onLoad);
        }

        return () => {
            if (iframe) {
                iframe.removeEventListener('load', onLoad);
            }
        };
    }, []);

    return (
        <iframe
            ref={iframeRef}
            srcDoc={source}
            style={{ width: '100%', border: 'none' }}
            title="Dynamic Iframe"
        ></iframe>
    );
};

export default DynamicIframe;


=== File: workbench-app/src/components/App/ErrorListFromAppState.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { MessageBarGroup, makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { useAppDispatch, useAppSelector } from '../../redux/app/hooks';
import { RootState } from '../../redux/app/store';
import { removeError } from '../../redux/features/app/appSlice';
import { ErrorMessageBar } from './ErrorMessageBar';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: tokens.colorPaletteRedBackground2,
        gap: tokens.spacingVerticalM,
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
    },
});

interface ErrorListFromAppStateProps {
    className?: string;
}

export const ErrorListFromAppState: React.FC<ErrorListFromAppStateProps> = (props) => {
    const { className } = props;
    const classes = useClasses();
    const errors = useAppSelector((state: RootState) => state.app.errors);
    const dispatch = useAppDispatch();

    if (!errors || errors.length === 0) {
        return null;
    }

    return (
        <MessageBarGroup className={mergeClasses(classes.root, className)}>
            {errors.map((error) => (
                <ErrorMessageBar
                    key={error.id}
                    title={error.title}
                    error={error.message}
                    onDismiss={() => dispatch(removeError(error.id))}
                />
            ))}
        </MessageBarGroup>
    );
};


=== File: workbench-app/src/components/App/ErrorMessageBar.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button, MessageBar, MessageBarActions, MessageBarBody, MessageBarTitle } from '@fluentui/react-components';
import { DismissRegular } from '@fluentui/react-icons';
import React from 'react';
import { Utility } from '../../libs/Utility';

interface ErrorMessageBarProps {
    title?: string;
    error?: Record<string, any> | string;
    onDismiss?: () => void;
}

export const ErrorMessageBar: React.FC<ErrorMessageBarProps> = (props) => {
    const { title, error, onDismiss } = props;

    let message = Utility.errorToMessageString(error);
    if (!title && !message) {
        message = 'An unknown error occurred';
    }

    return (
        <MessageBar intent="error" layout="multiline">
            <MessageBarBody>
                <MessageBarTitle>{title ?? 'Error'}:</MessageBarTitle>
                {message}
            </MessageBarBody>
            {onDismiss && (
                <MessageBarActions
                    containerAction={<Button appearance="transparent" icon={<DismissRegular />} onClick={onDismiss} />}
                />
            )}
        </MessageBar>
    );
};


=== File: workbench-app/src/components/App/ExperimentalNotice.tsx ===
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


=== File: workbench-app/src/components/App/FormWidgets/BaseModelEditorWidget.tsx ===
import {
    Accordion,
    AccordionHeader,
    AccordionItem,
    AccordionItemValue,
    AccordionPanel,
    AccordionToggleEventHandler,
    Button,
    Dropdown,
    Field,
    Input,
    makeStyles,
    Option,
    shorthands,
    Text,
    Textarea,
    tokens,
} from '@fluentui/react-components';
import { Add16Regular, Delete16Regular, Edit16Regular } from '@fluentui/react-icons';
import { findSchemaDefinition, WidgetProps } from '@rjsf/utils';
import React, { useRef } from 'react';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalXXS,
    },
    properties: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalL,
        ...shorthands.margin(tokens.spacingVerticalS, 0),
    },
    property: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalL,
        padding: tokens.spacingHorizontalM,
        border: '1px solid #ccc',
        borderRadius: tokens.borderRadiusMedium,
    },
    addNestedProperty: {
        ...shorthands.margin(tokens.spacingVerticalS, 0, tokens.spacingVerticalS, tokens.spacingHorizontalM),
    },
    keyRow: {
        display: 'flex',
        alignItems: 'center',
        gap: tokens.spacingHorizontalS,
    },
});

interface ModelSchema {
    properties?: {
        [key: string]: {
            title?: string;
            type?: string;
            description?: string;
            enum?: string[]; // For handling dropdowns
            properties?: ModelSchema['properties']; // For nested objects
            items?: { type: string }; // For handling arrays (lists)
        };
    };
}

const valueToModelSchema = (value: any): ModelSchema => {
    // if value is a string, parse it as JSON to get the schema
    // traverse the schema and replace all $refs with the actual definition
    const schema = JSON.parse(value);
    const traverse = (obj: any) => {
        if (obj && typeof obj === 'object') {
            if (obj.$ref) {
                return findSchemaDefinition(obj.$ref, schema);
            }
            Object.entries(obj).forEach(([key, value]) => {
                obj[key] = traverse(value);
            });
        }
        return obj;
    };
    return traverse(schema);
};

const modelSchemaToValue = (modelSchema: ModelSchema): string => {
    // convert the model schema back to a string
    // traverse the schema and replace all definitions with $refs
    const refs = new Map<string, string>();
    const traverse = (obj: any) => {
        if (obj && typeof obj === 'object') {
            Object.entries(obj).forEach(([key, value]) => {
                obj[key] = traverse(value);
            });
        }
        if (obj && obj.$id) {
            refs.set(obj.$id, obj);
            return { $ref: obj.$id };
        }
        return obj;
    };
    const schema = traverse(modelSchema);
    refs.forEach((value, key) => {
        schema[key] = value;
    });
    return JSON.stringify(schema);
};

export const BaseModelEditorWidget: React.FC<WidgetProps> = (props) => {
    const { label, value, onChange } = props;
    const classes = useClasses();
    const inputRef = useRef<HTMLInputElement | null>(null);
    const [openItems, setOpenItems] = React.useState<AccordionItemValue[]>([]);

    // Define the schema type
    const [modelSchema, setModelSchema] = React.useState<ModelSchema>(() => valueToModelSchema(value));

    const [editingKey, setEditingKey] = React.useState<{ oldKey: string; newKey: string } | null>(null);

    // Update the modelSchema when the value changes
    React.useEffect(() => {
        setModelSchema(valueToModelSchema(value));
    }, [value]);

    // Helper function to update the modelSchema
    const handleSchemaChange = (
        keyPath: string,
        propertyKey: keyof NonNullable<ModelSchema['properties']>[string],
        newValue: any,
    ) => {
        const keys = keyPath.split('.');
        const updatedModelSchema = { ...modelSchema };
        let current = updatedModelSchema.properties;

        for (let i = 0; i < keys.length - 1; i++) {
            if (!current || !current[keys[i]]) return;
            current = current[keys[i]].properties;
        }

        if (current && current[keys[keys.length - 1]]) {
            current[keys[keys.length - 1]] = {
                ...current[keys[keys.length - 1]],
                [propertyKey]: newValue,
            };
        }

        setModelSchema(updatedModelSchema);
        onChange(modelSchemaToValue(updatedModelSchema));
    };

    // Helper function to update the property key
    const handleKeyEditStart = (oldKey: string) => {
        const keySegments = oldKey.split('.');
        const displayedKey = keySegments[keySegments.length - 1]; // Use only the last part for editing

        setEditingKey({ oldKey, newKey: displayedKey });
        setTimeout(() => inputRef.current?.focus(), 0);
    };

    const handleKeyEditChange = (newKey: string) => {
        setEditingKey((prev) => (prev ? { ...prev, newKey } : null));
    };

    const reconstructPropertiesWithUpdatedKey = (
        properties: { [key: string]: any },
        oldKey: string,
        newKey: string,
    ) => {
        const updatedProperties: { [key: string]: any } = {};

        // Reconstruct the properties object maintaining the original order
        Object.entries(properties).forEach(([key, value]) => {
            if (key === oldKey) {
                updatedProperties[newKey] = value; // Replace the old key with the new key
            } else {
                updatedProperties[key] = value;
            }
        });

        return updatedProperties;
    };

    const handleKeyEditEnd = () => {
        if (editingKey && modelSchema.properties) {
            const { oldKey, newKey } = editingKey;
            const keySegments = oldKey.split('.');

            if (newKey !== keySegments[keySegments.length - 1] && newKey.trim() !== '') {
                const updatedModelSchema = { ...modelSchema };

                if (keySegments.length === 1) {
                    // Handle root-level key
                    if (updatedModelSchema.properties) {
                        updatedModelSchema.properties = reconstructPropertiesWithUpdatedKey(
                            updatedModelSchema.properties,
                            oldKey,
                            newKey,
                        );
                    }
                } else {
                    // Handle nested key
                    let current = updatedModelSchema.properties;
                    let parent = null;

                    // Traverse to the second-to-last segment
                    for (let i = 0; i < keySegments.length - 1; i++) {
                        if (!current || !current[keySegments[i]] || !current[keySegments[i]].properties) return;
                        parent = current;
                        current = current[keySegments[i]].properties;
                    }

                    const oldKeyLastSegment = keySegments[keySegments.length - 1];
                    if (current && current[oldKeyLastSegment]) {
                        // Update the key while maintaining the rest of the properties
                        const updatedNestedProperties = reconstructPropertiesWithUpdatedKey(
                            current,
                            oldKeyLastSegment,
                            newKey,
                        );

                        // Assign the updated nested properties back to the parent
                        if (parent && parent[keySegments[keySegments.length - 2]]) {
                            parent[keySegments[keySegments.length - 2]].properties = updatedNestedProperties;
                        } else if (updatedModelSchema.properties) {
                            updatedModelSchema.properties[keySegments[0]].properties = updatedNestedProperties;
                        }
                    }
                }

                setModelSchema(updatedModelSchema);
                onChange(JSON.stringify(updatedModelSchema));
            }
        }
        setEditingKey(null);
    };

    // Helper function to add a new property
    const handleAddProperty = () => {
        const newKey = `new_property_${Object.keys(modelSchema.properties || {}).length + 1}`;
        const updatedProperties = {
            ...modelSchema.properties,
            [newKey]: {
                title: 'New Property',
                type: 'string',
                description: '',
            },
        };
        const updatedModelSchema = {
            ...modelSchema,
            properties: updatedProperties,
        };
        setModelSchema(updatedModelSchema);
        onChange(JSON.stringify(updatedModelSchema));
        handleKeyEditStart(newKey);
    };

    // Helper function to remove a property
    const handleRemoveProperty = (key: string) => {
        const { [key]: _, ...remainingProperties } = modelSchema.properties || {};
        const updatedModelSchema = {
            ...modelSchema,
            properties: remainingProperties,
        };
        setModelSchema(updatedModelSchema);
        onChange(JSON.stringify(updatedModelSchema));
    };

    // Helper function to add a new nested property
    const handleAddNestedProperty = (parentKey: string) => {
        const keys = parentKey.split('.');
        const updatedModelSchema = { ...modelSchema };
        let current = updatedModelSchema.properties;

        for (let i = 0; i < keys.length; i++) {
            if (!current || !current[keys[i]]) return;
            current = current[keys[i]].properties;
        }

        const newKey = `new_nested_property_${Object.keys(current || {}).length + 1}`;
        const updatedNestedProperties = {
            ...current,
            [newKey]: {
                title: 'New Nested Property',
                type: 'string',
                description: '',
            },
        };

        if (current) {
            Object.assign(current, updatedNestedProperties);
        }

        setModelSchema(updatedModelSchema);
        onChange(JSON.stringify(updatedModelSchema));
    };

    const handleToggle: AccordionToggleEventHandler<unknown> = (_, data) => {
        setOpenItems(data.openItems);
    };

    // Helper function to render nested properties
    const renderNestedProperties = (properties: ModelSchema['properties'], parentKey: string) => (
        <div>
            <Accordion multiple collapsible>
                {Object.entries(properties || {}).map(([key, property], index) => (
                    <AccordionItem value={index} key={key}>
                        <AccordionHeader>{`${key} (${property.type ? property.type : 'unknown'})`}</AccordionHeader>
                        <AccordionPanel>{renderSchemaFieldEditor(`${parentKey}.${key}`, property)}</AccordionPanel>
                    </AccordionItem>
                ))}
            </Accordion>
            <div className={classes.addNestedProperty}>
                <Button
                    onClick={() => handleAddNestedProperty(parentKey)}
                    appearance="outline"
                    size="small"
                    icon={<Add16Regular />}
                >
                    Add Nested Property
                </Button>
            </div>
        </div>
    );

    // Helper function to render the schema field editor
    const renderSchemaFieldEditor = (
        key: string,
        property: {
            title?: string;
            type?: string;
            description?: string;
            enum?: string[];
            properties?: ModelSchema['properties'];
            items?: { type: string };
        },
    ) => {
        const keySegments = key.split('.');
        const displayedKey = keySegments[keySegments.length - 1]; // Extract the last part of the key for display

        const isEditingKey = editingKey && editingKey.oldKey === key;

        return (
            <div className={classes.property}>
                <Field label="Key">
                    <div className={classes.keyRow}>
                        {isEditingKey ? (
                            <Input
                                ref={inputRef}
                                value={editingKey ? editingKey.newKey : displayedKey}
                                onChange={(_, data) => handleKeyEditChange(data.value)}
                                onBlur={handleKeyEditEnd}
                                onFocus={(e) => e.target.select()}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter') {
                                        handleKeyEditEnd();
                                    }
                                }}
                            />
                        ) : (
                            <>
                                <Text>{displayedKey}</Text>
                                <Button
                                    onClick={() => handleKeyEditStart(key)}
                                    appearance="subtle"
                                    size="small"
                                    icon={<Edit16Regular />}
                                />
                            </>
                        )}
                    </div>
                </Field>
                <Field label="Description">
                    <Textarea
                        value={property.description || ''}
                        onChange={(_, data) => handleSchemaChange(key, 'description', data.value)}
                        rows={2}
                    />
                </Field>
                <Field label="Type">
                    <div>
                        <Dropdown
                            placeholder="Select a type"
                            selectedOptions={property.type ? [property.type] : []}
                            value={property.type ? property.type.charAt(0).toUpperCase() + property.type.slice(1) : ''}
                            onOptionSelect={(_, item) => {
                                handleSchemaChange(key, 'type', item.optionValue);
                                if (item.optionValue === 'array') {
                                    handleSchemaChange(key, 'items', { type: 'string' });
                                } else if (item.optionValue === 'object') {
                                    handleSchemaChange(key, 'properties', {});
                                } else {
                                    handleSchemaChange(key, 'items', undefined);
                                    handleSchemaChange(key, 'properties', undefined);
                                }
                            }}
                        >
                            <Option key="string" value="string">
                                String
                            </Option>
                            <Option key="number" value="number">
                                Number
                            </Option>
                            <Option key="boolean" value="boolean">
                                Boolean
                            </Option>
                            <Option key="object" value="object">
                                Object
                            </Option>
                            <Option key="array" value="array">
                                Array
                            </Option>
                        </Dropdown>
                    </div>
                </Field>
                {property.type === 'object' && property.properties && (
                    <div className={classes.root}>
                        <Text>Nested Properties:</Text>
                        {renderNestedProperties(property.properties, key)}
                    </div>
                )}
                {property.type === 'array' && property.items && (
                    <Field label="Array Item Type">
                        <div>
                            <Dropdown
                                placeholder="Select an item type"
                                selectedOptions={property.items.type ? [property.items.type] : []}
                                value={
                                    property.items?.type
                                        ? property.items.type.charAt(0).toUpperCase() + property.items.type.slice(1)
                                        : ''
                                }
                                onOptionSelect={(_, item) =>
                                    handleSchemaChange(key, 'items', { type: item.optionValue })
                                }
                            >
                                <Option key="string" value="string">
                                    String
                                </Option>
                                <Option key="number" value="number">
                                    Number
                                </Option>
                                <Option key="boolean" value="boolean">
                                    Boolean
                                </Option>
                                <Option key="object" value="object">
                                    Object
                                </Option>
                            </Dropdown>
                        </div>
                    </Field>
                )}
                <div>
                    <Button
                        onClick={() => handleRemoveProperty(key)}
                        appearance="outline"
                        size="small"
                        icon={<Delete16Regular />}
                    >
                        Remove Property
                    </Button>
                </div>
            </div>
        );
    };

    // Render the component
    return (
        <div className={classes.root}>
            <Text>{label}</Text>
            <Accordion openItems={openItems} onToggle={handleToggle} multiple collapsible>
                {Object.entries(modelSchema.properties || {}).map(([key, property], index) => (
                    <AccordionItem value={index} key={key}>
                        <AccordionHeader>{`${key} (${property.type ? property.type : 'unknown'})`}</AccordionHeader>
                        <AccordionPanel>{renderSchemaFieldEditor(key, property)}</AccordionPanel>
                    </AccordionItem>
                ))}
            </Accordion>
            <div>
                <Button onClick={handleAddProperty} appearance="outline" size="small" icon={<Add16Regular />}>
                    Add New Property
                </Button>
            </div>
        </div>
    );
};


=== File: workbench-app/src/components/App/FormWidgets/CustomizedArrayFieldTemplate.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import {
    Accordion,
    AccordionHeader,
    AccordionItem,
    AccordionItemValue,
    AccordionPanel,
    Button,
    Text,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import { Add16Regular, ArrowDown16Regular, ArrowUp16Regular, Delete16Regular } from '@fluentui/react-icons';
import { ArrayFieldTemplateItemType, ArrayFieldTemplateProps, RJSFSchema } from '@rjsf/utils';
import React from 'react';
import { TooltipWrapper } from '../TooltipWrapper';

const useClasses = makeStyles({
    heading: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalXXS,
    },
    panel: {
        ...shorthands.margin(0, 0, tokens.spacingVerticalM, tokens.spacingHorizontalXXXL),
        ...shorthands.padding(0, 0, 0, tokens.spacingHorizontalS),
    },
    itemActions: {
        display: 'flex',
        flexDirection: 'row',
        gap: tokens.spacingHorizontalS,
        ...shorthands.padding(0, 0, tokens.spacingVerticalM, tokens.spacingHorizontalM),
    },
    addAction: {
        ...shorthands.padding(tokens.spacingVerticalM),
    },
    inline: {
        display: 'inline',
    },
    simpleItem: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'end',
        // first item should take as much width as possible
        '& > *:first-child': {
            flexGrow: 1,
        },
        gap: tokens.spacingHorizontalS,
        ...shorthands.padding(tokens.spacingVerticalS, 0),
    },
});

export const CustomizedArrayFieldTemplate: React.FC<ArrayFieldTemplateProps> = (props) => {
    const { items, canAdd, onAddClick, className, disabled, schema, uiSchema, title, formData, rawErrors } = props;
    const classes = useClasses();

    const hideTitle = uiSchema?.['ui:options']?.['hideTitle'] === true;
    const collapsed = uiSchema?.['ui:options']?.['collapsed'] !== false;
    const isCollapsible = collapsed || uiSchema?.['ui:options']?.['collapsible'] !== false;
    const itemTitleFields: string[] = uiSchema?.items?.['ui:options']?.['titleFields'] ??  [];
    const itemCollapsed = uiSchema?.items?.['ui:options']?.['collapsed'] !== false;
    const itemCollapsible = itemCollapsed || uiSchema?.items?.['ui:options']?.['collapsible'] !== false;

    const openItems: AccordionItemValue[] = [];
    if (!itemCollapsed) {
        for (let i = 0; i < items.length; i++) {
            openItems.push(i);
        }
    }

    const getItemActions = (
        element: ArrayFieldTemplateItemType<any, RJSFSchema, any>,
        index: number,
        options: {
            hasRemove?: boolean;
            hasMoveUp?: boolean;
            hasMoveDown?: boolean;
            iconsOnly?: boolean;
        },
    ) => {
        const { hasRemove, hasMoveUp, hasMoveDown, iconsOnly } = options;
        return (
            <>
                {(hasRemove || hasMoveUp || hasMoveDown) && (
                    <div className={classes.itemActions}>
                        {hasRemove && (
                            <TooltipWrapper content="Delete item">
                                <Button
                                    icon={<Delete16Regular />}
                                    appearance="outline"
                                    size="small"
                                    onClick={element.onDropIndexClick(index)}
                                    disabled={disabled}
                                >
                                    {iconsOnly ? null : 'Delete'}
                                </Button>
                            </TooltipWrapper>
                        )}
                        {hasMoveUp && (
                            <TooltipWrapper content="Move item up">
                                <Button
                                    icon={<ArrowUp16Regular />}
                                    appearance="outline"
                                    size="small"
                                    onClick={element.onReorderClick(index, index - 1)}
                                    disabled={disabled || index === 0}
                                >
                                    {iconsOnly ? null : 'Move Up'}
                                </Button>
                            </TooltipWrapper>
                        )}
                        {hasMoveDown && (
                            <TooltipWrapper content="Move item down">
                                <Button
                                    icon={<ArrowDown16Regular />}
                                    appearance="outline"
                                    size="small"
                                    onClick={element.onReorderClick(index, index + 1)}
                                    disabled={disabled || index === items.length - 1}
                                >
                                    {iconsOnly ? null : 'Move Down'}
                                </Button>
                            </TooltipWrapper>
                        )}
                    </div>
                )}
            </>
        );
    };

    let content: JSX.Element | null = null;
    const isSimpleArray = items.every(
        (item) => item.schema.type === 'string' || item.schema.type === 'number' || item.schema.type === 'integer',
    );
    if (isSimpleArray) {
        content = (
            <div>
                {items.map((element, index) => {
                    const { children, hasRemove, hasMoveUp, hasMoveDown } = element;
                    return (
                        <div key={index} className={classes.simpleItem}>
                            {children}
                            <div className={classes.inline}>
                                {getItemActions(element, index, {
                                    hasRemove,
                                    hasMoveUp,
                                    hasMoveDown,
                                    iconsOnly: true,
                                })}
                            </div>
                        </div>
                    );
                })}
            </div>
        );
    } else {
        content = (
            <Accordion multiple collapsible={itemCollapsible} defaultOpenItems={openItems}>
                {items.map((element, index) => {
                    const { children, hasRemove, hasMoveUp, hasMoveDown } = element;

                    let itemTitle = `${schema.title}: ${index + 1}`;
                    if (itemTitleFields && itemTitleFields.length > 0) {
                        itemTitle = itemTitleFields
                            // @ts-ignore
                            .map((field) => `${items[index].schema.properties?.[field]?.title ?? field}: ${formData[index][field]}`)
                            .join(', ');
                    }

                    let itemCount = undefined;
                    const countField = uiSchema?.items?.['ui:options']?.['count_field']?.toString();
                    if (countField && formData[index][countField]) {
                        const field = formData[index][countField];
                        // if field is an array, count the length
                        if (Array.isArray(field)) {
                            itemCount = field.length;
                        }
                    }

                    return (
                        <AccordionItem key={index} value={index}>
                            <AccordionHeader>
                                <Text>{itemTitle}</Text>
                                {itemCount !== undefined && <Text>&nbsp;({itemCount})</Text>}
                            </AccordionHeader>
                            <AccordionPanel className={classes.panel}>
                                {getItemActions(element, index, { hasRemove, hasMoveUp, hasMoveDown })}
                                <div>{children}</div>
                            </AccordionPanel>
                        </AccordionItem>
                    );
                })}
            </Accordion>
        );
    }

    const descriptionAndControls =
        <>
            {schema.description && <Text italic>{schema.description}</Text>}
            {canAdd && (
                <div>
                    <Button
                        icon={<Add16Regular />}
                        appearance="outline"
                        size="small"
                        onClick={onAddClick}
                        disabled={disabled}
                    >
                        Add
                    </Button>
                </div>
            )}
            {rawErrors && rawErrors.length > 0 && (
                <div>
                    <Text style={{ color: 'red' }}>{rawErrors.join(', ')}</Text>
                </div>
            )}
        </>;

    if (isCollapsible) {
        return (
            <Accordion multiple collapsible defaultOpenItems={openItems}>
                <AccordionItem value={schema.$id}>
                    <AccordionHeader>
                        <Text>{title}</Text>
                    </AccordionHeader>
                    <AccordionPanel>
                        <div className={classes.heading}>
                            {descriptionAndControls}
                        </div>
                        {content}
                    </AccordionPanel>
                </AccordionItem>
            </Accordion>
        );
    }

    return (
        <div className={className}>
            <div className={classes.heading}>
                {!hideTitle && <Text>{title}</Text>}
                {descriptionAndControls}
            </div>
            {content}
        </div>
    );
};


=== File: workbench-app/src/components/App/FormWidgets/CustomizedFieldTemplate.tsx ===
import { Dropdown, Field, makeStaticStyles, makeStyles, Option, Text, tokens } from '@fluentui/react-components';
import {
    FieldTemplateProps,
    FormContextType,
    getTemplate,
    getUiOptions,
    RJSFSchema,
    StrictRJSFSchema,
} from '@rjsf/utils';
import React from 'react';

// Global styles for parent elements we don't directly control
const useStaticStyles = makeStaticStyles({
    'div:has(> [data-hidden-rjsf-field="true"])': {
        display: 'none',
    },
});

const useClasses = makeStyles({
    hiddenField: {
        display: 'none',
    },
});

/** The `FieldTemplate` component is the template used by `SchemaField` to render any field. It renders the field
 * content, (label, description, children, errors and help) inside of a `WrapIfAdditional` component.
 *
 * @param props - The `FieldTemplateProps` for this component
 */
export default function CustomizedFieldTemplate<
    T = any,
    S extends StrictRJSFSchema = RJSFSchema,
    F extends FormContextType = any,
>(props: FieldTemplateProps<T, S, F>) {
    const {
        id,
        children,
        classNames,
        style,
        disabled,
        displayLabel,
        formData,
        hidden,
        label,
        onChange,
        onDropPropertyClick,
        onKeyChange,
        readonly,
        required,
        rawErrors = [],
        errors,
        help,
        description,
        rawDescription,
        schema,
        uiSchema,
        registry,
    } = props;
    const uiOptions = getUiOptions<T, S, F>(uiSchema);
    const WrapIfAdditionalTemplate = getTemplate<'WrapIfAdditionalTemplate', T, S, F>(
        'WrapIfAdditionalTemplate',
        registry,
        uiOptions,
    );
    const classes = useClasses();
    useStaticStyles();

    // If uiSchema includes ui:options for this field, check if it has configurations
    // These are used to provide a dropdown to select a configuration for the field
    // that will update the formData value and allow users to switch between configurations
    // If the user modifies the field value, the configuration dropdown will be reset
    const configurationsComponent = React.useMemo(() => {
        if (uiOptions && uiOptions['configurations'] && typeof uiOptions['configurations'] === 'object') {
            // handle as record
            const configurations = uiOptions['configurations'] as Record<string, any>;

            // Handle selection change for dropdown
            const handleSelectionChange = (_: React.SyntheticEvent<HTMLElement>, option: any) => {
                const selectedConfig = configurations[option.optionValue];
                onChange(selectedConfig);
            };

            const selectedKey =
                Object.keys(configurations).find(
                    (key) => JSON.stringify(configurations[key]) === JSON.stringify(formData),
                ) || '';

            const selectedOptions = selectedKey ? [selectedKey] : [];

            return (
                <Field label={`${label}: Select Configuration`} style={{ padding: `${tokens.spacingVerticalM} 0` }}>
                    <div>
                        <Dropdown
                            value={selectedKey}
                            selectedOptions={selectedOptions}
                            onOptionSelect={handleSelectionChange}
                            placeholder="Choose a configuration"
                        >
                            {Object.entries(configurations).map(([key]) => (
                                <Option key={key} value={key}>
                                    {key}
                                </Option>
                            ))}
                        </Dropdown>
                    </div>
                </Field>
            );
        }
        return null;
    }, [formData, label, onChange, uiOptions]);

    if (hidden) {
        return <div className={classes.hiddenField} data-hidden-rjsf-field="true">{children}</div>;
    }
    return (
        <WrapIfAdditionalTemplate
            classNames={classNames}
            style={style}
            disabled={disabled}
            id={id}
            label={label}
            onDropPropertyClick={onDropPropertyClick}
            onKeyChange={onKeyChange}
            readonly={readonly}
            required={required}
            schema={schema}
            uiSchema={uiSchema}
            registry={registry}
        >
            <Field validationState={rawErrors.length ? 'error' : undefined} required={required}>
                {configurationsComponent}
                {children}
                {displayLabel && rawDescription ? (
                    <Text block style={{ display: 'block', marginTop: tokens.spacingVerticalS }}>
                        {description}
                    </Text>
                ) : null}
                {errors}
                {help}
            </Field>
        </WrapIfAdditionalTemplate>
    );
}


=== File: workbench-app/src/components/App/FormWidgets/CustomizedObjectFieldTemplate.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import {
    Accordion,
    AccordionHeader,
    AccordionItem,
    AccordionPanel,
    Divider,
    Text,
    Tooltip,
    makeStyles,
    tokens,
} from '@fluentui/react-components';
import { ObjectFieldTemplateProps } from '@rjsf/utils';
import React from 'react';

const useClasses = makeStyles({
    heading: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalS,
    },
    items: {
        display: 'flex',
        flexDirection: 'column',
        paddingLeft: tokens.spacingHorizontalM,
        gap: tokens.spacingVerticalS,
    },
});

export const CustomizedObjectFieldTemplate: React.FC<ObjectFieldTemplateProps> = (props) => {
    const { title, description, properties, uiSchema, idSchema, schema } = props;
    const classes = useClasses();

    const hideTitle = uiSchema?.['ui:options']?.['hideTitle'];

    const isCollapsed = uiSchema?.['ui:options']?.['collapsed'] !== false;
    const isCollapsible = uiSchema?.['ui:options']?.['collapsed'] !== undefined || uiSchema?.['ui:options']?.['collapsible'] !== false;
    const openItems = isCollapsed ? [] : [idSchema.$id];

    const descriptionValue = description ?? schema.description;

    if (isCollapsible) {
        return (
            <Accordion multiple collapsible defaultOpenItems={openItems}>
                <AccordionItem value={idSchema.$id}>
                    <AccordionHeader>
                        {descriptionValue &&
                            <Tooltip content={descriptionValue || ''} relationship='description'>
                                <Text>{title}</Text>
                            </Tooltip>
                        }
                        {!descriptionValue && <Text>{title}</Text>}
                    </AccordionHeader>
                    <AccordionPanel>
                        {descriptionValue && <Text italic>{descriptionValue}</Text>}
                        <div className={classes.items}>
                            {properties.map((element, index) => {
                                return <div key={index}>{element.content}</div>;
                            })}
                        </div>
                    </AccordionPanel>
                </AccordionItem>
            </Accordion>
        );
    }

    return (
        <div>
            <div className={classes.heading}>
                {!hideTitle && (
                    <>
                        <Text>{title}</Text>
                        <Divider />
                    </>
                )}
                {descriptionValue && <Text italic>{descriptionValue}</Text>}
            </div>
            <div className={classes.items}>
                {properties.map((element, index) => {
                    return <div key={index}>{element.content}</div>;
                })}
            </div>
        </div>
    );
};


=== File: workbench-app/src/components/App/FormWidgets/InspectableWidget.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { WidgetProps } from '@rjsf/utils';
import React from 'react';
import { DebugInspector } from '../../Conversations/DebugInspector';

export const InspectableWidget: React.FC<WidgetProps> = (props) => {
    const { value } = props;

    let jsonValue = undefined;
    try {
        jsonValue = JSON.parse(value as string);
    } catch (e) {
        return null;
    }

    return <DebugInspector debug={jsonValue} />;
};


=== File: workbench-app/src/components/App/LabelWithDescription.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Text } from '@fluentui/react-components';
import { QuestionCircle16Regular } from '@fluentui/react-icons';
import React from 'react';
import { TooltipWrapper } from './TooltipWrapper';

interface LabelWithDescriptionProps {
    label: string;
    description?: string;
}

export const LabelWithDescription: React.FC<LabelWithDescriptionProps> = (props) => {
    const { label, description } = props;

    return (
        <div>
            <Text weight="semibold">{label}</Text>
            {description && (
                <TooltipWrapper content={description}>
                    <QuestionCircle16Regular fontWeight={100} />
                </TooltipWrapper>
            )}
        </div>
    );
};


=== File: workbench-app/src/components/App/Loading.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Spinner, makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { Constants } from '../../Constants';

const useClasses = makeStyles({
    root: {
        ...shorthands.margin(tokens.spacingVerticalM),
    },
});

interface LoadingProps {
    className?: string;
}

export const Loading: React.FC<LoadingProps> = (props) => {
    const { className } = props;
    const classes = useClasses();
    const [showSpinner, setShowSpinner] = React.useState(false);

    React.useEffect(() => {
        const timer = setTimeout(() => {
            setShowSpinner(true);
        }, Constants.app.loaderDelayMs);

        return () => clearTimeout(timer);
    }, []);

    return showSpinner ? (
        <Spinner className={mergeClasses(classes.root, className)} size="medium" label="Loading..." />
    ) : null;
};


=== File: workbench-app/src/components/App/MenuItemControl.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { ButtonProps, MenuItem } from '@fluentui/react-components';
import React from 'react';
import { TooltipWrapper } from './TooltipWrapper';

type MenuItemControlProps = ButtonProps & {
    label?: string;
    description?: string;
    onClick?: () => void;
    iconOnly?: boolean;
};

export const MenuItemControl: React.FC<MenuItemControlProps> = (props) => {
    const { disabled, icon, label, description, onClick, iconOnly } = props;

    let menuItem = null;

    if (iconOnly) {
        if (description) {
            menuItem = (
                <TooltipWrapper content={description}>
                    <MenuItem disabled={disabled} icon={icon} onClick={onClick} />
                </TooltipWrapper>
            );
        } else {
            menuItem = <MenuItem disabled={disabled} icon={icon} onClick={onClick} />;
        }
    } else {
        menuItem = (
            <MenuItem disabled={disabled} icon={icon} onClick={onClick}>
                {label}
            </MenuItem>
        );
        if (description) {
            menuItem = <TooltipWrapper content={description}>{menuItem}</TooltipWrapper>;
        }
    }
    return menuItem;
};


=== File: workbench-app/src/components/App/MiniControl.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Card, Label, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { Link } from 'react-router-dom';
import { TooltipWrapper } from './TooltipWrapper';

const useClasses = makeStyles({
    header: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        color: 'inherit',
        gap: tokens.spacingHorizontalS,
        ...shorthands.textDecoration('none'),
    },
    link: {
        cursor: 'pointer',
    },
    body: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: tokens.spacingVerticalM,
    },
    actions: {
        display: 'flex',
        flexDirection: 'row',
        gap: tokens.spacingHorizontalS,
    },
});

interface MiniControlProps {
    icon: JSX.Element;
    label: string;
    linkUrl: string;
    actions?: JSX.Element;
    tooltip?: string;
}

export const MiniControl: React.FC<MiniControlProps> = (props) => {
    const { icon, label, linkUrl, actions, tooltip } = props;
    const classes = useClasses();

    const link = (
        <Link className={classes.header} to={linkUrl}>
            {icon}
            <Label className={classes.link} size="large">
                {label}
            </Label>
        </Link>
    );

    return (
        <Card>
            <div className={classes.body}>
                {tooltip ? <TooltipWrapper content={tooltip}>{link}</TooltipWrapper> : link}
                <div className={classes.actions}>{actions}</div>
            </div>
        </Card>
    );
};


=== File: workbench-app/src/components/App/MyAssistantServiceRegistrations.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { BotRegular } from '@fluentui/react-icons';
import React from 'react';
import { AssistantServiceRegistration } from '../../models/AssistantServiceRegistration';
import { useGetAssistantServiceRegistrationsQuery } from '../../services/workbench';
import { AssistantServiceRegistrationCreate } from '../AssistantServiceRegistrations/AssistantServiceRegistrationCreate';
import { AssistantServiceRegistrationRemove } from '../AssistantServiceRegistrations/AssistantServiceRegistrationRemove';
import { CommandButton } from './CommandButton';
import { MiniControl } from './MiniControl';
import { MyItemsManager } from './MyItemsManager';

interface MyAssistantServiceRegistrationsProps {
    assistantServiceRegistrations?: AssistantServiceRegistration[];
    title?: string;
    hideInstruction?: boolean;
    onCreate?: (assistantServiceRegistration: AssistantServiceRegistration) => void;
}

export const MyAssistantServiceRegistrations: React.FC<MyAssistantServiceRegistrationsProps> = (props) => {
    const { assistantServiceRegistrations, title, hideInstruction, onCreate } = props;
    const { refetch: refetchAssistantServiceRegistrations } = useGetAssistantServiceRegistrationsQuery({
        userIds: ['me'],
    });
    const [assistantServiceRegistrationCreateOpen, setAssistantServiceRegistrationCreateOpen] = React.useState(false);

    const handleAssistantServiceRegistrationCreate = async (
        assistantServiceRegistration: AssistantServiceRegistration,
    ) => {
        await refetchAssistantServiceRegistrations();
        onCreate?.(assistantServiceRegistration);
    };

    return (
        <MyItemsManager
            items={assistantServiceRegistrations
                ?.toSorted((a, b) => a.name.localeCompare(b.name))
                .map((assistantServiceRegistration) => (
                    <MiniControl
                        key={assistantServiceRegistration.assistantServiceId}
                        icon={<BotRegular />}
                        label={assistantServiceRegistration.name}
                        linkUrl={`/assistant-service-registration/${encodeURIComponent(
                            assistantServiceRegistration.assistantServiceId,
                        )}/edit`}
                        actions={
                            <>
                                {/* <Link to={`/assistant/${assistantServiceRegistration.id}/edit`}>
                                    <Button icon={<EditRegular />} />
                                </Link> */}
                                <AssistantServiceRegistrationRemove
                                    assistantServiceRegistration={assistantServiceRegistration}
                                    iconOnly
                                />
                            </>
                        }
                    />
                ))}
            title={title ?? 'My Assistant Service Registrations'}
            itemLabel="Assistant Service Registration"
            hideInstruction={hideInstruction}
            actions={
                <>
                    <CommandButton
                        icon={<BotRegular />}
                        label={`New Assistant Service Registration`}
                        description={`Create a new assistant service registration`}
                        onClick={() => setAssistantServiceRegistrationCreateOpen(true)}
                    />
                    <AssistantServiceRegistrationCreate
                        open={assistantServiceRegistrationCreateOpen}
                        onOpenChange={(open) => setAssistantServiceRegistrationCreateOpen(open)}
                        onCreate={handleAssistantServiceRegistrationCreate}
                    />
                </>
            }
        />
    );
};


=== File: workbench-app/src/components/App/MyItemsManager.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Card, Text, Title3, makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { PresenceMotionList } from '../App/PresenceMotionList';

const useClasses = makeStyles({
    root: {
        backgroundImage: `linear-gradient(to right, ${tokens.colorNeutralBackground1}, ${tokens.colorBrandBackground2})`,
    },
    actions: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: tokens.spacingVerticalS,
    },
});

interface MyItemsManagerProps {
    items?: JSX.Element[];
    title: string;
    itemLabel: string;
    hideInstruction?: boolean;
    actions: JSX.Element;
}

export const MyItemsManager: React.FC<MyItemsManagerProps> = (props) => {
    const { items, title, itemLabel, hideInstruction, actions } = props;
    const classes = useClasses();

    return (
        <Card className={classes.root}>
            <Text size={400} weight="semibold">
                {title}
            </Text>
            <div className={classes.actions}>{actions}</div>
            {items?.length === 0 && (
                <>
                    <Title3>No {itemLabel.toLowerCase()}s found.</Title3>
                    {!hideInstruction && (
                        <Text>
                            Create a new {itemLabel.toLowerCase()} by clicking the <strong>New {itemLabel}</strong>{' '}
                            button above.
                        </Text>
                    )}
                </>
            )}
            <PresenceMotionList items={items} />
        </Card>
    );
};


=== File: workbench-app/src/components/App/OverflowMenu.tsx ===
import {
    Button,
    makeStyles,
    Menu,
    MenuItem,
    MenuList,
    MenuPopover,
    MenuTrigger,
    Slot,
    tokens,
    useIsOverflowItemVisible,
    useOverflowMenu,
} from '@fluentui/react-components';
import { MoreHorizontalRegular } from '@fluentui/react-icons';
import React from 'react';

const useClasses = makeStyles({
    menu: {
        backgroundColor: tokens.colorNeutralBackground1,
    },
    menuButton: {
        alignSelf: 'center',
    },
});

export interface OverflowMenuItemData {
    id: string;
    icon?: Slot<'span'>;
    name?: string;
}

interface OverflowMenuItemProps {
    item: OverflowMenuItemData;
    onClick: (event: React.MouseEvent, id: string) => void;
}

export const OverflowMenuItem: React.FC<OverflowMenuItemProps> = (props) => {
    const { item, onClick } = props;
    const isVisible = useIsOverflowItemVisible(item.id);

    if (isVisible) {
        return null;
    }

    return (
        <MenuItem key={item.id} icon={item.icon} onClick={(event) => onClick(event, item.id)}>
            {item.name}
        </MenuItem>
    );
};

interface OverflowMenuProps {
    items: OverflowMenuItemData[];
    onItemSelect: (id: string) => void;
}

export const OverflowMenu: React.FC<OverflowMenuProps> = (props) => {
    const { items, onItemSelect } = props;
    const classes = useClasses();
    const { ref, isOverflowing, overflowCount } = useOverflowMenu<HTMLButtonElement>();

    const handleItemClick = (_event: React.MouseEvent, id: string) => {
        onItemSelect(id);
    };

    if (!isOverflowing) {
        return null;
    }

    return (
        <Menu hasIcons={items.find((item) => item.icon !== undefined) !== undefined}>
            <MenuTrigger disableButtonEnhancement>
                <Button
                    className={classes.menuButton}
                    appearance="transparent"
                    ref={ref}
                    icon={<MoreHorizontalRegular />}
                    aria-label={`${overflowCount} more options`}
                    role="tab"
                />
            </MenuTrigger>
            <MenuPopover>
                <MenuList className={classes.menu}>
                    {items.map((item) => (
                        <OverflowMenuItem key={item.id} item={item} onClick={handleItemClick}></OverflowMenuItem>
                    ))}
                </MenuList>
            </MenuPopover>
        </Menu>
    );
};


=== File: workbench-app/src/components/App/PresenceMotionList.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, mergeClasses, tokens } from '@fluentui/react-components';
import { PresenceGroup, createPresenceComponent, motionTokens } from '@fluentui/react-motions-preview';
import React from 'react';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
});

const ItemMotion = createPresenceComponent({
    enter: {
        keyframes: [{ opacity: 0 }, { opacity: 1 }],

        easing: motionTokens.easingEasyEase,
        duration: motionTokens.durationUltraSlow,
    },
    exit: {
        keyframes: [{ opacity: 1 }, { opacity: 0 }],

        easing: motionTokens.easingEasyEase,
        duration: motionTokens.durationUltraSlow,
    },
});

interface PresenceMotionListProps {
    className?: string;
    items?: React.ReactNode[];
}

export const PresenceMotionList: React.FC<PresenceMotionListProps> = (props) => {
    const { className, items } = props;
    const classes = useClasses();

    return (
        <div className={mergeClasses(classes.root, className)}>
            <PresenceGroup>
                {items?.map((item, index) => (
                    <ItemMotion key={index}>
                        <div>{item}</div>
                    </ItemMotion>
                ))}
            </PresenceGroup>
        </div>
    );
};


=== File: workbench-app/src/components/App/ProfileSettings.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { useAccount, useIsAuthenticated, useMsal } from '@azure/msal-react';
import {
    Label,
    Link,
    Persona,
    Popover,
    PopoverSurface,
    PopoverTrigger,
    makeStyles,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { AuthHelper } from '../../libs/AuthHelper';
import { useMicrosoftGraph } from '../../libs/useMicrosoftGraph';
import { useAppDispatch, useAppSelector } from '../../redux/app/hooks';
import { setLocalUser } from '../../redux/features/localUser/localUserSlice';

const useClasses = makeStyles({
    popoverSurface: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingHorizontalM,
    },
    accountInfo: {
        display: 'flex',
        flexDirection: 'column',
    },
});

export const ProfileSettings: React.FC = () => {
    const classes = useClasses();
    const { instance } = useMsal();
    const isAuthenticated = useIsAuthenticated();
    const account = useAccount();
    const microsoftGraph = useMicrosoftGraph();
    const localUserState = useAppSelector((state) => state.localUser);
    const dispatch = useAppDispatch();

    React.useEffect(() => {
        (async () => {
            if (!isAuthenticated || !account?.name || localUserState.id) {
                return;
            }

            const photo = await microsoftGraph.getMyPhotoAsync();

            dispatch(
                setLocalUser({
                    id: (account.homeAccountId || '').split('.').reverse().join('.'),
                    name: account.name,
                    email: account.username,
                    avatar: {
                        name: account.name,
                        image: photo ? { src: photo } : undefined,
                    },
                }),
            );
        })();
    }, [account, dispatch, isAuthenticated, localUserState.id, microsoftGraph]);

    const handleSignOut = () => {
        void AuthHelper.logoutAsync(instance);
    };

    const handleSignIn = () => {
        void AuthHelper.loginAsync(instance);
    };

    return (
        <Popover positioning="below-end">
            <PopoverTrigger>
                <Persona className="user-avatar" avatar={localUserState.avatar} presence={{ status: 'available' }} />
            </PopoverTrigger>
            <PopoverSurface>
                <div className={classes.popoverSurface}>
                    {isAuthenticated ? (
                        <>
                            <div className={classes.accountInfo}>
                                <Label>{localUserState.name}</Label>
                                <Label size="small">{localUserState.email}</Label>
                            </div>
                            <Link onClick={handleSignOut}>Sign Out</Link>
                        </>
                    ) : (
                        <Link onClick={handleSignIn}>Sign In</Link>
                    )}
                </div>
            </PopoverSurface>
        </Popover>
    );
};


=== File: workbench-app/src/components/App/TooltipWrapper.tsx ===
import { Tooltip } from '@fluentui/react-components';
import React from 'react';

interface TooltipWrapperProps {
    content: string;
    children: React.ReactElement;
}

// Use forwardRef to allow it to still be used within a DialogTrigger
export const TooltipWrapper = React.forwardRef((props: TooltipWrapperProps, forwardedRef) => {
    const { content, children, ...rest } = props;

    // rest will include any props passed by DialogTrigger,
    // e.g. onClick, aria-expanded, data-dialog-trigger, etc.

    const onlyChild = React.Children.only(children);

    // Merge and forward everything onto the actual child (button, link, etc.)
    const childWithAllProps = React.cloneElement(onlyChild, {
        ...onlyChild.props,
        ...rest,
        ref: forwardedRef,
    });

    return (
        <Tooltip content={content} relationship="label">
            {childWithAllProps}
        </Tooltip>
    );
});

TooltipWrapper.displayName = 'TooltipWrapper';


=== File: workbench-app/src/components/AssistantServiceRegistrations/AssistantServiceRegistrationApiKey.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button, Field, Input, Text, makeStyles, tokens } from '@fluentui/react-components';
import { Copy24Regular } from '@fluentui/react-icons';
import React from 'react';
import { DialogControl } from '../App/DialogControl';

const useClasses = makeStyles({
    dialogContent: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
    row: {
        display: 'flex',
        alignItems: 'center',
    },
});

interface AssistantServiceRegistrationApiKeyProps {
    apiKey: string;
    onClose: () => void;
}

export const AssistantServiceRegistrationApiKey: React.FC<AssistantServiceRegistrationApiKeyProps> = (props) => {
    const { apiKey, onClose } = props;
    const classes = useClasses();
    const inputRef = React.useRef<HTMLInputElement>(null);
    const [copiedTimeout, setCopiedTimeout] = React.useState<NodeJS.Timeout>();

    React.useEffect(() => {
        // wait for the dialog to open before selecting the link
        setTimeout(() => {
            inputRef.current?.select();
        }, 0);
    }, []);

    const handleCopy = React.useCallback(async () => {
        if (copiedTimeout) {
            clearTimeout(copiedTimeout);
            setCopiedTimeout(undefined);
        }

        await navigator.clipboard.writeText(apiKey);

        // set a timeout to clear the copied message
        const timeout = setTimeout(() => {
            setCopiedTimeout(undefined);
        }, 2000);
        setCopiedTimeout(timeout);
    }, [apiKey, copiedTimeout]);

    return (
        <DialogControl
            open={true}
            classNames={{
                dialogContent: classes.dialogContent,
            }}
            title="Assistant Service Registration API Key"
            content={
                <>
                    <Field>
                        <Input
                            ref={inputRef}
                            value={apiKey}
                            readOnly
                            contentAfter={
                                <div className={classes.row}>
                                    {copiedTimeout && <Text>Copied to clipboard!</Text>}
                                    <Button appearance="transparent" icon={<Copy24Regular />} onClick={handleCopy} />
                                </div>
                            }
                        />
                    </Field>
                    <Text>
                        Make sure to copy the API key before closing this dialog, as it will not be displayed again.
                    </Text>
                </>
            }
            onOpenChange={onClose}
        />
    );
};


=== File: workbench-app/src/components/AssistantServiceRegistrations/AssistantServiceRegistrationApiKeyReset.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogTrigger, Label } from '@fluentui/react-components';
import { KeyResetRegular } from '@fluentui/react-icons';
import React from 'react';
import { AssistantServiceRegistration } from '../../models/AssistantServiceRegistration';
import { useResetAssistantServiceRegistrationApiKeyMutation } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';
import { AssistantServiceRegistrationApiKey } from './AssistantServiceRegistrationApiKey';

interface AssistantServiceRegistrationApiKeyResetProps {
    assistantServiceRegistration: AssistantServiceRegistration;
    onRemove?: () => void;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const AssistantServiceRegistrationApiKeyReset: React.FC<AssistantServiceRegistrationApiKeyResetProps> = (
    props,
) => {
    const { assistantServiceRegistration, onRemove, iconOnly, asToolbarButton } = props;
    const [resetAssistantServiceRegistrationApiKey] = useResetAssistantServiceRegistrationApiKeyMutation();
    const [submitted, setSubmitted] = React.useState(false);
    const [unmaskedApiKey, setUnmaskedApiKey] = React.useState<string | undefined>(undefined);

    const handleReset = React.useCallback(async () => {
        if (submitted) {
            return;
        }
        setSubmitted(true);

        try {
            let updatedRegistration: AssistantServiceRegistration | undefined;
            try {
                updatedRegistration = await resetAssistantServiceRegistrationApiKey(
                    assistantServiceRegistration.assistantServiceId,
                ).unwrap();
            } finally {
                setSubmitted(false);
            }

            if (updatedRegistration) {
                setUnmaskedApiKey(updatedRegistration.apiKey);
            }

            onRemove?.();
        } finally {
            setSubmitted(false);
        }
    }, [submitted, onRemove, resetAssistantServiceRegistrationApiKey, assistantServiceRegistration.assistantServiceId]);

    return (
        <>
            {unmaskedApiKey && (
                <AssistantServiceRegistrationApiKey
                    apiKey={unmaskedApiKey}
                    onClose={() => setUnmaskedApiKey(undefined)}
                />
            )}
            <CommandButton
                disabled={submitted}
                description="Reset API Key"
                icon={<KeyResetRegular />}
                iconOnly={iconOnly}
                asToolbarButton={asToolbarButton}
                label={submitted ? 'Resetting...' : 'Reset'}
                dialogContent={{
                    title: 'Reset API Key',
                    content: (
                        <>
                            <p>
                                <Label>
                                    Are you sure you want to reset the API key for this assistant service registration?
                                </Label>
                            </p>
                            <p>
                                Any existing assistant services using the current API key will stop working. You will
                                need to update the API key in any assistant services that use it.
                            </p>
                        </>
                    ),
                    closeLabel: 'Cancel',
                    additionalActions: [
                        <DialogTrigger key="reset" disableButtonEnhancement>
                            <Button appearance="primary" onClick={handleReset}>
                                Reset
                            </Button>
                        </DialogTrigger>,
                    ],
                }}
            />
        </>
    );
};


=== File: workbench-app/src/components/AssistantServiceRegistrations/AssistantServiceRegistrationCreate.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Checkbox,
    DialogOpenChangeData,
    DialogOpenChangeEvent,
    DialogTrigger,
    Field,
    Input,
    makeStyles,
    Textarea,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import {
    AssistantServiceRegistration,
    NewAssistantServiceRegistration,
} from '../../models/AssistantServiceRegistration';
import {
    useCreateAssistantServiceRegistrationMutation,
    useGetAssistantServiceRegistrationsQuery,
} from '../../services/workbench';
import { DialogControl } from '../App/DialogControl';
import { AssistantServiceRegistrationApiKey } from './AssistantServiceRegistrationApiKey';

const useClasses = makeStyles({
    dialogContent: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
});

interface AssistantServiceRegistrationCreateProps {
    open: boolean;
    onOpenChange?: (open: boolean) => void;
    onCreate?: (assistantServiceRegistration: AssistantServiceRegistration) => void;
}

export const AssistantServiceRegistrationCreate: React.FC<AssistantServiceRegistrationCreateProps> = (props) => {
    const { open, onOpenChange, onCreate } = props;
    const classes = useClasses();
    const { refetch: refetchAssistantServiceRegistrations } = useGetAssistantServiceRegistrationsQuery({});
    const [createAssistantServiceRegistration] = useCreateAssistantServiceRegistrationMutation();
    const [name, setName] = React.useState('');
    const [includeInListing, setIncludeInListing] = React.useState(false);
    const [description, setDescription] = React.useState('');
    const [id, setId] = React.useState('');
    const [valid, setValid] = React.useState(false);
    const [submitted, setSubmitted] = React.useState(false);
    const [apiKey, setApiKey] = React.useState<string>();

    const handleSave = React.useCallback(async () => {
        if (submitted) {
            return;
        }
        setSubmitted(true);

        const newAssistantServiceRegistration: NewAssistantServiceRegistration = {
            assistantServiceId: id,
            name,
            description,
            includeInListing,
        };

        try {
            const assistantServiceRegistration = await createAssistantServiceRegistration(
                newAssistantServiceRegistration,
            ).unwrap();
            await refetchAssistantServiceRegistrations();
            onOpenChange?.(false);
            onCreate?.(assistantServiceRegistration);
            setApiKey(assistantServiceRegistration.apiKey);
        } finally {
            setSubmitted(false);
        }
    }, [
        createAssistantServiceRegistration,
        description,
        id,
        includeInListing,
        name,
        onCreate,
        onOpenChange,
        refetchAssistantServiceRegistrations,
        submitted,
    ]);

    const resetState = React.useCallback(() => {
        setValid(false);
        setId('');
        setName('');
        setIncludeInListing(false);
        setDescription('');
        setApiKey(undefined);
        setSubmitted(false);
    }, []);

    React.useEffect(() => {
        if (!open) {
            return;
        }
        resetState();
    }, [open, resetState]);

    const handleOpenChange = React.useCallback(
        (_event: DialogOpenChangeEvent, data: DialogOpenChangeData) => {
            if (!data.open) {
                resetState();
            }
            onOpenChange?.(data.open);
        },
        [onOpenChange, resetState],
    );

    return (
        <>
            {apiKey && <AssistantServiceRegistrationApiKey apiKey={apiKey} onClose={() => setApiKey(undefined)} />}
            <DialogControl
                open={open}
                classNames={{
                    dialogContent: classes.dialogContent,
                }}
                onOpenChange={handleOpenChange}
                title="Create Assistant Service Registration"
                content={
                    <form>
                        <Field label="Assistant Service ID" required>
                            <Input
                                value={id}
                                onChange={(event, data) => {
                                    // lowercase first
                                    data.value = data.value.toLowerCase();
                                    // limit to lowercase alphanumeric and hyphen
                                    data.value = data.value.replace(/[^a-z0-9-.]/g, '');

                                    setId(data.value);
                                    setValid(event.currentTarget.form!.checkValidity());
                                }}
                                aria-autocomplete="none"
                                placeholder="Unique identifier for your assistant; eg: helpful-assistant.team-name"
                            />
                        </Field>
                        <Field label="Name" required>
                            <Input
                                value={name}
                                onChange={(event, data) => {
                                    setName(data.value);
                                    setValid(event.currentTarget.form!.checkValidity());
                                }}
                                aria-autocomplete="none"
                                placeholder="Display name for your assistant; eg: Helpful Assistant"
                            />
                        </Field>
                        <Checkbox
                            label="Include this assistant service in everyone's create assistant list"
                            checked={includeInListing}
                            onChange={(_, data) => setIncludeInListing(data.checked === true)}
                        />
                        <Field label="Description">
                            <Textarea
                                value={description}
                                onChange={(event, data) => {
                                    setDescription(data.value);
                                    setValid(event.currentTarget.form!.checkValidity());
                                }}
                                aria-autocomplete="none"
                                placeholder="Description of your assistant; eg: A helpful assistant that can answer questions and provide guidance."
                            />
                        </Field>
                    </form>
                }
                additionalActions={[
                    <DialogTrigger key="save" disableButtonEnhancement>
                        <Button appearance="primary" onClick={handleSave} disabled={!valid || submitted}>
                            {submitted ? 'Saving...' : 'Save'}
                        </Button>
                    </DialogTrigger>,
                ]}
                closeLabel="Cancel"
            />
        </>
    );
};


=== File: workbench-app/src/components/AssistantServiceRegistrations/AssistantServiceRegistrationRemove.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { DialogTrigger } from '@fluentui/react-components';
import { DeleteRegular } from '@fluentui/react-icons';
import React from 'react';
import { AssistantServiceRegistration } from '../../models/AssistantServiceRegistration';
import { useRemoveAssistantServiceRegistrationMutation } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';

interface AssistantServiceRegistrationRemoveProps {
    assistantServiceRegistration: AssistantServiceRegistration;
    onRemove?: () => void;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const AssistantServiceRegistrationRemove: React.FC<AssistantServiceRegistrationRemoveProps> = (props) => {
    const { assistantServiceRegistration, onRemove, iconOnly, asToolbarButton } = props;
    const [removeAssistantServiceRegistration] = useRemoveAssistantServiceRegistrationMutation();
    const [submitted, setSubmitted] = React.useState(false);

    if (!assistantServiceRegistration) {
        throw new Error(`Assistant service registration not found`);
    }

    const handleAssistantServiceRegistrationRemove = React.useCallback(async () => {
        if (submitted) {
            return;
        }
        setSubmitted(true);

        try {
            await removeAssistantServiceRegistration(assistantServiceRegistration.assistantServiceId);
            onRemove?.();
        } finally {
            setSubmitted(false);
        }
    }, [assistantServiceRegistration.assistantServiceId, onRemove, removeAssistantServiceRegistration, submitted]);

    return (
        <CommandButton
            icon={<DeleteRegular />}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
            description="Delete assistant service registration"
            dialogContent={{
                title: 'Delete Assistant Service Registration',
                content: (
                    <p>
                        Are you sure you want to delete the assistant service registration{' '}
                        <strong>{assistantServiceRegistration.name}</strong>?
                    </p>
                ),
                closeLabel: 'Cancel',
                additionalActions: [
                    <DialogTrigger key="delete" disableButtonEnhancement>
                        <CommandButton
                            icon={<DeleteRegular />}
                            label="Delete"
                            onClick={handleAssistantServiceRegistrationRemove}
                        />
                    </DialogTrigger>,
                ],
            }}
        />
    );
};


=== File: workbench-app/src/components/Assistants/ApplyConfigButton.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogTrigger, makeStyles, Text } from '@fluentui/react-components';

import { diffJson } from 'diff';
import React from 'react';
import { Utility } from '../../libs/Utility';
import { CommandButton } from '../App/CommandButton';
import { DiffRenderer } from '../Conversations/ContentRenderers/DiffRenderer';

const useClasses = makeStyles({
    dialogSurface: {
        maxWidth: 'calc(100vw - 32px)',
        minWidth: 'min(600px, 100vw)',
        width: 'fit-content',
    },
    dialogContent: {
        height: 'calc(100vh - 150px)',
        width: 'calc(100vw - 100px)',
        paddingRight: '8px',
        boxSizing: 'border-box',
    },
    configDiff: {
        maxHeight: 'calc(100vh - 250px)',
        overflowY: 'auto',
    },
    diffView: {
        width: '100%',
    },
});

interface ApplyConfigButtonProps {
    label?: string;
    confirmMessage?: string;
    currentConfig?: object;
    newConfig: object;
    onApply?: (config: object) => void;
}

export const ApplyConfigButton: React.FC<ApplyConfigButtonProps> = (props) => {
    const { label, confirmMessage, currentConfig, newConfig, onApply } = props;
    const classes = useClasses();
    const [diffCount, setDiffCount] = React.useState<number>(0);

    React.useEffect(() => {
        if (currentConfig && newConfig) {
            const changes = diffJson(currentConfig, newConfig);
            // Count the number of changed values in the configuration diff
            // Note that the diff is a nested dictionary of changed values
            // that contain any combination of the oldValue and/or newValue
            // so we are really just counting if either oldValue or newValue is present
            // but do not count them twice if both are present
            const changeCount = changes.reduce((count, change) => count + (change.added ? 1 : 0), 0);
            setDiffCount(changeCount);
        }
    }, [currentConfig, newConfig]);

    const handleApply = React.useCallback(() => {
        onApply?.(newConfig);
    }, [newConfig, onApply]);

    const defaultLabel = 'Apply configuration';
    const title = `${label ?? defaultLabel}: ${diffCount} changes`;

    return (
        <>
            <CommandButton
                disabled={diffCount === 0}
                description="Apply configuration"
                label={title}
                dialogContent={{
                    title,
                    content: (
                        <>
                            <p>
                                <Text>{confirmMessage || 'Are you sure you want to apply the configuration?'}</Text>
                            </p>
                            <p>
                                <Text>The following values will be affected:</Text>
                            </p>
                            <div className={classes.configDiff}>
                                <DiffRenderer
                                    source={{
                                        content: JSON.stringify(Utility.sortKeys(currentConfig), null, 2),
                                        label: 'Current',
                                    }}
                                    compare={{
                                        content: JSON.stringify(Utility.sortKeys(newConfig), null, 2),
                                        label: 'New',
                                    }}
                                    wrapLines
                                />
                            </div>
                        </>
                    ),
                    closeLabel: 'Cancel',
                    additionalActions: [
                        <DialogTrigger key="apply" disableButtonEnhancement>
                            <Button appearance="primary" onClick={handleApply}>
                                Confirm
                            </Button>
                        </DialogTrigger>,
                    ],
                    classNames: { dialogSurface: classes.dialogSurface, dialogContent: classes.dialogContent },
                }}
            />
        </>
    );
};


=== File: workbench-app/src/components/Assistants/AssistantAdd.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import {
    AvatarProps,
    Button,
    Divider,
    Menu,
    MenuItem,
    MenuList,
    MenuPopover,
    MenuTrigger,
    Persona,
    makeStyles,
} from '@fluentui/react-components';
import { BotAddRegular, BotRegular, Sparkle24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Assistant } from '../../models/Assistant';
import { useGetAssistantServiceInfosQuery, useGetAssistantsQuery } from '../../services/workbench';
import { Loading } from '../App/Loading';
import { AssistantCreate } from './AssistantCreate';

const useClasses = makeStyles({
    menuList: {
        maxHeight: 'calc(100vh - 200px)',
    },
});

interface AssistantAddProps {
    exceptAssistantIds?: string[];
    onAdd: (assistant: Assistant) => void;
    disabled?: boolean;
}

export const AssistantAdd: React.FC<AssistantAddProps> = (props) => {
    const { exceptAssistantIds, onAdd, disabled } = props;
    const classes = useClasses();
    const { data: assistants, error: getAssistantsError, isLoading: isLoadingAssistants } = useGetAssistantsQuery();
    const {
        data: assistantServiceInfos,
        error: getAssistantServiceInfosError,
        isLoading: isLoadingAssistantServiceInfos,
    } = useGetAssistantServiceInfosQuery({});
    const [assistantCreateOpen, setAssistantCreateOpen] = React.useState(false);

    if (getAssistantsError) {
        const errorMessage = JSON.stringify(getAssistantsError);
        throw new Error(`Error loading assistants: ${errorMessage}`);
    }

    if (getAssistantServiceInfosError) {
        const errorMessage = JSON.stringify(getAssistantServiceInfosError);
        throw new Error(`Error loading assistant service infos: ${errorMessage}`);
    }

    if (isLoadingAssistants || isLoadingAssistantServiceInfos) {
        return <Loading />;
    }

    if (!assistants) {
        throw new Error(`Assistants not found`);
    }

    const handleNewAssistant = () => {
        setAssistantCreateOpen(true);
    };

    const handleAssistantAdd = async (assistant: Assistant) => {
        onAdd(assistant);
    };

    const unusedAssistants = assistants.filter((assistant) => !exceptAssistantIds?.includes(assistant.id));

    const avatarForAssistant = (assistant: Assistant): AvatarProps => {
        const icon = assistantServiceInfos?.find((info) => info.assistantServiceId === assistant.assistantServiceId)
            ?.metadata?._dashboard_card?.[assistant.templateId]?.icon;
        if (icon) {
            return { image: { src: icon }, name: '' };
        }

        return { icon: <BotRegular />, name: '' };
    };

    return (
        <div>
            <AssistantCreate
                open={assistantCreateOpen}
                onOpenChange={(open) => setAssistantCreateOpen(open)}
                onCreate={(assistant) => handleAssistantAdd(assistant)}
            />
            <Menu>
                <MenuTrigger disableButtonEnhancement>
                    <Button disabled={disabled} icon={<BotAddRegular />}>
                        Add assistant
                    </Button>
                </MenuTrigger>
                <MenuPopover className={classes.menuList}>
                    <MenuList>
                        {unusedAssistants.length === 0 && <MenuItem>No assistants available</MenuItem>}
                        {unusedAssistants
                            .sort((a, b) => a.name.toLocaleLowerCase().localeCompare(b.name.toLocaleLowerCase()))
                            .map((assistant) => (
                                <MenuItem key={assistant.id} onClick={() => handleAssistantAdd(assistant)}>
                                    <Persona
                                        name={assistant.name}
                                        size="medium"
                                        avatar={avatarForAssistant(assistant)}
                                        textAlignment="center"
                                        presence={
                                            !assistant.assistantServiceOnline
                                                ? {
                                                      status: 'offline',
                                                  }
                                                : undefined
                                        }
                                    />
                                </MenuItem>
                            ))}
                    </MenuList>
                    <Divider />
                    <MenuItem icon={<Sparkle24Regular />} onClick={handleNewAssistant}>
                        Create new assistant
                    </MenuItem>
                </MenuPopover>
            </Menu>
        </div>
    );
};


=== File: workbench-app/src/components/Assistants/AssistantConfigExportButton.tsx ===
import { Menu, MenuItem, MenuList, MenuPopover, MenuTrigger, SplitButton } from '@fluentui/react-components';
import YAML from 'js-yaml';
import React from 'react';

interface AssistantConfigExportButtonProps {
    config: object;
    assistantId: string;
}

export const AssistantConfigExportButton: React.FC<AssistantConfigExportButtonProps> = ({ config, assistantId }) => {
    const exportConfig = (format: 'json' | 'yaml') => {
        let content = '';
        let filename = `config_${assistantId}`;

        try {
            if (format === 'yaml') {
                content = YAML.dump(config);
                filename += '.yaml';
            } else {
                content = JSON.stringify(config, null, 2);
                filename += '.json';
            }

            const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();

            URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error while generating config file:', error);
        }
    };

    const primaryActionButtonProps = {
        onClick: () => exportConfig('json'),
    };

    return (
        <Menu positioning="below-end">
            <MenuTrigger disableButtonEnhancement>
                {(triggerProps) => (
                    <SplitButton menuButton={triggerProps} primaryActionButton={primaryActionButtonProps}>
                        Export Config
                    </SplitButton>
                )}
            </MenuTrigger>

            <MenuPopover>
                <MenuList>
                    <MenuItem onClick={() => exportConfig('json')}>JSON Format</MenuItem>
                    <MenuItem onClick={() => exportConfig('yaml')}>YAML Format</MenuItem>
                </MenuList>
            </MenuPopover>
        </Menu>
    );
};


=== File: workbench-app/src/components/Assistants/AssistantConfigImportButton.tsx ===
import { Button } from '@fluentui/react-components';
import YAML from 'js-yaml';
import React, { useRef } from 'react';
import { useAppDispatch } from '../../redux/app/hooks'; // Import the relevant hooks
import { addError } from '../../redux/features/app/appSlice'; // Import the error action

interface AssistantConfigImportButtonProps {
    onImport: (config: object) => void;
}

export const AssistantConfigImportButton: React.FC<AssistantConfigImportButtonProps> = ({ onImport }) => {
    const fileInputRef = useRef<HTMLInputElement | null>(null);
    const dispatch = useAppDispatch(); // Use the dispatch hook

    const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target?.files?.[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const content = e.target?.result as string;
                    let importedConfig;

                    if (file.name.endsWith('.yaml') || file.name.endsWith('.yml')) {
                        importedConfig = YAML.load(content);
                    } else {
                        importedConfig = JSON.parse(content);
                    }

                    if (typeof importedConfig === 'object' && importedConfig !== null) {
                        onImport(importedConfig as object);
                    } else {
                        throw new Error('Invalid configuration format');
                    }
                } catch (error) {
                    console.error('Error reading configuration file:', error);
                    dispatch(
                        addError({
                            title: 'Import Error',
                            message:
                                'There was an error importing the configuration file. Please check the file format and contents.',
                        }),
                    );
                }
            };
            reader.readAsText(file);
        }
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    return (
        <div>
            <input type="file" hidden ref={fileInputRef} accept=".json,.yaml,.yml" onChange={handleFileChange} />
            <Button onClick={() => fileInputRef.current?.click()}>Import Config</Button>
        </div>
    );
};


=== File: workbench-app/src/components/Assistants/AssistantConfiguration.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button, Divider, makeStyles, shorthands, Text, tokens } from '@fluentui/react-components';
import { Warning24Filled } from '@fluentui/react-icons';
import Form from '@rjsf/fluentui-rc';
import { RegistryWidgetsType, RJSFSchema } from '@rjsf/utils';
import validator from '@rjsf/validator-ajv8';
import debug from 'debug';
import React from 'react';
import { Constants } from '../../Constants';
import { Utility } from '../../libs/Utility';
import { Assistant } from '../../models/Assistant';
import { useGetConfigQuery, useUpdateConfigMutation } from '../../services/workbench';
import { ConfirmLeave } from '../App/ConfirmLeave';
import { ErrorMessageBar } from '../App/ErrorMessageBar';
import { BaseModelEditorWidget } from '../App/FormWidgets/BaseModelEditorWidget';
import { CustomizedArrayFieldTemplate } from '../App/FormWidgets/CustomizedArrayFieldTemplate';
import CustomizedFieldTemplate from '../App/FormWidgets/CustomizedFieldTemplate';
import { CustomizedObjectFieldTemplate } from '../App/FormWidgets/CustomizedObjectFieldTemplate';
import { InspectableWidget } from '../App/FormWidgets/InspectableWidget';
import { Loading } from '../App/Loading';
import { ApplyConfigButton } from './ApplyConfigButton';
import { AssistantConfigExportButton } from './AssistantConfigExportButton';
import { AssistantConfigImportButton } from './AssistantConfigImportButton';

const log = debug(Constants.debug.root).extend('AssistantEdit');

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
    actions: {
        position: 'sticky',
        top: 0,
        display: 'flex',
        flexDirection: 'row',
        gap: '8px',
        zIndex: tokens.zIndexContent,
        backgroundColor: 'white',
        padding: '8px',
        ...shorthands.border(tokens.strokeWidthThin, 'solid', tokens.colorNeutralStroke1),
    },
    warning: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        fontWeight: tokens.fontWeightSemibold,
        color: tokens.colorPaletteRedForeground1,
    },
});

interface AssistantConfigurationProps {
    assistant: Assistant;
    onIsDirtyChange?: (isDirty: boolean) => void;
}

export const AssistantConfiguration: React.FC<AssistantConfigurationProps> = (props) => {
    const { assistant, onIsDirtyChange } = props;
    const classes = useClasses();
    const {
        data: config,
        error: configError,
        isLoading: isLoadingConfig,
    } = useGetConfigQuery({ assistantId: assistant.id });
    const [updateConfig] = useUpdateConfigMutation();
    const [formData, setFormData] = React.useState<object>();
    const [isDirty, setDirty] = React.useState(false);
    const [isValid, setValid] = React.useState(true);
    const [configErrorMessage, setConfigErrorMessage] = React.useState<string>();

    React.useEffect(() => {
        setConfigErrorMessage(configError ? JSON.stringify(configError) : undefined);
    }, [configError]);

    React.useEffect(() => {
        if (onIsDirtyChange) {
            onIsDirtyChange(isDirty);
        }
    }, [isDirty, onIsDirtyChange]);

    React.useEffect(() => {
        if (isLoadingConfig) return;
        setFormData(config?.config);
    }, [isLoadingConfig, config]);

    const handleSubmit = async (updatedConfig: object) => {
        if (!config) return;
        await updateConfig({ assistantId: assistant.id, config: { ...config, config: updatedConfig } });
        setDirty(false);
    };

    const defaults = React.useMemo(() => {
        if (config?.jsonSchema) {
            return extractDefaultsFromSchema(config.jsonSchema);
        }
        return {};
    }, [config]);

    React.useEffect(() => {
        if (config?.config && formData) {
            // Compare the current form data with the original config to determine if the form is dirty
            const diff = Utility.deepDiff(config.config, formData);
            setDirty(Object.keys(diff).length > 0);
        }

        if (config?.jsonSchema && formData) {
            // Validate the form data against the JSON schema
            const { errors } = validator.validateFormData(
                formData,
                config.jsonSchema,
                undefined,
                undefined,
                config.uiSchema,
            );
            setValid(errors.length === 0);
        }
    }, [config, formData]);

    const restoreConfig = (config: object) => {
        log('Restoring config', config);
        setFormData(config);
    };

    const mergeConfigurations = (uploadedConfig: object) => {
        if (!config) return;

        const updatedConfig = Utility.deepMerge(config.config, uploadedConfig);
        setFormData(updatedConfig);
    };

    const widgets: RegistryWidgetsType = {
        inspectable: InspectableWidget,
        baseModelEditor: BaseModelEditorWidget,
    };

    const templates = {
        ArrayFieldTemplate: CustomizedArrayFieldTemplate,
        FieldTemplate: CustomizedFieldTemplate,
        ObjectFieldTemplate: CustomizedObjectFieldTemplate,
    };

    if (isLoadingConfig) {
        return <Loading />;
    }

    return (
        <div className={classes.root}>
            <Text size={400} weight="semibold">
                Assistant Configuration
            </Text>
            {!config ? (
                <ErrorMessageBar title="Error loading assistant config" error={configErrorMessage} />
            ) : (
                <>
                    <Text size={300} italic color="neutralSecondary">
                        Please practice Responsible AI when configuring your assistant. See the{' '}
                        <a
                            href="https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/system-message"
                            target="_blank"
                            rel="noreferrer"
                        >
                            Microsoft Azure OpenAI Service: System message templates
                        </a>{' '}
                        page for suggestions regarding content for the prompts below.
                    </Text>
                    <Divider />
                    <ConfirmLeave isDirty={isDirty} />
                    <div className={classes.actions}>
                        <Button appearance="primary" form="assistant-config-form" type="submit" disabled={!isDirty}>
                            Save
                        </Button>
                        <ApplyConfigButton
                            label="Reset"
                            confirmMessage="Are you sure you want to reset the changes to configuration?"
                            currentConfig={formData}
                            newConfig={config.config}
                            onApply={restoreConfig}
                        />
                        <ApplyConfigButton
                            label="Load defaults"
                            confirmMessage="Are you sure you want to load the default configuration?"
                            currentConfig={formData}
                            newConfig={defaults}
                            onApply={restoreConfig}
                        />
                        <AssistantConfigExportButton config={config?.config || {}} assistantId={assistant.id} />
                        <AssistantConfigImportButton onImport={mergeConfigurations} />
                        {!isValid && (
                            <div className={classes.warning}>
                                <Warning24Filled /> Configuration has missing or invalid values
                            </div>
                        )}
                    </div>
                    <Form
                        id="assistant-config-form"
                        aria-autocomplete="none"
                        autoComplete="off"
                        widgets={widgets}
                        templates={templates}
                        schema={config.jsonSchema ?? {}}
                        uiSchema={{
                            ...config.uiSchema,
                            'ui:options': {
                                ...config.uiSchema?.['ui:options'],
                                collapsible: false,
                                hideTitle: true,
                            },
                            'ui:submitButtonOptions': {
                                norender: true,
                                submitText: 'Save',
                                props: {
                                    disabled: isDirty === false,
                                },
                            },
                        }}
                        validator={validator}
                        liveValidate={true}
                        showErrorList={false}
                        formData={formData}
                        onChange={(data) => {
                            setFormData(data.formData);
                        }}
                        onSubmit={(data, event) => {
                            event.preventDefault();
                            handleSubmit(data.formData);
                        }}
                    />
                </>
            )}
        </div>
    );
};

/*
 * Helpers
 */

function extractDefaultsFromSchema(schema: RJSFSchema): any {
    const defaults: any = {};

    function traverse(schema: any, path: string[] = [], rootSchema: any = schema) {
        if (schema.$ref) {
            const refPath = schema.$ref.replace(/^#\/\$defs\//, '').split('/');
            const refSchema = refPath.reduce((acc: any, key: string) => acc?.[key], rootSchema.$defs);
            if (refSchema) {
                traverse(refSchema, path, rootSchema);
            } else {
                console.error(`Reference not found: ${schema.$ref}`);
            }
        }

        if (schema.default !== undefined) {
            setDefault(defaults, path, schema.default);
        }

        if (schema.properties) {
            for (const key in schema.properties) {
                traverse(schema.properties[key], [...path, key], rootSchema);
            }
        }
    }

    function setDefault(obj: any, path: string[], value: any) {
        let current = obj;
        for (let i = 0; i < path.length - 1; i++) {
            if (!current[path[i]]) {
                current[path[i]] = {};
            } else {
                // Create a new object to avoid modifying read-only properties
                current[path[i]] = { ...current[path[i]] };
            }
            current = current[path[i]];
        }
        current[path[path.length - 1]] = value;
    }

    traverse(schema);
    return defaults;
}


=== File: workbench-app/src/components/Assistants/AssistantConfigure.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { DialogOpenChangeData, DialogOpenChangeEvent, makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { Assistant } from '../../models/Assistant';
import { DialogControl } from '../App/DialogControl';
import { AssistantConfiguration } from './AssistantConfiguration';

const useClasses = makeStyles({
    dialogSurface: {
        maxWidth: 'calc(min(1000px, 100vw) - 32px)',
        minWidth: 'min(600px, 100vw)',
        width: 'fit-content',
    },
    dialogContent: {
        height: 'calc(100vh - 150px)',
        width: 'calc(min(1000px, 100vw) - 100px)',
        paddingRight: '8px',
        boxSizing: 'border-box',
        overflowY: 'auto',
    },
    content: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
});

interface AssistantConfigureDialogProps {
    assistant?: Assistant;
    open: boolean;
    onOpenChange: (event: DialogOpenChangeEvent, data: DialogOpenChangeData) => void;
}

export const AssistantConfigureDialog: React.FC<AssistantConfigureDialogProps> = (props) => {
    const { assistant, open, onOpenChange } = props;
    const classes = useClasses();
    const [isDirty, setIsDirty] = React.useState(false);

    const handleOpenChange = React.useCallback(
        (event: DialogOpenChangeEvent, data: DialogOpenChangeData) => {
            if (data.open) {
                setIsDirty(false);
                return;
            }

            if (isDirty) {
                const result = window.confirm('Are you sure you want to close without saving?');
                if (!result) {
                    return;
                }
            }

            setIsDirty(false);
            onOpenChange(event, data);
        },
        [isDirty, onOpenChange],
    );

    return (
        <DialogControl
            open={open}
            onOpenChange={handleOpenChange}
            title={assistant && `Configure "${assistant.name}"`}
            content={
                <div className={classes.content}>
                    {assistant && <AssistantConfiguration assistant={assistant} onIsDirtyChange={setIsDirty} />}
                </div>
            }
            classNames={{
                dialogSurface: classes.dialogSurface,
                dialogContent: classes.dialogContent,
            }}
        />
    );
};


=== File: workbench-app/src/components/Assistants/AssistantCreate.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Checkbox,
    Dialog,
    DialogActions,
    DialogBody,
    DialogContent,
    DialogOpenChangeData,
    DialogOpenChangeEvent,
    DialogSurface,
    DialogTitle,
    DialogTrigger,
    Divider,
    Dropdown,
    Field,
    Input,
    Label,
    Option,
    OptionGroup,
    Tooltip,
    makeStyles,
    tokens,
} from '@fluentui/react-components';
import { Info16Regular, PresenceAvailableRegular } from '@fluentui/react-icons';
import React from 'react';
import { Constants } from '../../Constants';
import { Assistant } from '../../models/Assistant';
import { AssistantServiceInfo } from '../../models/AssistantServiceInfo';
import {
    useCreateAssistantMutation,
    useGetAssistantServiceInfosQuery,
    useGetAssistantsQuery,
} from '../../services/workbench';
import { AssistantImport } from './AssistantImport';

const useClasses = makeStyles({
    dialogContent: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
    option: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: tokens.spacingHorizontalXS,
    },
    optionDescription: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalXS,
    },
});

interface AssistantCreateProps {
    open: boolean;
    onOpenChange?: (open: boolean) => void;
    onCreate?: (assistant: Assistant) => void;
    onImport?: (result: { assistantIds: string[]; conversationIds: string[] }) => void;
}

export const AssistantCreate: React.FC<AssistantCreateProps> = (props) => {
    const { open, onOpenChange, onCreate, onImport } = props;
    const classes = useClasses();
    const { refetch: refetchAssistants } = useGetAssistantsQuery();
    const {
        data: assistantServices,
        refetch: refetchAssistantServices,
        error: getAssistantServicesError,
        isLoading: isLoadingAssistantServices,
    } = useGetAssistantServiceInfosQuery({});
    const {
        data: myAssistantServices,
        refetch: refetchMyAssistantServices,
        error: getMyAssistantServicesError,
        isLoading: isLoadingMyAssistantServices,
    } = useGetAssistantServiceInfosQuery({ userIds: ['me'] });
    const [createAssistant] = useCreateAssistantMutation();
    const [name, setName] = React.useState('');
    const [assistantServiceId, setAssistantServiceId] = React.useState('');
    const [templateId, setTemplateId] = React.useState('');
    const [manualEntry, setManualEntry] = React.useState(false);
    const [submitted, setSubmitted] = React.useState(false);

    if (getAssistantServicesError) {
        const errorMessage = JSON.stringify(getAssistantServicesError);
        throw new Error(`Error loading assistant services: ${errorMessage}`);
    }
    if (getMyAssistantServicesError) {
        const errorMessage = JSON.stringify(getMyAssistantServicesError);
        throw new Error(`Error loading my assistant services: ${errorMessage}`);
    }

    const handleSave = async () => {
        if (submitted) {
            return;
        }
        setSubmitted(true);

        try {
            const assistant = await createAssistant({
                name,
                assistantServiceId,
                templateId: templateId,
            }).unwrap();
            await refetchAssistants();
            onOpenChange?.(false);
            onCreate?.(assistant);
        } finally {
            setSubmitted(false);
        }
    };

    React.useEffect(() => {
        if (!open) {
            return;
        }

        refetchAssistantServices();
        refetchMyAssistantServices();
        setName('');
        setAssistantServiceId('');
        setManualEntry(false);
        setSubmitted(false);
    }, [open, refetchAssistantServices, refetchMyAssistantServices]);

    const handleOpenChange = React.useCallback(
        (_event: DialogOpenChangeEvent, data: DialogOpenChangeData) => {
            onOpenChange?.(data.open);
        },
        [onOpenChange],
    );

    const handleImport = async (result: { assistantIds: string[]; conversationIds: string[] }) => {
        // actual import already handled inside the AssistantImport component
        onOpenChange?.(false);
        onImport?.(result);
    };

    const handleImportError = () => {
        onOpenChange?.(false);
    };

    const categorizedAssistantServices: Record<string, AssistantServiceInfo[]> = {
        ...(assistantServices ?? [])
            .filter(
                (service) =>
                    !myAssistantServices?.find(
                        (myService) => myService.assistantServiceId === service.assistantServiceId,
                    ),
            )
            .reduce((accumulated, assistantService) => {
                const entry = Object.entries(Constants.assistantCategories).find(([_, serviceIds]) =>
                    serviceIds.includes(assistantService.assistantServiceId),
                );
                const assignedCategory = entry ? entry[0] : 'Other';
                if (!accumulated[assignedCategory]) {
                    accumulated[assignedCategory] = [];
                }
                accumulated[assignedCategory].push(assistantService);
                return accumulated;
            }, {} as Record<string, AssistantServiceInfo[]>),
        'My Services': myAssistantServices ?? [],
    };

    const orderedCategories = [...Object.keys(Constants.assistantCategories), 'Other', 'My Services'].filter(
        (category) => categorizedAssistantServices[category]?.length,
    );

    const options = orderedCategories.map((category) => (
        <OptionGroup key={category} label={category}>
            {(categorizedAssistantServices[category] ?? [])
                .flatMap((assistantService) => {
                    return assistantService.templates.map((template) => ({
                        assistantServiceId: assistantService.assistantServiceId,
                        name: template.name,
                        templateId: template.id,
                        description: template.description,
                    }));
                })
                .toSorted((a, b) => a.name.localeCompare(b.name))
                .map((assistantService) => {
                    const key = JSON.stringify([assistantService.assistantServiceId, assistantService.templateId]);
                    return (
                        <Option key={key} text={assistantService.name} value={key}>
                            <div className={classes.option}>
                                <PresenceAvailableRegular color="green" />
                                <Label weight="semibold">{assistantService.name}</Label>
                                <Tooltip
                                    content={
                                        <div className={classes.optionDescription}>
                                            <Label size="small">
                                                <em>{assistantService.description}</em>
                                            </Label>
                                            <Divider />
                                            <Label size="small">Assistant service ID:</Label>
                                            <Label size="small">{assistantService.assistantServiceId}</Label>
                                            <Label size="small">Assistant type ID:</Label>
                                            <Label size="small">{assistantService.templateId}</Label>
                                        </div>
                                    }
                                    relationship="description"
                                >
                                    <Info16Regular />
                                </Tooltip>
                            </div>
                        </Option>
                    );
                })}
        </OptionGroup>
    ));

    if (isLoadingAssistantServices || isLoadingMyAssistantServices) {
        return null;
    }

    return (
        <Dialog open={open} onOpenChange={handleOpenChange}>
            <DialogSurface>
                <form
                    onSubmit={(event) => {
                        event.preventDefault();
                        handleSave();
                    }}
                >
                    <DialogBody>
                        <DialogTitle>New Assistant</DialogTitle>
                        <DialogContent className={classes.dialogContent}>
                            {!manualEntry && (
                                <Field label="Assistant Service">
                                    <Dropdown
                                        placeholder="Select an assistant service"
                                        disabled={submitted}
                                        onOptionSelect={(_event, data) => {
                                            if (data.optionValue) {
                                                const [assistantServiceId, templateId] = JSON.parse(data.optionValue);
                                                setAssistantServiceId(assistantServiceId);
                                                setTemplateId(templateId);
                                            }

                                            if (data.optionText && name === '') {
                                                setName(data.optionText);
                                            }
                                        }}
                                    >
                                        {options}
                                    </Dropdown>
                                </Field>
                            )}
                            {manualEntry && (
                                <Field label="Assistant Service ID">
                                    <Input
                                        disabled={submitted}
                                        value={assistantServiceId}
                                        onChange={(_event, data) => setAssistantServiceId(data?.value)}
                                        aria-autocomplete="none"
                                    />
                                </Field>
                            )}
                            <Field label="Name">
                                <Input
                                    disabled={submitted}
                                    value={name}
                                    onChange={(_event, data) => setName(data?.value)}
                                    aria-autocomplete="none"
                                />
                            </Field>
                            <button disabled={!name || !assistantServiceId || submitted} type="submit" hidden />
                        </DialogContent>
                        <DialogActions>
                            <Checkbox
                                style={{ whiteSpace: 'nowrap' }}
                                label="Enter Assistant Service ID"
                                checked={manualEntry}
                                onChange={(_event, data) => setManualEntry(data.checked === true)}
                            />
                            <AssistantImport disabled={submitted} onImport={handleImport} onError={handleImportError} />
                            <DialogTrigger disableButtonEnhancement>
                                <Button appearance="secondary">Cancel</Button>
                            </DialogTrigger>
                            <DialogTrigger disableButtonEnhancement>
                                <Button
                                    disabled={!name || !assistantServiceId || submitted}
                                    appearance="primary"
                                    onClick={handleSave}
                                >
                                    {submitted ? 'Saving...' : 'Save'}
                                </Button>
                            </DialogTrigger>
                        </DialogActions>
                    </DialogBody>
                </form>
            </DialogSurface>
        </Dialog>
    );
};


=== File: workbench-app/src/components/Assistants/AssistantDelete.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogTrigger, Label } from '@fluentui/react-components';
import { Delete24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Assistant } from '../../models/Assistant';
import { useDeleteAssistantMutation } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';

interface AssistantDeleteProps {
    assistant: Assistant;
    onDelete?: () => void;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const AssistantDelete: React.FC<AssistantDeleteProps> = (props) => {
    const { assistant, onDelete, iconOnly, asToolbarButton } = props;
    const [deleteAssistant] = useDeleteAssistantMutation();
    const [submitted, setSubmitted] = React.useState(false);

    const handleDelete = React.useCallback(async () => {
        if (submitted) {
            return;
        }
        setSubmitted(true);

        try {
            await deleteAssistant(assistant.id);
            onDelete?.();
        } finally {
            setSubmitted(false);
        }
    }, [submitted, deleteAssistant, assistant.id, onDelete]);

    return (
        <CommandButton
            description="Delete assistant"
            icon={<Delete24Regular />}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
            label="Delete"
            dialogContent={{
                title: 'Delete Assistant',
                content: (
                    <p>
                        <Label> Are you sure you want to delete this assistant?</Label>
                    </p>
                ),
                closeLabel: 'Cancel',
                additionalActions: [
                    <DialogTrigger key="delete" disableButtonEnhancement>
                        <Button appearance="primary" onClick={handleDelete} disabled={submitted}>
                            {submitted ? 'Deleting...' : 'Delete'}
                        </Button>
                    </DialogTrigger>,
                ],
            }}
        />
    );
};


=== File: workbench-app/src/components/Assistants/AssistantDuplicate.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogTrigger } from '@fluentui/react-components';
import { SaveCopy24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useWorkbenchService } from '../../libs/useWorkbenchService';
import { Assistant } from '../../models/Assistant';
import { CommandButton } from '../App/CommandButton';

interface AssistantDuplicateProps {
    assistant: Assistant;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
    onDuplicate?: (assistantId: string) => void;
    onDuplicateError?: (error: Error) => void;
}

export const AssistantDuplicate: React.FC<AssistantDuplicateProps> = (props) => {
    const { assistant, iconOnly, asToolbarButton, onDuplicate, onDuplicateError } = props;
    const workbenchService = useWorkbenchService();
    const [submitted, setSubmitted] = React.useState(false);

    const duplicateAssistant = React.useCallback(async () => {
        if (submitted) {
            return;
        }
        setSubmitted(true);

        try {
            const newAssistantId = await workbenchService.exportThenImportAssistantAsync(assistant.id);
            onDuplicate?.(newAssistantId);
        } catch (error) {
            onDuplicateError?.(error as Error);
        } finally {
            setSubmitted(false);
        }
    }, [submitted, workbenchService, assistant.id, onDuplicate, onDuplicateError]);

    return (
        <CommandButton
            description="Duplicate assistant"
            icon={<SaveCopy24Regular />}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
            label="Duplicate"
            dialogContent={{
                title: 'Duplicate assistant',
                content: <p>Are you sure you want to duplicate this assistant?</p>,
                closeLabel: 'Cancel',
                additionalActions: [
                    <DialogTrigger key="duplicate" disableButtonEnhancement>
                        <Button appearance="primary" onClick={duplicateAssistant} disabled={submitted}>
                            {submitted ? 'Duplicating...' : 'Duplicate'}
                        </Button>
                    </DialogTrigger>,
                ],
            }}
        />
    );
};


=== File: workbench-app/src/components/Assistants/AssistantExport.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { useExportUtility } from '../../libs/useExportUtility';
import { ContentExport } from '../App/ContentExport';

interface AssistantExportProps {
    assistantId: string;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const AssistantExport: React.FC<AssistantExportProps> = (props) => {
    const { assistantId, iconOnly, asToolbarButton } = props;
    const { exportAssistantFunction } = useExportUtility();

    return (
        <ContentExport
            id={assistantId}
            contentTypeLabel="assistant"
            exportFunction={exportAssistantFunction}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
        />
    );
};


=== File: workbench-app/src/components/Assistants/AssistantImport.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { ArrowUpload24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useWorkbenchService } from '../../libs/useWorkbenchService';
import { CommandButton } from '../App/CommandButton';

interface AssistantImportProps {
    disabled?: boolean;
    iconOnly?: boolean;
    label?: string;
    asToolbarButton?: boolean;
    onImport?: (result: { assistantIds: string[]; conversationIds: string[] }) => void;
    onError?: (error: Error) => void;
}

export const AssistantImport: React.FC<AssistantImportProps> = (props) => {
    const { disabled, iconOnly, label, asToolbarButton, onImport, onError } = props;
    const [uploading, setUploading] = React.useState(false);
    const fileInputRef = React.useRef<HTMLInputElement>(null);
    const workbenchService = useWorkbenchService();

    const onFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        if (uploading || !event.target.files) {
            return;
        }
        setUploading(true);

        try {
            const file = event.target.files[0];
            const result = await workbenchService.importConversationsAsync(file);
            onImport?.(result);

            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        } catch (error) {
            onError?.(error as Error);
        } finally {
            setUploading(false);
        }
    };

    const onUpload = async () => {
        fileInputRef.current?.click();
    };

    return (
        <div>
            <input hidden ref={fileInputRef} type="file" onChange={onFileChange} />
            <CommandButton
                disabled={uploading || disabled}
                description="Import assistant"
                icon={<ArrowUpload24Regular />}
                iconOnly={iconOnly}
                asToolbarButton={asToolbarButton}
                label={label ?? (uploading ? 'Uploading...' : 'Import')}
                onClick={onUpload}
            />
        </div>
    );
};


=== File: workbench-app/src/components/Assistants/AssistantRemove.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogOpenChangeData, DialogOpenChangeEvent } from '@fluentui/react-components';
import { PlugDisconnectedRegular } from '@fluentui/react-icons';
import React from 'react';
import { Utility } from '../../libs/Utility';
import { useNotify } from '../../libs/useNotify';
import { Assistant } from '../../models/Assistant';
import {
    useCreateConversationMessageMutation,
    useGetConversationParticipantsQuery,
    useRemoveConversationParticipantMutation,
} from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';
import { DialogControl } from '../App/DialogControl';

const useAssistantRemoveControls = (assistant?: Assistant, conversationId?: string) => {
    const [createConversationMessage] = useCreateConversationMessageMutation();
    const [removeConversationParticipant] = useRemoveConversationParticipantMutation();
    const { refetch: refetchParticipants } = useGetConversationParticipantsQuery(conversationId ?? '', {
        skip: !conversationId,
    });
    const [submitted, setSubmitted] = React.useState(false);

    const handleRemove = React.useCallback(
        async (onRemove?: (assistant: Assistant) => Promise<void>, onError?: (error: Error) => void) => {
            if (!assistant || !conversationId || submitted) {
                return;
            }

            try {
                await Utility.withStatus(setSubmitted, async () => {
                    await removeConversationParticipant({
                        conversationId: conversationId,
                        participantId: assistant.id,
                    });
                    await onRemove?.(assistant);

                    const content = `${assistant.name} removed from conversation`;
                    await createConversationMessage({
                        conversationId: conversationId,
                        content,
                        messageType: 'notice',
                    });

                    // Refetch participants to update the assistant name in the list
                    if (conversationId) {
                        await refetchParticipants();
                    }
                });
            } catch (error) {
                onError?.(error as Error);
            }
        },
        [
            assistant,
            conversationId,
            createConversationMessage,
            refetchParticipants,
            removeConversationParticipant,
            submitted,
        ],
    );

    const removeAssistantForm = React.useCallback(
        (onRemove?: (assistant: Assistant) => Promise<void>) => (
            <form
                onSubmit={(event) => {
                    event.preventDefault();
                    handleRemove(onRemove);
                }}
            >
                <p>
                    Are you sure you want to remove assistant <strong>{assistant?.name}</strong> from this conversation?
                </p>
            </form>
        ),
        [assistant?.name, handleRemove],
    );

    const removeAssistantButton = React.useCallback(
        (onRemove?: (assistant: Assistant) => Promise<void>, onError?: (error: Error) => void) => (
            <Button
                key="remove"
                disabled={submitted}
                onClick={() => handleRemove(onRemove, onError)}
                appearance="primary"
            >
                {submitted ? 'Removing...' : 'Remove'}
            </Button>
        ),
        [handleRemove, submitted],
    );

    return {
        removeAssistantForm,
        removeAssistantButton,
    };
};

interface AssistantRemoveDialogProps {
    assistant?: Assistant;
    conversationId?: string;
    onRemove?: (assistant: Assistant) => Promise<void>;
    open: boolean;
    onOpenChange: (event: DialogOpenChangeEvent, data: DialogOpenChangeData) => void;
}

export const AssistantRemoveDialog: React.FC<AssistantRemoveDialogProps> = (props) => {
    const { assistant, conversationId, open, onOpenChange, onRemove } = props;
    const { removeAssistantForm, removeAssistantButton } = useAssistantRemoveControls(assistant, conversationId);
    const { notifyWarning } = useNotify();

    const handleError = React.useCallback(
        (error: Error) => {
            notifyWarning({
                id: 'assistant-remove-error',
                title: 'Remove assistant failed',
                message: error.message,
            });
        },
        [notifyWarning],
    );

    return (
        <DialogControl
            open={open}
            onOpenChange={onOpenChange}
            title="Remove assistant"
            content={removeAssistantForm(onRemove)}
            closeLabel="Cancel"
            additionalActions={[removeAssistantButton(onRemove, handleError)]}
        />
    );
};

interface AssistantRemoveProps {
    assistant: Assistant;
    conversationId: string;
    disabled?: boolean;
    onRemove?: (assistant: Assistant) => Promise<void>;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const AssistantRemove: React.FC<AssistantRemoveProps> = (props) => {
    const { assistant, conversationId, disabled, onRemove, iconOnly, asToolbarButton } = props;
    const { removeAssistantForm, removeAssistantButton } = useAssistantRemoveControls(assistant, conversationId);

    return (
        <CommandButton
            iconOnly={iconOnly}
            icon={<PlugDisconnectedRegular />}
            label="Remove"
            disabled={disabled}
            description="Remove assistant"
            asToolbarButton={asToolbarButton}
            dialogContent={{
                title: `Remove "${assistant.name}"`,
                content: removeAssistantForm(onRemove),
                closeLabel: 'Cancel',
                additionalActions: [removeAssistantButton(onRemove)],
            }}
        />
    );
};


=== File: workbench-app/src/components/Assistants/AssistantRename.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogOpenChangeData, DialogOpenChangeEvent, Field, Input } from '@fluentui/react-components';
import { EditRegular } from '@fluentui/react-icons';
import React from 'react';
import { Utility } from '../../libs/Utility';
import { useNotify } from '../../libs/useNotify';
import { Assistant } from '../../models/Assistant';
import { useGetConversationParticipantsQuery, useUpdateAssistantMutation } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';
import { DialogControl } from '../App/DialogControl';

const useAssistantRenameControls = (assistant?: Assistant, conversationId?: string) => {
    const [updateAssistant] = useUpdateAssistantMutation();
    const { refetch: refetchParticipants } = useGetConversationParticipantsQuery(conversationId ?? '', {
        skip: !conversationId,
    });
    const [newName, setNewName] = React.useState<string>();
    const [submitted, setSubmitted] = React.useState(false);

    const handleRename = React.useCallback(
        async (onRename?: (id: string, value: string) => Promise<void>, onError?: (error: Error) => void) => {
            if (!assistant || !newName || submitted) {
                return;
            }

            try {
                await Utility.withStatus(setSubmitted, async () => {
                    await updateAssistant({ ...assistant, name: newName });
                    await onRename?.(assistant.id, newName);

                    // Refetch participants to update the assistant name in the list
                    if (conversationId) {
                        await refetchParticipants();
                    }
                });
            } catch (error) {
                onError?.(error as Error);
            }
        },
        [assistant, conversationId, newName, refetchParticipants, submitted, updateAssistant],
    );

    const renameAssistantForm = React.useCallback(
        (onRename?: (id: string, value: string) => Promise<void>) => (
            <form
                onSubmit={(event) => {
                    event.preventDefault();
                    handleRename(onRename);
                }}
            >
                <Field label="Name">
                    <Input
                        disabled={submitted}
                        defaultValue={assistant?.name}
                        onChange={(_event, data) => setNewName(data.value)}
                    />
                </Field>
            </form>
        ),
        [assistant?.name, handleRename, submitted],
    );

    const renameAssistantButton = React.useCallback(
        (onRename?: (id: string, value: string) => Promise<void>, onError?: (error: Error) => void) => (
            <Button
                key="rename"
                disabled={!newName || submitted}
                onClick={() => handleRename(onRename, onError)}
                appearance="primary"
            >
                {submitted ? 'Renaming...' : 'Rename'}
            </Button>
        ),
        [handleRename, newName, submitted],
    );

    return { renameAssistantForm, renameAssistantButton };
};

interface AssistantRenameDialogProps {
    assistant?: Assistant;
    conversationId?: string;
    onRename?: (value: string) => Promise<void>;
    open?: boolean;
    onOpenChange?: (event: DialogOpenChangeEvent, data: DialogOpenChangeData) => void;
}

export const AssistantRenameDialog: React.FC<AssistantRenameDialogProps> = (props) => {
    const { assistant, conversationId, onRename, open, onOpenChange } = props;
    const { renameAssistantForm, renameAssistantButton } = useAssistantRenameControls(assistant, conversationId);
    const { notifyWarning } = useNotify();

    const handleError = React.useCallback(
        (error: Error) => {
            notifyWarning({
                id: 'assistant-rename-error',
                title: 'Rename assistant failed',
                message: error.message,
            });
        },
        [notifyWarning],
    );

    return (
        <DialogControl
            open={open}
            onOpenChange={onOpenChange}
            title="Rename assistant"
            content={renameAssistantForm(onRename)}
            closeLabel="Cancel"
            additionalActions={[renameAssistantButton(onRename, handleError)]}
        />
    );
};

interface AssistantRenameProps {
    assistant: Assistant;
    conversationId?: string;
    disabled?: boolean;
    onRename?: (value: string) => Promise<void>;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const AssistantRename: React.FC<AssistantRenameProps> = (props) => {
    const { assistant, conversationId, disabled, onRename, iconOnly, asToolbarButton } = props;
    const { renameAssistantForm, renameAssistantButton } = useAssistantRenameControls(assistant, conversationId);

    return (
        <CommandButton
            iconOnly={iconOnly}
            icon={<EditRegular />}
            label="Rename"
            disabled={disabled}
            description="Rename assistant"
            asToolbarButton={asToolbarButton}
            dialogContent={{
                title: `Rename assistant`,
                content: renameAssistantForm(onRename),
                closeLabel: 'Cancel',
                additionalActions: [renameAssistantButton(onRename)],
            }}
        />
    );
};


=== File: workbench-app/src/components/Assistants/AssistantServiceInfo.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { DialogOpenChangeData, DialogOpenChangeEvent } from '@fluentui/react-components';
import React from 'react';
import { Assistant } from '../../models/Assistant';
import { DialogControl } from '../App/DialogControl';
import { AssistantServiceMetadata } from './AssistantServiceMetadata';

interface AssistantServiceInfoDialogProps {
    assistant?: Assistant;
    open: boolean;
    onOpenChange: (event: DialogOpenChangeEvent, data: DialogOpenChangeData) => void;
}

export const AssistantServiceInfoDialog: React.FC<AssistantServiceInfoDialogProps> = (props) => {
    const { assistant, open, onOpenChange } = props;

    return (
        <DialogControl
            open={open}
            onOpenChange={onOpenChange}
            title={assistant && `"${assistant?.name}" Service Info`}
            content={assistant && <AssistantServiceMetadata assistantServiceId={assistant.assistantServiceId} />}
            closeLabel="Close"
        />
    );
};


=== File: workbench-app/src/components/Assistants/AssistantServiceMetadata.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Label, Text, makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { AssistantServiceRegistration } from '../../models/AssistantServiceRegistration';
import { useGetAssistantServiceRegistrationsQuery } from '../../services/workbench';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
    data: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalS,
    },
});

interface AssistantServiceMetadataProps {
    assistantServiceId: string;
}

export const AssistantServiceMetadata: React.FC<AssistantServiceMetadataProps> = (props) => {
    const { assistantServiceId } = props;
    const classes = useClasses();

    const {
        data: assistantServices,
        isLoading: isAssistantServicesLoading,
        isError: getAssistantServicesError,
    } = useGetAssistantServiceRegistrationsQuery({});

    if (getAssistantServicesError) {
        const errorMessage = JSON.stringify(getAssistantServicesError);
        throw new Error(`Error loading assistant services: ${errorMessage}`);
    }

    const [assistantService, setAssistantService] = React.useState<AssistantServiceRegistration | undefined>(undefined);

    React.useEffect(() => {
        const service = assistantServices?.find((service) => service.assistantServiceId === assistantServiceId);

        if (service) {
            setAssistantService(service);
        }
    }, [assistantServiceId, assistantServices, setAssistantService]);

    if (isAssistantServicesLoading) return null;
    if (!assistantService) return null;

    return (
        <div className={classes.root}>
            <Text size={400} weight="semibold">
                Assistant Backend Service
            </Text>
            <div className={classes.data}>
                <Label weight="semibold">{assistantService.name}</Label>
                <Label>
                    <em>{assistantService.description}</em>
                </Label>
                <Label size="small">Assistant service ID: {assistantService.assistantServiceId}</Label>
                <Label size="small">Hosted at: {assistantService.assistantServiceUrl}</Label>
                <Label size="small">
                    Created by: {assistantService.createdByUserName} [{assistantService.createdByUserId}]
                </Label>
            </div>
        </div>
    );
};


=== File: workbench-app/src/components/Assistants/MyAssistants.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Bot24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Assistant } from '../../models/Assistant';
import { useGetAssistantsQuery } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';
import { MiniControl } from '../App/MiniControl';
import { MyItemsManager } from '../App/MyItemsManager';
import { AssistantCreate } from './AssistantCreate';
import { AssistantDelete } from './AssistantDelete';
import { AssistantDuplicate } from './AssistantDuplicate';
import { AssistantExport } from './AssistantExport';
import { AssistantImport } from './AssistantImport';

interface MyAssistantsProps {
    assistants?: Assistant[];
    title?: string;
    hideInstruction?: boolean;
    onCreate?: (assistant: Assistant) => void;
}

export const MyAssistants: React.FC<MyAssistantsProps> = (props) => {
    const { assistants, title, hideInstruction, onCreate } = props;
    const { refetch: refetchAssistants } = useGetAssistantsQuery();
    const [assistantCreateOpen, setAssistantCreateOpen] = React.useState(false);

    const handleAssistantCreate = async (assistant: Assistant) => {
        await refetchAssistants();
        onCreate?.(assistant);
    };

    const handleAssistantImport = async (result: { assistantIds: string[]; conversationIds: string[] }) => {
        (await refetchAssistants().unwrap())
            .filter((assistant) => result.assistantIds.includes(assistant.id))
            .forEach((assistant) => onCreate?.(assistant));
    };

    return (
        <MyItemsManager
            items={assistants
                ?.toSorted((a, b) => a.name.localeCompare(b.name))
                .map((assistant) => (
                    <MiniControl
                        key={assistant.id}
                        icon={<Bot24Regular />}
                        label={assistant?.name}
                        linkUrl={`/assistant/${encodeURIComponent(assistant.id)}/edit`}
                        actions={
                            <>
                                <AssistantExport assistantId={assistant.id} iconOnly />
                                <AssistantDuplicate assistant={assistant} iconOnly />
                                <AssistantDelete assistant={assistant} iconOnly />
                            </>
                        }
                    />
                ))}
            title={title ?? 'My Assistants'}
            itemLabel="Assistant"
            hideInstruction={hideInstruction}
            actions={
                <>
                    <CommandButton
                        icon={<Bot24Regular />}
                        label={`New Assistant`}
                        description={`Select an assistant service and create a new assistant instance`}
                        onClick={() => setAssistantCreateOpen(true)}
                    />
                    <AssistantCreate
                        open={assistantCreateOpen}
                        onOpenChange={(open) => setAssistantCreateOpen(open)}
                        onCreate={handleAssistantCreate}
                        onImport={handleAssistantImport}
                    />
                    <AssistantImport onImport={handleAssistantImport} />
                </>
            }
        />
    );
};


=== File: workbench-app/src/components/Conversations/Canvas/AssistantCanvas.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { Assistant } from '../../../models/Assistant';
import { useGetConversationStateDescriptionsQuery } from '../../../services/workbench';
import { ErrorMessageBar } from '../../App/ErrorMessageBar';
import { Loading } from '../../App/Loading';
import { AssistantInspectorList } from './AssistantInspectorList';

const useClasses = makeStyles({
    inspectors: {
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: tokens.colorNeutralBackgroundAlpha,
        height: '100%',
        maxHeight: '100%',
        overflowY: 'auto',
        overflowX: 'hidden',
    },
});

interface AssistantCanvasProps {
    assistant: Assistant;
    conversationId: string;
}

export const AssistantCanvas: React.FC<AssistantCanvasProps> = (props) => {
    const { assistant, conversationId } = props;
    const classes = useClasses();
    const [stateDescriptionsErrorMessage, setStateDescriptionsErrorMessage] = React.useState<string>();

    const {
        data: stateDescriptions,
        error: stateDescriptionsError,
        isLoading: isLoadingStateDescriptions,
    } = useGetConversationStateDescriptionsQuery({ assistantId: assistant.id, conversationId: conversationId });

    React.useEffect(() => {
        const errorMessage = stateDescriptionsError ? JSON.stringify(stateDescriptionsError) : undefined;
        if (stateDescriptionsErrorMessage !== errorMessage) {
            setStateDescriptionsErrorMessage(errorMessage);
        }
    }, [stateDescriptionsError, stateDescriptionsErrorMessage]);

    // watching fetching instead of load, to avoid passing the old data on assistant id change
    if (isLoadingStateDescriptions && !stateDescriptionsErrorMessage) {
        return <Loading />;
    }

    const enabledStateDescriptions = stateDescriptions?.filter((stateDescription) => stateDescription.enabled) || [];

    return (
        <div className={classes.inspectors}>
            {enabledStateDescriptions.length === 0 ? (
                stateDescriptionsErrorMessage ? (
                    <ErrorMessageBar title="Failed to load assistant states" error={stateDescriptionsErrorMessage} />
                ) : (
                    <div>No states found for this assistant</div>
                )
            ) : (
                <AssistantInspectorList
                    conversationId={conversationId}
                    assistant={assistant}
                    stateDescriptions={enabledStateDescriptions}
                />
            )}
        </div>
    );
};


=== File: workbench-app/src/components/Conversations/Canvas/AssistantCanvasList.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Overflow, OverflowItem, Tab, TabList, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { useChatCanvasController } from '../../../libs/useChatCanvasController';
import { Assistant } from '../../../models/Assistant';
import { Conversation } from '../../../models/Conversation';
import { OverflowMenu, OverflowMenuItemData } from '../../App/OverflowMenu';
import { AssistantCanvas } from './AssistantCanvas';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
    },
    noAssistants: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        ...shorthands.padding(tokens.spacingVerticalS),
    },
    header: {
        overflow: 'hidden',
        ...shorthands.padding(tokens.spacingVerticalS),
        ...shorthands.borderBottom(tokens.strokeWidthThin, 'solid', tokens.colorNeutralStroke1),
    },
});

interface AssistantCanvasListProps {
    selectedAssistant?: Assistant;
    conversationAssistants: Assistant[];
    conversation: Conversation;
}

export const AssistantCanvasList: React.FC<AssistantCanvasListProps> = (props) => {
    const { selectedAssistant, conversationAssistants, conversation } = props;
    const classes = useClasses();
    const chatCanvasController = useChatCanvasController();

    const tabItems = React.useMemo(
        () =>
            conversationAssistants.slice().map(
                (assistant): OverflowMenuItemData => ({
                    id: assistant.id,
                    name: assistant.name,
                }),
            ),
        [conversationAssistants],
    );

    const handleTabSelect = React.useCallback(
        (id: string) => {
            // Find the assistant that corresponds to the selected tab
            const conversationAssistant = conversationAssistants.find(
                (conversationAssistant) => conversationAssistant.id === id,
            );

            // Set the new assistant as the active assistant
            // If we can't find the assistant, we'll set the assistant to undefined
            chatCanvasController.transitionToState({
                selectedAssistantId: conversationAssistant?.id,
                selectedAssistantStateId: undefined,
            });
        },
        [chatCanvasController, conversationAssistants],
    );

    const assistant = React.useMemo(
        () => selectedAssistant ?? conversationAssistants[0],
        [selectedAssistant, conversationAssistants],
    );

    if (conversationAssistants.length === 1) {
        // Only one assistant, no need to show tabs, just show the single assistant
        return <AssistantCanvas assistant={conversationAssistants[0]} conversationId={conversation.id} />;
    }

    // Multiple assistants, show tabs
    return (
        <div className={classes.root}>
            <div className={classes.header}>
                <Overflow minimumVisible={1}>
                    <TabList
                        selectedValue={assistant.id}
                        onTabSelect={(_, data) => handleTabSelect(data.value as string)}
                        size="small"
                    >
                        {tabItems.map((tabItem) => (
                            <OverflowItem
                                key={tabItem.id}
                                id={tabItem.id}
                                priority={tabItem.id === assistant.id ? 2 : 1}
                            >
                                <Tab value={tabItem.id}>{tabItem.name}</Tab>
                            </OverflowItem>
                        ))}
                        <OverflowMenu items={tabItems} onItemSelect={handleTabSelect} />
                    </TabList>
                </Overflow>
            </div>
            <AssistantCanvas assistant={assistant} conversationId={conversation.id} />
        </div>
    );
};


=== File: workbench-app/src/components/Conversations/Canvas/AssistantInspector.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button, Text, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import { ArrowDownloadRegular } from '@fluentui/react-icons';
import {} from '@rjsf/core';
import Form from '@rjsf/fluentui-rc';
import { RegistryWidgetsType } from '@rjsf/utils';
import validator from '@rjsf/validator-ajv8';
import React from 'react';
import { ConversationState } from '../../../models/ConversationState';
import { ConversationStateDescription } from '../../../models/ConversationStateDescription';
import { useUpdateConversationStateMutation } from '../../../services/workbench';
import { CustomizedArrayFieldTemplate } from '../../App/FormWidgets/CustomizedArrayFieldTemplate';
import { CustomizedObjectFieldTemplate } from '../../App/FormWidgets/CustomizedObjectFieldTemplate';
import { InspectableWidget } from '../../App/FormWidgets/InspectableWidget';
import { CodeContentRenderer } from '../ContentRenderers/CodeContentRenderer';
import { ContentListRenderer } from '../ContentRenderers/ContentListRenderer';
import { ContentRenderer } from '../ContentRenderers/ContentRenderer';
import { MilkdownEditorWrapper } from '../ContentRenderers/MarkdownEditorRenderer';
import { DebugInspector } from '../DebugInspector';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
    },
    header: {
        flexShrink: 0,
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
        ...shorthands.padding(tokens.spacingVerticalM),
    },
    body: {
        flexGrow: 1,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'auto',
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
    },
    form: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
});

interface Attachment {
    filename: string;
    content: string;
}

interface AssistantInspectorProps {
    assistantId: string;
    conversationId: string;
    stateDescription: ConversationStateDescription;
    state: ConversationState;
}

export const AssistantInspector: React.FC<AssistantInspectorProps> = (props) => {
    const { assistantId, conversationId, stateDescription, state } = props;
    const classes = useClasses();
    const [updateConversationState] = useUpdateConversationStateMutation();
    const [formData, setFormData] = React.useState<object>(state.data);
    const [isSubmitting, setIsSubmitting] = React.useState(false);

    React.useEffect(() => {
        setFormData(state.data);
    }, [state.data]);

    const handleChange = React.useCallback(
        async (updatedState: object) => {
            if (!state || isSubmitting) return;
            setIsSubmitting(true);
            setFormData(updatedState);
            await updateConversationState({ assistantId, conversationId, state: { ...state, data: updatedState } });
            setIsSubmitting(false);
        },
        [assistantId, conversationId, state, updateConversationState, isSubmitting],
    );

    const defaultRenderer = React.useCallback(() => {
        // check to see if data contains a key "content" that is a string, if so, render it
        // with the default content renderer, otherwise, render the data as a json object
        if ('content' in state.data) {
            const content = state.data['content'];
            if (typeof content === 'string') {
                return <ContentRenderer content={content} />;
            }
            if (Array.isArray(content)) {
                return <ContentListRenderer contentList={content} />;
            }
        }
        return <CodeContentRenderer content={JSON.stringify(state.data, null, 2)} language="json" />;
    }, [state]);

    const jsonSchemaRenderer = React.useCallback(() => {
        const widgets: RegistryWidgetsType = {
            inspectable: InspectableWidget,
        };

        const templates = {
            ArrayFieldTemplate: CustomizedArrayFieldTemplate,
            ObjectFieldTemplate: CustomizedObjectFieldTemplate,
        };
        return (
            <Form
                aria-autocomplete="none"
                autoComplete="off"
                className={classes.form}
                widgets={widgets}
                templates={templates}
                schema={state.jsonSchema ?? {}}
                uiSchema={{
                    ...state.uiSchema,
                    'ui:submitButtonOptions': {
                        submitText: 'Save',
                        ...state.uiSchema?.['ui:submitButtonOptions'],
                        props: {
                            disabled: JSON.stringify(formData) === JSON.stringify(state.data),
                            ...state.uiSchema?.['ui:submitButtonOptions']?.['props'],
                        },
                    },
                }}
                formData={formData}
                validator={validator}
                onChange={(data) => {
                    setFormData(data.formData);
                }}
                onSubmit={(data, event) => {
                    event.preventDefault();
                    handleChange(data.formData);
                }}
            />
        );
    }, [classes.form, formData, handleChange, state]);

    const markdownEditorRenderer = React.useCallback(() => {
        // Check if the data contains markdown_content, if not assume its empty.
        var markdownContent = 'markdown_content' in state.data ? String(state.data.markdown_content ?? '') : '';
        const filename = 'filename' in state.data ? String(state.data.filename) : undefined;
        // Check if the document is in read-only mode
        const isReadOnly = 'readonly' in state.data ? Boolean(state.data.readonly) : false;

        return (
            <MilkdownEditorWrapper
                content={markdownContent}
                filename={filename}
                readOnly={isReadOnly}
                onSubmit={async (updatedContent: string) => {
                    if (!state || isSubmitting || isReadOnly) return;
                    setIsSubmitting(true);
                    try {
                        // Convert back the unicode line separators to <br> tags
                        const updatedState = {
                            ...state.data,
                            markdown_content: updatedContent,
                        };
                        setFormData(updatedState);
                        await updateConversationState({
                            assistantId,
                            conversationId,
                            state: { ...state, data: updatedState },
                        });
                    } finally {
                        setIsSubmitting(false);
                    }
                }}
            />
        );
    }, [state, isSubmitting, updateConversationState, assistantId, conversationId]);

    let debugInspector = null;
    if (state && 'metadata' in state.data) {
        if ('debug' in (state.data.metadata as Record<string, unknown>)) {
            const debug = (state.data.metadata as Record<string, Record<string, unknown>>).debug;
            debugInspector = <DebugInspector debug={debug} />;
        }
    }

    const attachments = (state && 'attachments' in state.data ? state.data['attachments'] : []) as Attachment[];

    const handleDownloadAttachment = async (attachment: Attachment) => {
        // download helper function
        const download = (filename: string, href: string) => {
            const a = document.createElement('a');
            a.download = filename;
            a.href = href;
            a.click();
        };

        // if the content is a data URL, use it directly, otherwise create a blob URL
        if (attachment.content.startsWith('data:')) {
            download(attachment.filename, attachment.content);
        } else {
            const url = URL.createObjectURL(new Blob([attachment.content]));
            download(attachment.filename, url);
            URL.revokeObjectURL(url);
        }
    };

    const renderer = () => {
        if (!state) {
            return defaultRenderer();
        }
        if (state.jsonSchema) {
            return jsonSchemaRenderer();
        } else if (state.data && 'markdown_content' in state.data) {
            return markdownEditorRenderer();
        }
        return defaultRenderer();
    };
    return (
        <div className={classes.root}>
            <div className={classes.header}>
                <Text>{stateDescription.description}</Text>
                {debugInspector}
                {attachments.map((attachment) => (
                    <div key={attachment.filename}>
                        <Button
                            onClick={() => handleDownloadAttachment(attachment)}
                            icon={<ArrowDownloadRegular />}
                            appearance="subtle"
                        >
                            {attachment.filename}
                        </Button>
                    </div>
                ))}
            </div>
            <div className={classes.body}>{renderer()}</div>
        </div>
    );
};


=== File: workbench-app/src/components/Conversations/Canvas/AssistantInspectorList.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Overflow, OverflowItem, Tab, TabList, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import { EventSourceMessage } from '@microsoft/fetch-event-source';
import React from 'react';
import { useChatCanvasController } from '../../../libs/useChatCanvasController';
import { Assistant } from '../../../models/Assistant';
import { ConversationStateDescription } from '../../../models/ConversationStateDescription';
import { useAppSelector } from '../../../redux/app/hooks';
import { workbenchConversationEvents } from '../../../routes/FrontDoor';
import { useGetConversationStateQuery } from '../../../services/workbench';
import { Loading } from '../../App/Loading';
import { OverflowMenu, OverflowMenuItemData } from '../../App/OverflowMenu';
import { AssistantInspector } from './AssistantInspector';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
    },
    header: {
        flexShrink: 0,
        height: 'fit-content',
        overflow: 'hidden',
        ...shorthands.padding(tokens.spacingVerticalS),
        ...shorthands.borderBottom(tokens.strokeWidthThin, 'solid', tokens.colorNeutralStroke1),
    },
    body: {
        flexGrow: 1,
        overflowY: 'auto',
    },
});

interface AssistantInspectorListProps {
    conversationId: string;
    assistant: Assistant;
    stateDescriptions: ConversationStateDescription[];
}

export const AssistantInspectorList: React.FC<AssistantInspectorListProps> = (props) => {
    const { conversationId, assistant, stateDescriptions } = props;
    const classes = useClasses();
    const chatCanvasState = useAppSelector((state) => state.chatCanvas);
    const chatCanvasController = useChatCanvasController();

    const selectedStateDescription = React.useMemo(
        () =>
            stateDescriptions.find(
                (stateDescription) => stateDescription.id === chatCanvasState.selectedAssistantStateId,
            ) ?? stateDescriptions[0],
        [stateDescriptions, chatCanvasState.selectedAssistantStateId],
    );

    const {
        data: state,
        error: stateError,
        isLoading: isLoadingState,
        refetch: refetchState,
    } = useGetConversationStateQuery(
        { assistantId: assistant.id, stateId: selectedStateDescription.id, conversationId },
        { refetchOnMountOrArgChange: true },
    );

    if (stateError) {
        const errorMessage = JSON.stringify(stateError);
        throw new Error(`Error loading assistant state: ${errorMessage}`);
    }

    const handleEvent = React.useCallback(
        (event: EventSourceMessage) => {
            const { data } = JSON.parse(event.data);
            if (assistant.id !== data['assistant_id']) return;
            if (selectedStateDescription.id !== data['state_id']) return;
            if (conversationId !== data['conversation_id']) return;
            refetchState();
        },
        [assistant.id, selectedStateDescription.id, conversationId, refetchState],
    );

    React.useEffect(() => {
        workbenchConversationEvents.addEventListener('assistant.state.updated', handleEvent);

        return () => {
            workbenchConversationEvents.removeEventListener('assistant.state.updated', handleEvent);
        };
    }, [handleEvent]);

    const tabItems = React.useMemo(
        () =>
            stateDescriptions
                .filter((stateDescription) => stateDescription.id !== 'config')
                .map(
                    (stateDescription): OverflowMenuItemData => ({
                        id: stateDescription.id,
                        name: stateDescription.displayName,
                    }),
                ),
        [stateDescriptions],
    );

    const handleTabSelect = React.useCallback(
        (id: string) => {
            chatCanvasController.transitionToState({ selectedAssistantStateId: id });
        },
        [chatCanvasController],
    );

    const component = React.useMemo(() => {
        if (!state || isLoadingState) {
            return <Loading />;
        }
        if (stateDescriptions.length === 1) {
            // Only one assistant state, no need to show tabs, just show the single assistant state
            return (
                <AssistantInspector
                    assistantId={assistant.id}
                    conversationId={conversationId}
                    stateDescription={stateDescriptions[0]}
                    state={state}
                />
            );
        }

        if (stateDescriptions.length === 0) {
            return (
                <div className={classes.root}>
                    <div className={classes.header}>
                        <div>No assistant state inspectors available</div>
                    </div>
                </div>
            );
        }

        return (
            <div className={classes.root}>
                <div className={classes.header}>
                    <Overflow minimumVisible={1}>
                        <TabList
                            selectedValue={selectedStateDescription.id}
                            onTabSelect={(_, data) => handleTabSelect(data.value as string)}
                            size="small"
                        >
                            {tabItems.map((tabItem) => (
                                <OverflowItem
                                    key={tabItem.id}
                                    id={tabItem.id}
                                    priority={tabItem.id === selectedStateDescription.id ? 2 : 1}
                                >
                                    <Tab value={tabItem.id}>{tabItem.name}</Tab>
                                </OverflowItem>
                            ))}
                            <OverflowMenu items={tabItems} onItemSelect={handleTabSelect} />
                        </TabList>
                    </Overflow>
                </div>
                <div className={classes.body}>
                    <AssistantInspector
                        assistantId={assistant.id}
                        conversationId={conversationId}
                        stateDescription={selectedStateDescription}
                        state={state}
                    />
                </div>
            </div>
        );
    }, [
        state,
        isLoadingState,
        stateDescriptions,
        classes.root,
        classes.header,
        classes.body,
        selectedStateDescription,
        tabItems,
        handleTabSelect,
        assistant.id,
        conversationId,
    ]);
    return <>{component}</>;
};


=== File: workbench-app/src/components/Conversations/Canvas/ConversationCanvas.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Card, Text, makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { Conversation } from '../../../models/Conversation';
import { ConversationFile } from '../../../models/ConversationFile';
import { ConversationParticipant } from '../../../models/ConversationParticipant';
import { ContextWindow } from '../ContextWindow';
import { ConversationTranscript } from '../ConversationTranscript';
import { FileList } from '../FileList';
import { ParticipantList } from '../ParticipantList';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingHorizontalM,
        width: '100%',
    },
    card: {
        overflow: 'visible',
    },
});

interface ConversationCanvasProps {
    conversation: Conversation;
    conversationParticipants: ConversationParticipant[];
    conversationFiles: ConversationFile[];
    preventAssistantModifyOnParticipantIds?: string[];
    readOnly: boolean;
}

export const ConversationCanvas: React.FC<ConversationCanvasProps> = (props) => {
    const {
        conversationParticipants,
        conversationFiles,
        conversation,
        preventAssistantModifyOnParticipantIds,
        readOnly,
    } = props;
    const classes = useClasses();

    return (
        <div className={classes.root}>
            <Card className={classes.card}>
                <Text size={400} weight="semibold">
                    Participants
                </Text>
                <ParticipantList
                    conversation={conversation}
                    participants={conversationParticipants}
                    preventAssistantModifyOnParticipantIds={preventAssistantModifyOnParticipantIds}
                    readOnly={readOnly}
                />
            </Card>
            <Card className={classes.card}>
                <Text size={400} weight="semibold">
                    Transcript
                </Text>
                <ConversationTranscript conversation={conversation} participants={conversationParticipants} />
            </Card>
            <Card className={classes.card}>
                <Text size={400} weight="semibold">
                    Context window
                </Text>
                <ContextWindow conversation={conversation} />
            </Card>
            <Card className={classes.card}>
                <Text size={400} weight="semibold">
                    Files
                </Text>
                <FileList readOnly={readOnly} conversation={conversation} conversationFiles={conversationFiles} />
            </Card>
        </div>
    );
};


=== File: workbench-app/src/components/Conversations/ChatInputPlugins/ClearEditorPlugin.tsx ===
// Copyright (c) Microsoft. All rights reserved.
// based on code from: https://github.com/facebook/lexical/blob/main/packages/lexical-react/src/LexicalClearEditorPlugin.ts

import { useLexicalComposerContext } from '@fluentui-copilot/react-copilot';
import {
    $createParagraphNode,
    $getRoot,
    $getSelection,
    $isRangeSelection,
    CLEAR_EDITOR_COMMAND,
    COMMAND_PRIORITY_EDITOR,
} from 'lexical';
import React from 'react';

interface ClearEditorPluginProps {
    onClear?: () => void;
}

export const ClearEditorPlugin = ({ onClear }: ClearEditorPluginProps): JSX.Element | null => {
    const [editor] = useLexicalComposerContext();

    React.useLayoutEffect(() => {
        return editor.registerCommand(
            CLEAR_EDITOR_COMMAND,
            () => {
                editor.update(() => {
                    if (onClear == null) {
                        const root = $getRoot();
                        const selection = $getSelection();
                        const paragraph = $createParagraphNode();
                        root.clear();
                        root.append(paragraph);

                        if (selection !== null) {
                            paragraph.select();
                        }
                        if ($isRangeSelection(selection)) {
                            selection.format = 0;
                        }
                    } else {
                        onClear();
                    }
                });
                return true;
            },
            COMMAND_PRIORITY_EDITOR,
        );
    }, [editor, onClear]);

    return null;
};


=== File: workbench-app/src/components/Conversations/ChatInputPlugins/LexicalMenu.ts ===
// Copyright (c) Microsoft. All rights reserved.
// Based on code from: https://github.com/facebook/lexical/blob/main/packages/lexical-react/src/shared/LexicalMenu.ts

import { useLexicalComposerContext } from '@fluentui-copilot/react-copilot';
import { mergeRegister } from '@lexical/utils';
import {
    $getSelection,
    $isRangeSelection,
    COMMAND_PRIORITY_LOW,
    CommandListenerPriority,
    KEY_ARROW_DOWN_COMMAND,
    KEY_ARROW_UP_COMMAND,
    KEY_ENTER_COMMAND,
    KEY_ESCAPE_COMMAND,
    KEY_TAB_COMMAND,
    LexicalEditor,
    TextNode,
} from 'lexical';
import React from 'react';
import { SCROLL_TYPEAHEAD_OPTION_INTO_VIEW_COMMAND } from './TypeaheadMenuPlugin';

export type MenuTextMatch = {
    leadOffset: number;
    matchingString: string;
    replaceableString: string;
};

export type MenuResolution = {
    match?: MenuTextMatch;
    getRect: () => DOMRect;
};

export class MenuOption {
    key: string;
    ref?: React.MutableRefObject<HTMLElement | null>;

    constructor(key: string) {
        this.key = key;
        this.ref = { current: null };
        this.setRefElement = this.setRefElement.bind(this);
    }

    setRefElement(element: HTMLElement | null) {
        this.ref = { current: element };
    }
}

export type MenuRenderFn<TOption extends MenuOption> = (
    anchorElementRef: React.MutableRefObject<HTMLElement | null>,
    itemProps: {
        selectedIndex: number | null;
        selectOptionAndCleanUp: (option: TOption) => void;
        setHighlightedIndex: (index: number) => void;
        options: Array<TOption>;
    },
    matchingString: string | null,
) => React.ReactPortal | JSX.Element | null;

const scrollIntoViewIfNeeded = (target: HTMLElement) => {
    const typeaheadContainerNode = document.getElementById('typeahead-menu');
    if (!typeaheadContainerNode) {
        return;
    }

    const typeaheadRect = typeaheadContainerNode.getBoundingClientRect();

    if (typeaheadRect.top + typeaheadRect.height > window.innerHeight) {
        typeaheadContainerNode.scrollIntoView({
            block: 'center',
        });
    }

    if (typeaheadRect.top < 0) {
        typeaheadContainerNode.scrollIntoView({
            block: 'center',
        });
    }

    target.scrollIntoView({ block: 'nearest' });
};

/**
 * Walk backwards along user input and forward through entity title to try
 * and replace more of the user's text with entity.
 */
const getFullMatchOffset = (documentText: string, entryText: string, offset: number): number => {
    let triggerOffset = offset;
    for (let i = triggerOffset; i <= entryText.length; i++) {
        if (documentText.slice(-i) === entryText.slice(0, i)) {
            triggerOffset = i;
        }
    }
    return triggerOffset;
};

/**
 * Split Lexical TextNode and return a new TextNode only containing matched text.
 * Common use cases include: removing the node, replacing with a new node.
 */
const $splitNodeContainingQuery = (match: MenuTextMatch): TextNode | null => {
    const selection = $getSelection();
    if (!$isRangeSelection(selection) || !selection.isCollapsed()) {
        return null;
    }
    const anchor = selection.anchor;
    if (anchor.type !== 'text') {
        return null;
    }
    const anchorNode = anchor.getNode();
    if (!anchorNode.isSimpleText()) {
        return null;
    }
    const selectionOffset = anchor.offset;
    const textContent = anchorNode.getTextContent().slice(0, selectionOffset);
    const characterOffset = match.replaceableString.length;
    const queryOffset = getFullMatchOffset(textContent, match.matchingString, characterOffset);
    const startOffset = selectionOffset - queryOffset;
    if (startOffset < 0) {
        return null;
    }
    let newNode;
    if (startOffset === 0) {
        [newNode] = anchorNode.splitText(selectionOffset);
    } else {
        [, newNode] = anchorNode.splitText(startOffset, selectionOffset);
    }

    return newNode;
};

// Got from https://stackoverflow.com/a/42543908/2013580
export const getScrollParent = (element: HTMLElement, includeHidden: boolean): HTMLElement | HTMLBodyElement => {
    let style = getComputedStyle(element);
    const excludeStaticParent = style.position === 'absolute';
    const overflowRegex = includeHidden ? /(auto|scroll|hidden)/ : /(auto|scroll)/;
    if (style.position === 'fixed') {
        return document.body;
    }
    for (let parent: HTMLElement | null = element; (parent = parent.parentElement); ) {
        style = getComputedStyle(parent);
        if (excludeStaticParent && style.position === 'static') {
            continue;
        }
        if (overflowRegex.test(style.overflow + style.overflowY + style.overflowX)) {
            return parent;
        }
    }
    return document.body;
};

const isTriggerVisibleInNearestScrollContainer = (
    targetElement: HTMLElement,
    containerElement: HTMLElement,
): boolean => {
    const tRect = targetElement.getBoundingClientRect();
    const cRect = containerElement.getBoundingClientRect();
    return tRect.top > cRect.top && tRect.top < cRect.bottom;
};

// Reposition the menu on scroll, window resize, and element resize.
export const useDynamicPositioning = (
    resolution: MenuResolution | null,
    targetElement: HTMLElement | null,
    onReposition: () => void,
    onVisibilityChange?: (isInView: boolean) => void,
) => {
    const [editor] = useLexicalComposerContext();
    React.useEffect(() => {
        if (targetElement != null && resolution != null) {
            const rootElement = editor.getRootElement();
            const rootScrollParent = rootElement != null ? getScrollParent(rootElement, false) : document.body;
            let ticking = false;
            let previousIsInView = isTriggerVisibleInNearestScrollContainer(targetElement, rootScrollParent);
            const handleScroll = () => {
                if (!ticking) {
                    window.requestAnimationFrame(() => {
                        onReposition();
                        ticking = false;
                    });
                    ticking = true;
                }
                const isInView = isTriggerVisibleInNearestScrollContainer(targetElement, rootScrollParent);
                if (isInView !== previousIsInView) {
                    previousIsInView = isInView;
                    if (onVisibilityChange != null) {
                        onVisibilityChange(isInView);
                    }
                }
            };
            const resizeObserver = new ResizeObserver(onReposition);
            window.addEventListener('resize', onReposition);
            document.addEventListener('scroll', handleScroll, {
                capture: true,
                passive: true,
            });
            resizeObserver.observe(targetElement);
            return () => {
                resizeObserver.unobserve(targetElement);
                window.removeEventListener('resize', onReposition);
                document.removeEventListener('scroll', handleScroll, true);
            };
        }

        return;
    }, [targetElement, editor, onVisibilityChange, onReposition, resolution]);
};

export const LexicalMenu = <TOption extends MenuOption>({
    close,
    editor,
    anchorElementRef,
    resolution,
    options,
    menuRenderFn,
    onSelectOption,
    shouldSplitNodeWithQuery = false,
    commandPriority = COMMAND_PRIORITY_LOW,
}: {
    close: () => void;
    editor: LexicalEditor;
    anchorElementRef: React.MutableRefObject<HTMLElement>;
    resolution: MenuResolution;
    options: Array<TOption>;
    shouldSplitNodeWithQuery?: boolean;
    menuRenderFn: MenuRenderFn<TOption>;
    onSelectOption: (
        option: TOption,
        textNodeContainingQuery: TextNode | null,
        closeMenu: () => void,
        matchingString: string,
    ) => void;
    commandPriority?: CommandListenerPriority;
}): JSX.Element | null => {
    const [selectedIndex, setHighlightedIndex] = React.useState<null | number>(null);

    const matchingString = resolution.match && resolution.match.matchingString;

    React.useEffect(() => {
        setHighlightedIndex(0);
    }, [matchingString]);

    const selectOptionAndCleanUp = React.useCallback(
        (selectedEntry: TOption) => {
            editor.update(() => {
                const textNodeContainingQuery =
                    resolution.match != null && shouldSplitNodeWithQuery
                        ? $splitNodeContainingQuery(resolution.match)
                        : null;

                onSelectOption(
                    selectedEntry,
                    textNodeContainingQuery,
                    close,
                    resolution.match ? resolution.match.matchingString : '',
                );
            });
        },
        [editor, shouldSplitNodeWithQuery, resolution.match, onSelectOption, close],
    );

    const updateSelectedIndex = React.useCallback(
        (index: number) => {
            const rootElem = editor.getRootElement();
            if (rootElem !== null) {
                rootElem.setAttribute('aria-activedescendant', 'typeahead-item-' + index);
                setHighlightedIndex(index);
            }
        },
        [editor],
    );

    React.useEffect(() => {
        return () => {
            const rootElem = editor.getRootElement();
            if (rootElem !== null) {
                rootElem.removeAttribute('aria-activedescendant');
            }
        };
    }, [editor]);

    React.useLayoutEffect(() => {
        if (options === null) {
            setHighlightedIndex(null);
        } else if (selectedIndex === null) {
            updateSelectedIndex(0);
        }
    }, [options, selectedIndex, updateSelectedIndex]);

    React.useEffect(() => {
        return mergeRegister(
            editor.registerCommand(
                SCROLL_TYPEAHEAD_OPTION_INTO_VIEW_COMMAND,
                ({ option }) => {
                    if (option.ref && option.ref.current != null) {
                        scrollIntoViewIfNeeded(option.ref.current);
                        return true;
                    }

                    return false;
                },
                commandPriority,
            ),
        );
    }, [editor, updateSelectedIndex, commandPriority]);

    React.useEffect(() => {
        return mergeRegister(
            editor.registerCommand<KeyboardEvent>(
                KEY_ARROW_DOWN_COMMAND,
                (payload) => {
                    const event = payload;
                    if (options !== null && options.length && selectedIndex !== null) {
                        const newSelectedIndex = selectedIndex !== options.length - 1 ? selectedIndex + 1 : 0;
                        updateSelectedIndex(newSelectedIndex);
                        const option = options[newSelectedIndex];
                        if (option.ref != null && option.ref.current) {
                            editor.dispatchCommand(SCROLL_TYPEAHEAD_OPTION_INTO_VIEW_COMMAND, {
                                index: newSelectedIndex,
                                option,
                            });
                        }
                        event.preventDefault();
                        event.stopImmediatePropagation();
                    }
                    return true;
                },
                commandPriority,
            ),
            editor.registerCommand<KeyboardEvent>(
                KEY_ARROW_UP_COMMAND,
                (payload) => {
                    const event = payload;
                    if (options !== null && options.length && selectedIndex !== null) {
                        const newSelectedIndex = selectedIndex !== 0 ? selectedIndex - 1 : options.length - 1;
                        updateSelectedIndex(newSelectedIndex);
                        const option = options[newSelectedIndex];
                        if (option.ref != null && option.ref.current) {
                            scrollIntoViewIfNeeded(option.ref.current);
                        }
                        event.preventDefault();
                        event.stopImmediatePropagation();
                    }
                    return true;
                },
                commandPriority,
            ),
            editor.registerCommand<KeyboardEvent>(
                KEY_ESCAPE_COMMAND,
                (payload) => {
                    const event = payload;
                    event.preventDefault();
                    event.stopImmediatePropagation();
                    close();
                    return true;
                },
                commandPriority,
            ),
            editor.registerCommand<KeyboardEvent>(
                KEY_TAB_COMMAND,
                (payload) => {
                    const event = payload;
                    if (options === null || selectedIndex === null || options[selectedIndex] == null) {
                        return false;
                    }
                    event.preventDefault();
                    event.stopImmediatePropagation();
                    selectOptionAndCleanUp(options[selectedIndex]);
                    return true;
                },
                commandPriority,
            ),
            editor.registerCommand(
                KEY_ENTER_COMMAND,
                (event: KeyboardEvent | null) => {
                    if (options === null || selectedIndex === null || options[selectedIndex] == null) {
                        return false;
                    }
                    if (event !== null) {
                        event.preventDefault();
                        event.stopImmediatePropagation();
                    }
                    selectOptionAndCleanUp(options[selectedIndex]);
                    return true;
                },
                commandPriority,
            ),
        );
    }, [selectOptionAndCleanUp, close, editor, options, selectedIndex, updateSelectedIndex, commandPriority]);

    const listItemProps = React.useMemo(
        () => ({
            options,
            selectOptionAndCleanUp,
            selectedIndex,
            setHighlightedIndex,
        }),
        [selectOptionAndCleanUp, selectedIndex, options],
    );

    return menuRenderFn(anchorElementRef, listItemProps, resolution.match ? resolution.match.matchingString : '');
};

export const useMenuAnchorRef = (
    resolution: MenuResolution | null,
    setResolution: (r: MenuResolution | null) => void,
    className?: string,
    parent: HTMLElement = document.body,
): React.MutableRefObject<HTMLElement> => {
    const [editor] = useLexicalComposerContext();
    const anchorElementRef = React.useRef<HTMLElement>(document.createElement('div'));
    const positionMenu = React.useCallback(() => {
        anchorElementRef.current.style.top = anchorElementRef.current.style.bottom;
        const rootElement = editor.getRootElement();
        const containerDiv = anchorElementRef.current;

        const menuEle = containerDiv.firstChild as HTMLElement;
        if (rootElement !== null && resolution !== null) {
            const { left, top, width, height } = resolution.getRect();
            containerDiv.style.bottom = `${top + window.scrollY}px`;
            containerDiv.style.left = `${left + window.scrollX}px`;
            containerDiv.style.height = `${height}px`;
            containerDiv.style.width = `${width}px`;
            if (menuEle !== null) {
                menuEle.style.top = `${top}`;
                const menuRect = menuEle.getBoundingClientRect();
                const menuHeight = menuRect.height;
                const menuWidth = menuRect.width;

                const rootElementRect = rootElement.getBoundingClientRect();

                if (left + menuWidth > rootElementRect.right) {
                    containerDiv.style.left = `${rootElementRect.right - menuWidth + window.scrollX}px`;
                }
                if (
                    (top + menuHeight > window.innerHeight || top + menuHeight > rootElementRect.bottom) &&
                    top - rootElementRect.top > menuHeight + height
                ) {
                    containerDiv.style.top = `${top - menuHeight + window.scrollY - height}px`;
                }
            }

            if (!containerDiv.isConnected) {
                if (className != null) {
                    containerDiv.className = className;
                }
                containerDiv.setAttribute('aria-label', 'Typeahead menu');
                containerDiv.setAttribute('id', 'typeahead-menu');
                containerDiv.setAttribute('role', 'listbox');
                containerDiv.style.display = 'block';
                containerDiv.style.position = 'absolute';
                parent.append(containerDiv);
            }
            anchorElementRef.current = containerDiv;
            rootElement.setAttribute('aria-controls', 'typeahead-menu');
        }
    }, [editor, resolution, className, parent]);

    React.useEffect(() => {
        const rootElement = editor.getRootElement();
        if (resolution !== null) {
            positionMenu();
            return () => {
                if (rootElement !== null) {
                    rootElement.removeAttribute('aria-controls');
                }

                const containerDiv = anchorElementRef.current;
                if (containerDiv !== null && containerDiv.isConnected) {
                    containerDiv.remove();
                }
            };
        }

        return;
    }, [editor, positionMenu, resolution]);

    const onVisibilityChange = React.useCallback(
        (isInView: boolean) => {
            if (resolution !== null) {
                if (!isInView) {
                    setResolution(null);
                }
            }
        },
        [resolution, setResolution],
    );

    useDynamicPositioning(resolution, anchorElementRef.current, positionMenu, onVisibilityChange);

    return anchorElementRef;
};

export type TriggerFn = (text: string, editor: LexicalEditor) => MenuTextMatch | null;


=== File: workbench-app/src/components/Conversations/ChatInputPlugins/ParticipantMentionsPlugin.tsx ===
// Copyright (c) Microsoft. All rights reserved.
// Based on code from: https://github.com/facebook/lexical/blob/main/packages/lexical-playground/src/plugins/MentionsPlugin/index.tsx

import { $createChatInputEntityNode, TextNode, useLexicalComposerContext } from '@fluentui-copilot/react-copilot';
import { Label } from '@fluentui/react-components';
import React from 'react';
import { createPortal } from 'react-dom';
import { ConversationParticipant } from '../../../models/ConversationParticipant';
import { MenuOption, MenuTextMatch } from './LexicalMenu';
import { TypeaheadMenuPlugin, useBasicTypeaheadTriggerMatch } from './TypeaheadMenuPlugin';

const punctuationCharacters = '\\.,\\+\\*\\?\\$\\@\\|#{}\\(\\)\\^\\-\\[\\]\\\\/!%\'"~=<>_:;';
const triggerCharacters = ['@'].join('');

// Chars we expect to see in a mention (non-space, non-punctuation).
const validCharacters = '[^' + triggerCharacters + punctuationCharacters + '\\s]';

// Non-standard series of chars. Each series must be preceded and followed by
// a valid char.
const validJoins =
    '(?:' +
    '\\.[ |$]|' + // E.g. "r. " in "Mr. Smith"
    ' |' + // E.g. " " in "Josh Duck"
    '[' +
    punctuationCharacters +
    ']|' + // E.g. "-' in "Smith-Jones"
    ')';

const lengthLimit = 75;

const atSignMentionsRegex = new RegExp(
    '(^|\\s|\\()([' + triggerCharacters + ']((?:' + validCharacters + validJoins + '){0,' + lengthLimit + '}))$',
);

// 50 is the longest alias length limit.
const aliasLengthLimit = 50;

// Regex used to match alias.
const atSignMentionsRegexAliasRegex = new RegExp(
    '(^|\\s|\\()([' + triggerCharacters + ']((?:' + validCharacters + '){0,' + aliasLengthLimit + '}))$',
);

// At most, 5 suggestions are shown in the popup.
const suggestionListLengthLimit = 5;

interface ParticipantMentionsPluginProps {
    participants: ConversationParticipant[];
    parent?: HTMLElement | null;
}

class MentionTypeaheadOption extends MenuOption {
    participant: ConversationParticipant;

    constructor(participant: ConversationParticipant) {
        super(participant.id);
        this.participant = participant;
    }
}

const MentionsTypeaheadMenuItem = ({
    index,
    isSelected,
    onClick,
    onMouseEnter,
    option,
}: {
    index: number;
    isSelected: boolean;
    onClick: () => void;
    onMouseEnter: () => void;
    option: MentionTypeaheadOption;
}) => {
    let className = 'item';
    if (isSelected) {
        className += ' selected';
    }
    return (
        <li
            key={option.key}
            tabIndex={-1}
            className={className}
            ref={option.setRefElement}
            role="option"
            aria-selected={isSelected}
            id={'typeahead-item-' + index}
            onMouseEnter={onMouseEnter}
            onClick={onClick}
        >
            <Label>{option.participant.name}</Label>
        </li>
    );
};

const checkForAtSignMentions = (text: string, minMatchLength: number): MenuTextMatch | null => {
    let match = atSignMentionsRegex.exec(text);

    if (match === null) {
        match = atSignMentionsRegexAliasRegex.exec(text);
    }
    if (match !== null) {
        // The strategy ignores leading whitespace but we need to know it's
        // length to add it to the leadOffset
        const maybeLeadingWhitespace = match[1];

        const matchingString = match[3];
        if (matchingString.length >= minMatchLength) {
            return {
                leadOffset: match.index + maybeLeadingWhitespace.length,
                matchingString,
                replaceableString: match[2],
            };
        }
    }
    return null;
};

const getPossibleQueryMatch = (text: string): MenuTextMatch | null => {
    return checkForAtSignMentions(text, 1);
};

export const ParticipantMentionsPlugin: React.FC<ParticipantMentionsPluginProps> = (props) => {
    const { participants, parent } = props;
    const [editor] = useLexicalComposerContext();
    const [queryString, setQueryString] = React.useState<string | null>(null);
    const [results, setResults] = React.useState<ConversationParticipant[]>([]);

    React.useEffect(() => {
        if (queryString === null) {
            setResults([]);
            return;
        }

        const query = queryString.toLowerCase();
        const results = participants.filter((participant) => participant.name.toLowerCase().includes(query));
        setResults(results);
    }, [queryString, participants]);

    const options = React.useMemo(
        () => results.map((result) => new MentionTypeaheadOption(result)).slice(0, suggestionListLengthLimit),
        [results],
    );

    const checkForSlashTriggerMatch = useBasicTypeaheadTriggerMatch('/', {
        minLength: 0,
    });

    const checkForMentionMatch = React.useCallback(
        (text: string) => {
            const slashMatch = checkForSlashTriggerMatch(text, editor);
            if (slashMatch !== null) {
                return null;
            }
            return getPossibleQueryMatch(text);
        },
        [checkForSlashTriggerMatch, editor],
    );

    const onSelectOption = React.useCallback(
        (selectedOption: MentionTypeaheadOption, nodeToReplace: TextNode | null, closeMenu: () => void) => {
            editor.update(() => {
                const data = {
                    type: 'mention',
                    participant: selectedOption.participant,
                };
                const mentionNode = $createChatInputEntityNode(
                    selectedOption.key,
                    `@${selectedOption.participant.name}`,
                    data,
                );
                if (nodeToReplace) {
                    nodeToReplace.replace(mentionNode);
                }
                closeMenu();
            });
        },
        [editor],
    );

    return (
        <TypeaheadMenuPlugin<MentionTypeaheadOption>
            onQueryChange={setQueryString}
            onSelectOption={onSelectOption}
            triggerFn={checkForMentionMatch}
            options={options}
            parent={parent ?? undefined}
            menuRenderFn={(anchorElementRef, { selectedIndex, selectOptionAndCleanUp, setHighlightedIndex }) =>
                anchorElementRef.current && results.length
                    ? createPortal(
                          <div className="typeahead-popover mentions-menu">
                              <ul>
                                  {options.map((option, i: number) => (
                                      <MentionsTypeaheadMenuItem
                                          index={i}
                                          isSelected={selectedIndex === i}
                                          onClick={() => {
                                              setHighlightedIndex(i);
                                              selectOptionAndCleanUp(option);
                                          }}
                                          onMouseEnter={() => {
                                              setHighlightedIndex(i);
                                          }}
                                          key={option.key}
                                          option={option}
                                      />
                                  ))}
                              </ul>
                          </div>,
                          anchorElementRef.current,
                      )
                    : null
            }
        />
    );
};


=== File: workbench-app/src/components/Conversations/ChatInputPlugins/TypeaheadMenuPlugin.css ===
.typeahead-popover.mentions-menu {
    position: absolute;
    z-index: 1000;
    bottom: 20px;
    background-color: white;
    border: 1px solid #ccc;
}

.typeahead-popover.mentions-menu ul {
    list-style-type: none;
    margin: 0;
    padding: 0;
    max-height: 200px;
    overflow-y: auto;
    width: 100%;
}

.typeahead-popover.mentions-menu li {
    padding: 5px 10px;
    cursor: pointer;
}

.typeahead-popover.mentions-menu li.selected {
    background-color: #ccc;
}

.typeahead-popover.mentions-menu li label {
    white-space: nowrap;
}


=== File: workbench-app/src/components/Conversations/ChatInputPlugins/TypeaheadMenuPlugin.tsx ===
// Copyright (c) Microsoft. All rights reserved.
// Based on code from: https://github.com/facebook/lexical/blob/main/packages/lexical-react/src/LexicalTypeaheadMenuPlugin.tsx

import type { MenuRenderFn, MenuResolution, MenuTextMatch, TriggerFn } from './LexicalMenu';

import { useLexicalComposerContext } from '@fluentui-copilot/react-copilot';
import {
    $getSelection,
    $isRangeSelection,
    $isTextNode,
    COMMAND_PRIORITY_LOW,
    CommandListenerPriority,
    createCommand,
    LexicalCommand,
    LexicalEditor,
    RangeSelection,
    TextNode,
} from 'lexical';
import * as React from 'react';
import { useCallback, useEffect, useState } from 'react';
import './TypeaheadMenuPlugin.css';

import { LexicalMenu, MenuOption, useMenuAnchorRef } from './LexicalMenu';

export const PUNCTUATION = '\\.,\\+\\*\\?\\$\\@\\|#{}\\(\\)\\^\\-\\[\\]\\\\/!%\'"~=<>_:;';

const getTextUpToAnchor = (selection: RangeSelection): string | null => {
    const anchor = selection.anchor;
    if (anchor.type !== 'text') {
        return null;
    }
    const anchorNode = anchor.getNode();
    if (!anchorNode.isSimpleText()) {
        return null;
    }
    const anchorOffset = anchor.offset;
    return anchorNode.getTextContent().slice(0, anchorOffset);
};

const tryToPositionRange = (leadOffset: number, range: Range, editorWindow: Window): boolean => {
    const domSelection = editorWindow.getSelection();
    if (domSelection === null || !domSelection.isCollapsed) {
        return false;
    }
    const anchorNode = domSelection.anchorNode;
    const startOffset = leadOffset;
    const endOffset = domSelection.anchorOffset;

    if (anchorNode == null || endOffset == null) {
        return false;
    }

    try {
        range.setStart(anchorNode, startOffset);
        range.setEnd(anchorNode, endOffset);
    } catch (error) {
        return false;
    }

    return true;
};

const getQueryTextForSearch = (editor: LexicalEditor): string | null => {
    let text = null;
    editor.getEditorState().read(() => {
        const selection = $getSelection();
        if (!$isRangeSelection(selection)) {
            return;
        }
        text = getTextUpToAnchor(selection);
    });
    return text;
};

const isSelectionOnEntityBoundary = (editor: LexicalEditor, offset: number): boolean => {
    if (offset !== 0) {
        return false;
    }
    return editor.getEditorState().read(() => {
        const selection = $getSelection();
        if ($isRangeSelection(selection)) {
            const anchor = selection.anchor;
            const anchorNode = anchor.getNode();
            const prevSibling = anchorNode.getPreviousSibling();
            return $isTextNode(prevSibling) && prevSibling.isTextEntity();
        }
        return false;
    });
};

const startTransition = (callback: () => void) => {
    if (React.startTransition) {
        React.startTransition(callback);
    } else {
        callback();
    }
};

export const SCROLL_TYPEAHEAD_OPTION_INTO_VIEW_COMMAND: LexicalCommand<{
    index: number;
    option: MenuOption;
}> = createCommand('SCROLL_TYPEAHEAD_OPTION_INTO_VIEW_COMMAND');

export const useBasicTypeaheadTriggerMatch = (
    trigger: string,
    { minLength = 1, maxLength = 75 }: { minLength?: number; maxLength?: number },
): TriggerFn => {
    return useCallback(
        (text: string) => {
            const validChars = '[^' + trigger + PUNCTUATION + '\\s]';
            const TypeaheadTriggerRegex = new RegExp(
                '(^|\\s|\\()([' + trigger + ']((?:' + validChars + '){0,' + maxLength + '}))$',
            );
            const match = TypeaheadTriggerRegex.exec(text);
            if (match !== null) {
                const maybeLeadingWhitespace = match[1];
                const matchingString = match[3];
                if (matchingString.length >= minLength) {
                    return {
                        leadOffset: match.index + maybeLeadingWhitespace.length,
                        matchingString,
                        replaceableString: match[2],
                    };
                }
            }
            return null;
        },
        [maxLength, minLength, trigger],
    );
};

export type TypeaheadMenuPluginProps<TOption extends MenuOption> = {
    onQueryChange: (matchingString: string | null) => void;
    onSelectOption: (
        option: TOption,
        textNodeContainingQuery: TextNode | null,
        closeMenu: () => void,
        matchingString: string,
    ) => void;
    options: Array<TOption>;
    menuRenderFn: MenuRenderFn<TOption>;
    triggerFn: TriggerFn;
    onOpen?: (resolution: MenuResolution) => void;
    onClose?: () => void;
    anchorClassName?: string;
    commandPriority?: CommandListenerPriority;
    parent?: HTMLElement;
};

export const TypeaheadMenuPlugin = <TOption extends MenuOption>({
    options,
    onQueryChange,
    onSelectOption,
    onOpen,
    onClose,
    menuRenderFn,
    triggerFn,
    anchorClassName,
    commandPriority = COMMAND_PRIORITY_LOW,
    parent,
}: TypeaheadMenuPluginProps<TOption>): JSX.Element | null => {
    const [editor] = useLexicalComposerContext();
    const [resolution, setResolution] = useState<MenuResolution | null>(null);
    const anchorElementRef = useMenuAnchorRef(resolution, setResolution, anchorClassName, parent);

    const closeTypeahead = useCallback(() => {
        setResolution(null);
        if (onClose != null && resolution !== null) {
            onClose();
        }
    }, [onClose, resolution]);

    const openTypeahead = useCallback(
        (res: MenuResolution) => {
            setResolution(res);
            if (onOpen != null && resolution === null) {
                onOpen(res);
            }
        },
        [onOpen, resolution],
    );

    useEffect(() => {
        const updateListener = () => {
            editor.getEditorState().read(() => {
                const editorWindow = editor._window || window;
                const range = editorWindow.document.createRange();
                const selection = $getSelection();
                const text = getQueryTextForSearch(editor);

                if (!$isRangeSelection(selection) || !selection.isCollapsed() || text === null || range === null) {
                    closeTypeahead();
                    return;
                }

                const match = triggerFn(text, editor);
                onQueryChange(match ? match.matchingString : null);

                if (match !== null && !isSelectionOnEntityBoundary(editor, match.leadOffset)) {
                    const isRangePositioned = tryToPositionRange(match.leadOffset, range, editorWindow);
                    if (isRangePositioned !== null) {
                        startTransition(() =>
                            openTypeahead({
                                getRect: () => range.getBoundingClientRect(),
                                match,
                            }),
                        );
                        return;
                    }
                }
                closeTypeahead();
            });
        };

        const removeUpdateListener = editor.registerUpdateListener(updateListener);

        return () => {
            removeUpdateListener();
        };
    }, [editor, triggerFn, onQueryChange, resolution, closeTypeahead, openTypeahead]);

    return resolution === null || editor === null ? null : (
        <LexicalMenu
            close={closeTypeahead}
            resolution={resolution}
            editor={editor}
            anchorElementRef={anchorElementRef}
            options={options}
            menuRenderFn={menuRenderFn}
            shouldSplitNodeWithQuery={true}
            onSelectOption={onSelectOption}
            commandPriority={commandPriority}
        />
    );
};

export { MenuOption, MenuRenderFn, MenuResolution, MenuTextMatch, TriggerFn };


=== File: workbench-app/src/components/Conversations/ContentRenderers/CodeContentRenderer.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { stackoverflowLight as syntaxHighlighterStyle } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import { CopyButton } from '../../App/CopyButton';

const useClasses = makeStyles({
    root: {
        position: 'relative',
    },
    copy: {
        position: 'absolute',
        right: tokens.spacingHorizontalXS,
        top: tokens.spacingVerticalXS,
    },
});

interface CodeContentRendererProps {
    content: string;
    language: string;
}

export const CodeContentRenderer: React.FC<CodeContentRendererProps> = (props) => {
    const { content, language } = props;
    const classes = useClasses();

    return (
        <div className={classes.root}>
            <div className={classes.copy}>
                <CopyButton data={content}></CopyButton>
            </div>
            <SyntaxHighlighter
                PreTag="div"
                language={language}
                style={syntaxHighlighterStyle}
                wrapLongLines
                // eslint-disable-next-line react/no-children-prop
                children={content}
            />
        </div>
    );
};


=== File: workbench-app/src/components/Conversations/ContentRenderers/ContentListRenderer.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { ContentRenderer } from './ContentRenderer';

interface ContentListRendererProps {
    contentList: string[];
}

export const ContentListRenderer: React.FC<ContentListRendererProps> = (props) => {
    const { contentList } = props;
    return (
        <div>
            {contentList.map((content, index) => (
                <ContentRenderer key={index} content={content} />
            ))}
        </div>
    );
};


=== File: workbench-app/src/components/Conversations/ContentRenderers/ContentRenderer.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { CodeContentRenderer } from './CodeContentRenderer';
import { HtmlContentRenderer } from './HtmlContentRenderer';
import { JsonSchemaContentRenderer } from './JsonSchemaContentRenderer';
import { MarkdownContentRenderer } from './MarkdownContentRenderer';

interface ContentRenderProps {
    content: string;
    contentType?: string;
    metadata?: Record<string, unknown>;
    onSubmit?: (data: string) => Promise<void>;
}

export const ContentRenderer: React.FC<ContentRenderProps> = (props) => {
    const { content, contentType, metadata, onSubmit } = props;

    if (contentType === 'application/json') {
        if (metadata?.json_schema) {
            return <JsonSchemaContentRenderer content={content} metadata={metadata} onSubmit={onSubmit} />;
        }
        return <CodeContentRenderer content={content} language="json" />;
    }

    if (content.includes('```html')) {
        return <HtmlContentRenderer content={content} displayNonHtmlContent />;
    }

    // Default to markdown
    return <MarkdownContentRenderer content={content} />;
};


=== File: workbench-app/src/components/Conversations/ContentRenderers/DiffRenderer.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, tokens } from '@fluentui/react-components';
import { DiffFile, generateDiffFile } from '@git-diff-view/file';
import { DiffModeEnum, DiffView } from '@git-diff-view/react';
import '@git-diff-view/react/styles/diff-view.css';
import React from 'react';

const useClasses = makeStyles({
    root: {
        position: 'relative',
    },
    copy: {
        position: 'absolute',
        right: tokens.spacingHorizontalXS,
        top: tokens.spacingVerticalXS,
    },
});

export interface DiffItem {
    content: string;
    label?: string;
    language?: string;
}

interface DiffRendererProps {
    source: DiffItem;
    compare: DiffItem;
    splitView?: boolean;
    wrapLines?: boolean;
}

export const DiffRenderer: React.FC<DiffRendererProps> = (props) => {
    const { source, compare, splitView, wrapLines } = props;
    const classes = useClasses();

    const diffFile = React.useMemo(() => {
        if (source.content === compare.content) {
            return undefined;
        }

        const file = generateDiffFile(
            source.label || 'Source',
            source.content,
            compare.label || 'Compare',
            compare.content,
        );

        file.init();
        if (splitView) {
            file.buildSplitDiffLines();
        } else {
            file.buildUnifiedDiffLines();
        }

        const bundle = file.getBundle();
        const mergeFile = DiffFile.createInstance(
            {
                oldFile: {
                    fileName: source.label,
                    content: source.content,
                    fileLang: source.language,
                },
                newFile: {
                    fileName: compare.label,
                    content: compare.content,
                    fileLang: compare.language,
                },
            },
            bundle,
        );

        return mergeFile;
    }, [source.label, source.content, source.language, compare.label, compare.content, compare.language, splitView]);

    return (
        <div className={classes.root}>
            <DiffView
                diffFile={diffFile}
                diffViewMode={splitView ? DiffModeEnum.Split : DiffModeEnum.Unified}
                diffViewWrap={wrapLines}
            />
        </div>
    );
};


=== File: workbench-app/src/components/Conversations/ContentRenderers/HtmlContentRenderer.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, shorthands, Text, tokens } from '@fluentui/react-components';
import React from 'react';
import DynamicIframe from '../../App/DynamicIframe';
import { CodeContentRenderer } from './CodeContentRenderer';
import { MarkdownContentRenderer } from './MarkdownContentRenderer';

const useClasses = makeStyles({
    previewTitle: {
        ...shorthands.margin(tokens.spacingVerticalM, 0, 0, 0),
    },
    previewBox: {
        border: `1px solid ${tokens.colorNeutralStroke1}`,
    },
});

interface HtmlContentRendererProps {
    content: string;
    displayNonHtmlContent?: boolean;
}

export const HtmlContentRenderer: React.FC<HtmlContentRendererProps> = (props) => {
    const { content, displayNonHtmlContent } = props;
    const classes = useClasses();

    // replace all html content with the dynamic iframe
    const parts = content.split(/(```html\n[\s\S]*?\n```)/g);

    return (
        <>
            {parts.map((part, index) => {
                const htmlMatch = part.match(/```html\n([\s\S]*?)\n```/);
                if (htmlMatch) {
                    return (
                        <>
                            {displayNonHtmlContent ? (
                                <>
                                    <CodeContentRenderer key={index} content={htmlMatch[1]} language="html" />
                                    <Text className={classes.previewTitle} weight="semibold">
                                        Preview:
                                    </Text>
                                </>
                            ) : null}
                            <div className={displayNonHtmlContent ? classes.previewBox : ''}>
                                <DynamicIframe key={index} source={htmlMatch[1]} />
                            </div>
                        </>
                    );
                } else {
                    return displayNonHtmlContent ? <MarkdownContentRenderer key={index} content={part} /> : null;
                }
            })}
        </>
    );
};


=== File: workbench-app/src/components/Conversations/ContentRenderers/JsonSchemaContentRenderer.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, shorthands, tokens } from '@fluentui/react-components';
import {} from '@rjsf/core';
import Form from '@rjsf/fluentui-rc';
import { RegistryWidgetsType } from '@rjsf/utils';
import validator from '@rjsf/validator-ajv8';
import React from 'react';
import { CustomizedArrayFieldTemplate } from '../../App/FormWidgets/CustomizedArrayFieldTemplate';
import { CustomizedObjectFieldTemplate } from '../../App/FormWidgets/CustomizedObjectFieldTemplate';
import { InspectableWidget } from '../../App/FormWidgets/InspectableWidget';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        ...shorthands.padding(tokens.spacingVerticalM),
        gap: tokens.spacingVerticalL,
    },
    form: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
});

interface InspectorProps {
    content: string;
    metadata: Record<string, unknown>;
    onSubmit?: (data: string) => Promise<void>;
}

export const JsonSchemaContentRenderer: React.FC<InspectorProps> = (props) => {
    const { content, metadata, onSubmit } = props;
    const classes = useClasses();

    const currentData = JSON.parse(content);
    const jsonSchema: object = metadata.json_schema || {};
    const uiSchema: object = metadata.ui_schema || {};

    const [formData, setFormData] = React.useState<object>(currentData);
    const [isSubmitting, setIsSubmitting] = React.useState(false);

    const handleSubmit = React.useCallback(
        async (updatedData: object) => {
            if (isSubmitting) return;
            setIsSubmitting(true);
            setFormData(updatedData);
            await onSubmit?.(JSON.stringify(updatedData));
            setIsSubmitting(false);
        },
        [isSubmitting, onSubmit],
    );

    const widgets: RegistryWidgetsType = {
        inspectable: InspectableWidget,
    };

    const templates = {
        ArrayFieldTemplate: CustomizedArrayFieldTemplate,
        ObjectFieldTemplate: CustomizedObjectFieldTemplate,
    };

    return (
        <>
            <Form
                aria-autocomplete="none"
                autoComplete="off"
                disabled={isSubmitting}
                className={classes.form}
                widgets={widgets}
                templates={templates}
                schema={jsonSchema}
                uiSchema={uiSchema}
                formData={formData}
                validator={validator}
                onChange={(data) => {
                    setFormData(data.formData);
                }}
                onSubmit={(data, event) => {
                    event.preventDefault();
                    handleSubmit(data.formData);
                }}
            />
        </>
    );
};


=== File: workbench-app/src/components/Conversations/ContentRenderers/MarkdownContentRenderer.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { makeStyles } from '@fluentui/react-components';
import React from 'react';
import Markdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize from 'rehype-sanitize';
import remarkGfm from 'remark-gfm';
import { CodeContentRenderer } from './CodeContentRenderer';
import { MermaidContentRenderer } from './MermaidContentRenderer';
import { MusicABCContentRenderer } from './MusicABCContentRenderer';

const useClasses = makeStyles({
    root: {
        // when this is first child of another griffel component
        '& :first-child': {
            marginTop: 0,
        },
        // when this is last child of another griffel component
        '& :last-child': {
            marginBottom: 0,
        },
    },
});

interface MarkdownContentRendererProps {
    content: string;
}

export const MarkdownContentRenderer: React.FC<MarkdownContentRendererProps> = (props) => {
    const { content } = props;
    const classes = useClasses();

    let cleanedContent = content;
    // strip ```markdown & ``` from the beginning and end of the content if exists
    if (content.startsWith('```markdown') && content.endsWith('```')) {
        cleanedContent = content.substring(11, content.length - 3);
    }

    return (
        <Markdown
            className={classes.root}
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeRaw, rehypeSanitize]}
            components={{
                code(props) {
                    // TODO: determine if we should fix these eslint-disable lines
                    // eslint-disable-next-line react/prop-types
                    const { children, className, node, ...rest } = props;
                    const match = /language-(\w+)/i.exec(className || '');

                    if (match) {
                        const language = match[1];
                        const content = String(children).replace(/\n$/, '');

                        if (language === 'mermaid') {
                            return <MermaidContentRenderer content={content} clickToZoom />;
                        }

                        if (language === 'abc') {
                            return <MusicABCContentRenderer content={content} />;
                        }

                        return <CodeContentRenderer content={content} language={language} />;
                    }

                    // no language specified, just render the code
                    return (
                        // eslint-disable-next-line react/jsx-props-no-spreading
                        <code {...rest} className={className}>
                            {children}
                        </code>
                    );
                },
            }}
        >
            {cleanedContent}
        </Markdown>
    );
};


=== File: workbench-app/src/components/Conversations/ContentRenderers/MarkdownEditorRenderer.tsx ===
import { Button, makeStyles, Text } from '@fluentui/react-components';
import { LockClosedRegular, LockOpenRegular, SaveRegular } from '@fluentui/react-icons';
import { Crepe } from '@milkdown/crepe';
import '@milkdown/crepe/theme/common/style.css';
import '@milkdown/crepe/theme/frame.css';
import { Milkdown, MilkdownProvider, useEditor } from '@milkdown/react';
import React from 'react';

const useStyles = makeStyles({
    editorContainer: {
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        height: '100%',
        flex: 1,
    },
    milkdownWrapper: {
        height: '100%',
        width: '100%',
        flex: 1,
        display: 'flex',
        '& .milkdown': {
            height: '100%',
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            flex: 1,
            overflow: 'auto',
        },
        '& .ProseMirror': {
            margin: '10px 0 0 0',
            padding: '14px 20px 20px 70px',
        },
        '& [data-milkdown-root="true"]': {
            height: '100%',
            width: '100%',
        },
    },
    toolbar: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingLeft: '70px',
    },
    filenameContainer: {
        display: 'flex',
        alignItems: 'baseline',
        gap: '12px',
    },
    filename: {
        margin: '0',
        fontSize: '42px',
        fontWeight: 'bold',
        lineHeight: '1',
        fontFamily: 'Noto Sans',
    },
    readOnlyIndicator: {
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
        color: 'var(--colorNeutralForeground3)',
        fontStyle: 'italic',
    },
    buttonGroup: {
        display: 'flex',
        gap: '4px',
    },
    saveButton: {
        backgroundColor: 'var(--colorStatusDangerBackground2)',
        color: 'var(--colorStatusDangerForeground2)',
    },
});

interface MilkdownEditorProps {
    content?: string;
    onSave?: (content: string) => void;
    filename?: string;
    readOnly?: boolean;
    onToggleReadOnly?: () => void;
    isBackendReadOnly?: boolean;
}

const MilkdownEditor: React.FC<MilkdownEditorProps> = ({
    content = '',
    onSave,
    filename,
    readOnly = false,
    onToggleReadOnly,
    isBackendReadOnly = false,
}) => {
    const styles = useStyles();
    const [editorInstance, setEditorInstance] = React.useState<Crepe | null>(null);
    const [hasUnsavedChanges, setHasUnsavedChanges] = React.useState(false);
    const initialContentRef = React.useRef(content);

    useEditor(
        (root) => {
            const crepe = new Crepe({
                root,
                defaultValue: content,
                featureConfigs: {
                    [Crepe.Feature.Placeholder]: {
                        text: 'Just start typing...',
                        mode: 'block',
                    },
                },
            });

            crepe.create().then(() => {
                crepe.setReadonly(readOnly);
                setEditorInstance(crepe);

                // Set up content change detection
                crepe.on((listener) => {
                    listener.markdownUpdated(() => {
                        const currentContent = crepe.getMarkdown();
                        setHasUnsavedChanges(currentContent !== initialContentRef.current);
                    });
                });
            });

            return crepe;
        },
        [content],
    );

    // Reset unsaved changes flag when content prop changes (after saving)
    React.useEffect(() => {
        initialContentRef.current = content;
        setHasUnsavedChanges(false);
    }, [content]);

    // Update readonly state when it changes
    React.useEffect(() => {
        if (editorInstance) {
            editorInstance.setReadonly(readOnly);
        }
    }, [readOnly, editorInstance]);

    const handleSave = React.useCallback(() => {
        if (!onSave || !editorInstance || !hasUnsavedChanges) return;
        const currentContent = editorInstance.getMarkdown();
        onSave(currentContent);
        // Note: We don't reset hasUnsavedChanges here because the parent component
        // should update the content prop which will trigger the useEffect above
    }, [onSave, editorInstance, hasUnsavedChanges]);

    // Add keyboard shortcut for Ctrl+S
    React.useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                if (!readOnly && hasUnsavedChanges) {
                    handleSave();
                }
            }
        };

        document.addEventListener('keydown', handleKeyDown);
        return () => {
            document.removeEventListener('keydown', handleKeyDown);
        };
    }, [handleSave, readOnly, hasUnsavedChanges]);

    // Add beforeunload event listener to warn when closing with unsaved changes
    React.useEffect(() => {
        const handleBeforeUnload = (e: BeforeUnloadEvent) => {
            if (hasUnsavedChanges && !readOnly) {
                // Standard way to show confirmation dialog when closing
                const message = 'You have unsaved changes in the editor. Are you sure you want to leave?';
                e.preventDefault();
                return message;
            }
            return undefined;
        };

        window.addEventListener('beforeunload', handleBeforeUnload);
        return () => {
            window.removeEventListener('beforeunload', handleBeforeUnload);
        };
    }, [hasUnsavedChanges, readOnly]);

    return (
        <>
            {/* Toolbar with filename and save button */}
            {(onSave || filename || readOnly) && (
                <div className={styles.toolbar}>
                    <div className={styles.filenameContainer}>
                        {filename && (
                            <Text as="h1" className={styles.filename}>
                                {filename.replace(/\.[^/.]+$/, '')}
                            </Text>
                        )}
                        {readOnly && (
                            <div className={styles.readOnlyIndicator}>
                                <LockClosedRegular />
                                <Text>{isBackendReadOnly ? 'View-only due to assistant at work' : 'View-only'}</Text>
                            </div>
                        )}
                    </div>
                    <div className={styles.buttonGroup}>
                        {onSave && !readOnly && (
                            <Button
                                appearance="subtle"
                                icon={<SaveRegular />}
                                onClick={handleSave}
                                disabled={!hasUnsavedChanges}
                                className={hasUnsavedChanges ? styles.saveButton : undefined}
                            >
                                Save Changes
                            </Button>
                        )}
                        {onToggleReadOnly && !isBackendReadOnly && (
                            <Button
                                icon={readOnly ? <LockOpenRegular /> : <LockClosedRegular />}
                                onClick={onToggleReadOnly}
                                appearance="subtle"
                            >
                                {readOnly ? 'Switch to Edit Mode' : 'Switch to View Mode'}
                            </Button>
                        )}
                    </div>
                </div>
            )}
            <div className={styles.milkdownWrapper}>
                <Milkdown />
            </div>
        </>
    );
};

export interface MilkdownEditorWrapperProps extends MilkdownEditorProps {
    onSubmit?: (content: string) => Promise<void>;
}

export const MilkdownEditorWrapper: React.FC<MilkdownEditorWrapperProps> = ({
    content,
    onSubmit,
    filename,
    readOnly = false,
}) => {
    const styles = useStyles();
    const [isSubmitting, setIsSubmitting] = React.useState(false);
    const [isReadOnly, setIsReadOnly] = React.useState(readOnly);

    // Track if read-only state is backend-enforced
    const isBackendReadOnly = readOnly;

    React.useEffect(() => {
        setIsReadOnly(readOnly);
    }, [readOnly]);

    const handleSave = React.useCallback(
        async (updatedContent: string) => {
            if (!onSubmit || isSubmitting || isReadOnly) return;

            setIsSubmitting(true);
            try {
                await onSubmit(updatedContent);
            } finally {
                setIsSubmitting(false);
            }
        },
        [onSubmit, isSubmitting, isReadOnly],
    );

    const toggleReadOnly = React.useCallback(() => {
        // Only allow toggling if not backend-enforced
        if (!isBackendReadOnly) {
            setIsReadOnly(!isReadOnly);
        }
    }, [isReadOnly, isBackendReadOnly]);

    return (
        <div className={styles.editorContainer}>
            <MilkdownProvider>
                <MilkdownEditor
                    content={content}
                    onSave={onSubmit && !isReadOnly ? handleSave : undefined}
                    filename={filename}
                    readOnly={isReadOnly}
                    onToggleReadOnly={toggleReadOnly}
                    isBackendReadOnly={isBackendReadOnly}
                />
            </MilkdownProvider>
        </div>
    );
};


=== File: workbench-app/src/components/Conversations/ContentRenderers/MermaidContentRenderer.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Popover,
    PopoverSurface,
    PopoverTrigger,
    Text,
    Tooltip,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import { ErrorCircle20Regular, Info20Regular, ZoomFit24Regular } from '@fluentui/react-icons';
import mermaid from 'mermaid';
import React from 'react';
import { TooltipWrapper } from '../../App/TooltipWrapper';
import { DebugInspector } from '../DebugInspector';

mermaid.initialize({
    startOnLoad: false,
    theme: 'light',
    securityLevel: 'loose',
    flowchart: {
        useMaxWidth: true,
    },
});

const useClasses = makeStyles({
    root: {
        whiteSpace: 'normal',
        display: 'flex',
        flexDirection: 'column',
    },
    inspectorTrigger: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        color: tokens.colorStatusDangerForeground1,
        gap: tokens.spacingHorizontalXXS,
        cursor: 'pointer',
    },
    dialogTrigger: {
        position: 'relative',
    },
    inlineActions: {
        position: 'absolute',
        top: 0,
        right: 0,
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: tokens.spacingHorizontalS,
    },
    dialogSurface: {
        position: 'fixed',
        zIndex: tokens.zIndexPopup,
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        textAlign: 'center',
        backgroundColor: tokens.colorNeutralBackground1,
    },
    dialogContent: {
        ...shorthands.padding(tokens.spacingVerticalM),
    },
    dialogActions: {
        position: 'absolute',
        bottom: tokens.spacingVerticalM,
        right: tokens.spacingHorizontalM,
    },
});

interface MermaidContentRenderProps {
    content: string;
    clickToZoom?: boolean;
}

export const MermaidContentRenderer: React.FC<MermaidContentRenderProps> = (props) => {
    const { content, clickToZoom } = props;
    const classes = useClasses();
    const mainRef = React.useRef<HTMLPreElement>(null);
    const [parseError, setParseError] = React.useState<Error | null>(null);
    const [isPopupOpen, setIsPopupOpen] = React.useState(false);

    React.useEffect(() => {
        if (!mainRef.current) {
            return;
        }

        const mermaidRun = async () => {
            try {
                await mermaid.parse(content.trim());
            } catch (error) {
                setParseError(error as Error);
                return;
            }

            await mermaid.run({
                nodes: [mainRef.current!],
                suppressErrors: true,
            });
        };
        mermaidRun();
    }, [content]);

    const mermaidDiagram = (
        <pre ref={mainRef} className="mermaid">
            {content.trim()}
        </pre>
    );

    return (
        <div className={classes.root}>
            {parseError && (
                <DebugInspector
                    trigger={
                        <Tooltip
                            content="Display debug information to indicate how this content was created."
                            relationship="label"
                        >
                            <div className={classes.inspectorTrigger}>
                                <ErrorCircle20Regular />
                                <Text>Error parsing mermaid content. Click for more information.</Text>
                            </div>
                        </Tooltip>
                    }
                    debug={{
                        parseError,
                    }}
                />
            )}
            {clickToZoom && (
                <div className={classes.dialogTrigger}>
                    <div className={classes.inlineActions}>
                        <Popover openOnHover>
                            <PopoverTrigger>
                                <Info20Regular />
                            </PopoverTrigger>
                            <PopoverSurface>
                                <pre>{content.trim()}</pre>
                            </PopoverSurface>
                        </Popover>
                        <TooltipWrapper content="Zoom diagram">
                            <Button icon={<ZoomFit24Regular />} onClick={() => setIsPopupOpen(true)} />
                        </TooltipWrapper>
                    </div>
                    {mermaidDiagram}
                </div>
            )}
            {clickToZoom && isPopupOpen && (
                <div className={classes.dialogSurface}>
                    <div className={classes.dialogContent}>
                        <MermaidContentRenderer content={content} />
                    </div>
                    <div className={classes.dialogActions}>
                        <Button appearance="primary" onClick={() => setIsPopupOpen(false)}>
                            Close
                        </Button>
                    </div>
                </div>
            )}
            {!clickToZoom && mermaidDiagram}
        </div>
    );
};


=== File: workbench-app/src/components/Conversations/ContentRenderers/MusicABCContentRenderer.css ===
/* Copyright (c) Microsoft. All rights reserved. */

.abc-midi-link a {
    display: block;
    text-align: center;
    color: #0078d4;
}


=== File: workbench-app/src/components/Conversations/ContentRenderers/MusicABCContentRenderer.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { generateUuid } from '@azure/ms-rest-js';
import { makeStyles, shorthands, tokens } from '@fluentui/react-components';
import { Info16Regular } from '@fluentui/react-icons';
import abcjs from 'abcjs';
import 'abcjs/abcjs-audio.css';
import debug from 'debug';
import React from 'react';
import { Constants } from '../../../Constants';
import { TooltipWrapper } from '../../App/TooltipWrapper';
import './MusicABCContentRenderer.css';

const log = debug(Constants.debug.root).extend('music-abc-content-renderer');

const useClasses = makeStyles({
    root: {
        whiteSpace: 'normal',
        position: 'relative',
    },
    controller: {
        ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalL, tokens.spacingVerticalXXXL),
    },
    infoButton: {
        position: 'absolute',
        top: tokens.spacingVerticalM,
        right: tokens.spacingHorizontalM,
    },
});

interface MusicABCContentRendererProps {
    content: string;
}

export const MusicABCContentRenderer: React.FC<MusicABCContentRendererProps> = (props) => {
    const { content } = props;
    const classes = useClasses();
    const [id] = React.useState(generateUuid());
    const abcAudioRef = React.useRef<HTMLDivElement>(null);

    React.useEffect(() => {
        void (async () => {
            abcjs.renderAbc(`abc-paper-${id}`, content, { responsive: 'resize' });

            const midi = abcjs.synth.getMidiFile(content, { midiOutputType: 'link' });
            const midiLink = document.getElementById(`abc-midi-${id}`);
            if (midiLink) {
                midiLink.innerHTML = midi;
            }
        })();
    }, [content, id]);

    React.useEffect(() => {
        void (async () => {
            if (!abcAudioRef.current || !abcjs.synth.supportsAudio()) return;

            const cursorControl = {};
            const audioParams = {
                chordsOff: false,
            };

            const visualObj = abcjs.renderAbc('*', content, { responsive: 'resize' });

            const synthControl = new abcjs.synth.SynthController();
            synthControl.load(`#abc-audio-${id}`, cursorControl, {
                displayLoop: true,
                displayRestart: true,
                displayPlay: true,
                displayProgress: true,
                displayWarp: true,
            });

            await synthControl.setTune(visualObj[0], false, audioParams);
            log('audio loaded');
        })();
    }, [content, id]);

    return (
        <div className={classes.root}>
            <div id={`abc-paper-${id}`} />
            <div id={`abc-midi-${id}`} className="abc-midi-link" />
            <div id={`abc-audio-${id}`} ref={abcAudioRef} className={classes.controller} />
            <TooltipWrapper content={content}>
                <Info16Regular className={classes.infoButton} />
            </TooltipWrapper>
        </div>
    );
};


=== File: workbench-app/src/components/Conversations/ContextWindow.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { ProgressBar } from '@fluentui/react-components';
import React from 'react';
import { Conversation } from '../../models/Conversation';

interface FileListProps {
    conversation: Conversation;
}

export const ContextWindow: React.FC<FileListProps> = (props) => {
    const { conversation } = props;

    const tokenCountToDisplay = (count: number | undefined, includeLabel: boolean = true) => {
        const label = includeLabel ? ' token' + (count !== 1 ? 's' : '') : '';
        if (!count) {
            return `0${label}`;
        }
        if (count < 1_000) {
            return `${count}${label}`;
        } else if (count < 1_000_000) {
            return `${(count / 1_000).toFixed(1).toString().replaceAll('.0', '')}k${label}`;
        } else {
            return `${(count / 1_000_000).toFixed(1).toString().replaceAll('.0', '')}m${label}`;
        }
    };

    if (conversation.metadata?.token_counts === undefined) {
        return 'Token count not available';
    }

    const { total: totalTokenCount, max: maxTokenCount } = conversation.metadata?.token_counts;

    return (
        <>
            {tokenCountToDisplay(totalTokenCount, false)} of {tokenCountToDisplay(maxTokenCount)} (
            {Math.floor((totalTokenCount / maxTokenCount) * 100)}%)
            <ProgressBar thickness="large" value={totalTokenCount / maxTokenCount}></ProgressBar>
        </>
    );
};


=== File: workbench-app/src/components/Conversations/ConversationCreate.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    DialogOpenChangeData,
    DialogOpenChangeEvent,
    DialogTrigger,
    makeStyles,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { Conversation } from '../../models/Conversation';
import { useCreateConversationMutation } from '../../services/workbench';
import { DialogControl } from '../App/DialogControl';

const useClasses = makeStyles({
    dialogContent: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
});

interface ConversationCreateProps {
    open: boolean;
    onOpenChange?: (open: boolean) => void;
    onCreate?: (conversation: Conversation) => void;
    metadata?: {
        [key: string]: any;
    };
}

export const ConversationCreate: React.FC<ConversationCreateProps> = (props) => {
    const { open, onOpenChange, onCreate, metadata } = props;
    const classes = useClasses();
    const [createConversation] = useCreateConversationMutation();
    const [submitted, setSubmitted] = React.useState(false);

    const handleSave = React.useCallback(async () => {
        if (submitted) {
            return;
        }
        setSubmitted(true);

        try {
            const conversation = await createConversation({ metadata }).unwrap();
            onOpenChange?.(false);
            onCreate?.(conversation);
        } finally {
            setSubmitted(false);
        }
    }, [createConversation, metadata, onCreate, onOpenChange, submitted]);

    React.useEffect(() => {
        if (!open) {
            return;
        }
        setSubmitted(false);
    }, [open]);

    const handleOpenChange = React.useCallback(
        (_event: DialogOpenChangeEvent, data: DialogOpenChangeData) => {
            onOpenChange?.(data.open);
        },
        [onOpenChange],
    );

    return (
        <DialogControl
            open={open}
            classNames={{
                dialogContent: classes.dialogContent,
            }}
            onOpenChange={handleOpenChange}
            title="New Conversation"
            content={
                <form
                    onSubmit={(event) => {
                        event.preventDefault();
                        handleSave();
                    }}
                >
                    <button disabled={submitted} type="submit" hidden />
                </form>
            }
            closeLabel="Cancel"
            additionalActions={[
                <DialogTrigger key="save" disableButtonEnhancement>
                    <Button disabled={submitted} appearance="primary" onClick={handleSave}>
                        {submitted ? 'Saving...' : 'Save'}
                    </Button>
                </DialogTrigger>,
            ]}
        />
    );
};


=== File: workbench-app/src/components/Conversations/ConversationDuplicate.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    DialogOpenChangeData,
    DialogOpenChangeEvent,
    DialogTrigger,
    Field,
    Input,
    Radio,
    RadioGroup,
} from '@fluentui/react-components';
import { SaveCopy24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useNotify } from '../../libs/useNotify';
import { useWorkbenchService } from '../../libs/useWorkbenchService';
import { Utility } from '../../libs/Utility';
import { useDuplicateConversationMutation } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';
import { DialogControl } from '../App/DialogControl';

const enum AssistantParticipantOption {
    SameAssistants = 'Include the same assistants in the new conversation.',
    CloneAssistants = 'Create copies of the assistants in the new conversation.',
}

const useConversationDuplicateControls = (id: string) => {
    const workbenchService = useWorkbenchService();
    const [assistantParticipantOption, setAssistantParticipantOption] = React.useState<AssistantParticipantOption>(
        AssistantParticipantOption.SameAssistants,
    );
    const [duplicateConversation] = useDuplicateConversationMutation();
    const [submitted, setSubmitted] = React.useState(false);
    const [title, setTitle] = React.useState('');

    const handleDuplicateConversation = React.useCallback(
        async (onDuplicate?: (conversationId: string) => Promise<void>, onError?: (error: Error) => void) => {
            try {
                await Utility.withStatus(setSubmitted, async () => {
                    switch (assistantParticipantOption) {
                        case AssistantParticipantOption.SameAssistants:
                            const results = await duplicateConversation({ id, title }).unwrap();
                            if (results.conversationIds.length === 0) {
                                throw new Error('No conversation ID returned');
                            }
                            await onDuplicate?.(results.conversationIds[0]);
                            break;
                        case AssistantParticipantOption.CloneAssistants:
                            const duplicateIds = await workbenchService.exportThenImportConversationAsync([id]);
                            await onDuplicate?.(duplicateIds[0]);
                            break;
                    }
                });
            } catch (error) {
                onError?.(error as Error);
            }
        },
        [assistantParticipantOption, duplicateConversation, id, title, workbenchService],
    );

    const duplicateConversationForm = React.useCallback(
        () => (
            <>
                <Field label="Title" required={true}>
                    <Input
                        value={title}
                        onChange={(_, data) => setTitle(data.value)}
                        required={true}
                        placeholder="Enter a title for the duplicated conversation"
                    />
                </Field>
                <Field label="Assistant Duplication Options" required={true}>
                    <RadioGroup
                        defaultValue={assistantParticipantOption}
                        onChange={(_, data) => setAssistantParticipantOption(data.value as AssistantParticipantOption)}
                        required={true}
                    >
                        <Radio
                            value={AssistantParticipantOption.SameAssistants}
                            label={AssistantParticipantOption.SameAssistants}
                        />
                        <Radio
                            value={AssistantParticipantOption.CloneAssistants}
                            label={AssistantParticipantOption.CloneAssistants}
                        />
                    </RadioGroup>
                </Field>
            </>
        ),
        [assistantParticipantOption, title],
    );

    const duplicateConversationButton = React.useCallback(
        (onDuplicate?: (conversationId: string) => Promise<void>, onError?: (error: Error) => void) => (
            <Button
                key="duplicate"
                appearance="primary"
                onClick={() => handleDuplicateConversation(onDuplicate, onError)}
                disabled={submitted}
            >
                {submitted ? 'Duplicating...' : 'Duplicate'}
            </Button>
        ),
        [handleDuplicateConversation, submitted],
    );

    return {
        duplicateConversationForm,
        duplicateConversationButton,
    };
};

interface ConversationDuplicateDialogProps {
    conversationId: string;
    onDuplicate: (conversationId: string) => Promise<void>;
    open?: boolean;
    onOpenChange: (event: DialogOpenChangeEvent, data: DialogOpenChangeData) => void;
}

export const ConversationDuplicateDialog: React.FC<ConversationDuplicateDialogProps> = (props) => {
    const { conversationId, onDuplicate, open, onOpenChange } = props;
    const { duplicateConversationForm, duplicateConversationButton } = useConversationDuplicateControls(conversationId);
    const { notifyWarning } = useNotify();

    const handleError = React.useCallback(
        (error: Error) => {
            notifyWarning({
                id: 'error',
                title: 'Duplicate conversation failed',
                message: error.message,
            });
        },
        [notifyWarning],
    );

    return (
        <DialogControl
            open={open}
            onOpenChange={onOpenChange}
            title="Duplicate conversation"
            content={duplicateConversationForm()}
            closeLabel="Cancel"
            additionalActions={[duplicateConversationButton(onDuplicate, handleError)]}
        />
    );
};

interface ConversationDuplicateProps {
    conversationId: string;
    disabled?: boolean;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
    onDuplicate?: (conversationId: string) => Promise<void>;
    onDuplicateError?: (error: Error) => void;
}

export const ConversationDuplicate: React.FC<ConversationDuplicateProps> = (props) => {
    const { conversationId, iconOnly, asToolbarButton, onDuplicate, onDuplicateError } = props;
    const { duplicateConversationForm, duplicateConversationButton } = useConversationDuplicateControls(conversationId);

    return (
        <CommandButton
            description="Duplicate conversation"
            icon={<SaveCopy24Regular />}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
            label="Duplicate"
            dialogContent={{
                title: 'Duplicate conversation',
                content: duplicateConversationForm(),
                closeLabel: 'Cancel',
                additionalActions: [
                    <DialogTrigger key="duplicate" disableButtonEnhancement>
                        {duplicateConversationButton(onDuplicate, onDuplicateError)}
                    </DialogTrigger>,
                ],
            }}
        />
    );
};


=== File: workbench-app/src/components/Conversations/ConversationExport.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { ProgressBar } from '@fluentui/react-components';
import React from 'react';
import { useExportUtility } from '../../libs/useExportUtility';
import { useNotify } from '../../libs/useNotify';
import { Utility } from '../../libs/Utility';
import { ContentExport } from '../App/ContentExport';
import { DialogControl } from '../App/DialogControl';

interface ConversationExportWithStatusDialogProps {
    conversationId?: string;
    onExport: (id: string) => Promise<void>;
}

export const ConversationExportWithStatusDialog: React.FC<ConversationExportWithStatusDialogProps> = (props) => {
    const { conversationId, onExport } = props;
    const { exportConversation } = useExportUtility();
    const { notifyWarning } = useNotify();
    const [submitted, setSubmitted] = React.useState(false);

    const handleError = React.useCallback(
        (error: Error) => {
            notifyWarning({
                id: 'error',
                title: 'Export conversation failed',
                message: error.message,
            });
        },
        [notifyWarning],
    );

    React.useEffect(() => {
        if (!conversationId) {
            return;
        }

        (async () => {
            try {
                await Utility.withStatus(setSubmitted, async () => {
                    await exportConversation(conversationId);
                    await onExport(conversationId);
                });
            } catch (error) {
                handleError(error as Error);
            }
        })();
    }, [conversationId, exportConversation, handleError, notifyWarning, onExport]);

    return (
        <DialogControl
            open={submitted}
            title="Exporting Conversation"
            hideDismissButton
            content={
                <p>
                    <ProgressBar />
                </p>
            }
        />
    );
};

interface ConversationExportProps {
    conversationId: string;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const ConversationExport: React.FC<ConversationExportProps> = (props) => {
    const { conversationId, iconOnly, asToolbarButton } = props;
    const { exportConversationFunction } = useExportUtility();

    return (
        <ContentExport
            id={conversationId}
            contentTypeLabel="conversation"
            exportFunction={exportConversationFunction}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
        />
    );
};


=== File: workbench-app/src/components/Conversations/ConversationFileIcon.tsx ===
import { Image } from '@fluentui/react-components';
import { FileTypeIconSize, getFileTypeIconAsUrl } from '@fluentui/react-file-type-icons';
import { FileIconTypeInput } from '@fluentui/react-file-type-icons/lib/FileIconType';
import React from 'react';
import { ConversationFile } from '../../models/ConversationFile';

interface ConversationFileIconProps {
    file: File | ConversationFile | string;
    className?: string;
    /**
     * The type of file type icon you need. Use this property for
     * file type icons that are not associated with a file extension,
     * such as folder.
     */
    type?: FileIconTypeInput;
    size?: FileTypeIconSize;
}

export const ConversationFileIcon: React.FC<ConversationFileIconProps> = (props) => {
    const { file, className, type, size } = props;

    // if it is of type File and is an image, display the image instead of the file type icon
    if (file instanceof File && file.type.startsWith('image/')) {
        return <Image className={className} src={URL.createObjectURL(file)} alt={file.name} />;
    }

    // for all other cases, display the file type icon
    const filename = typeof file === 'string' ? file : file.name;
    return (
        <Image
            className={className}
            src={getFileTypeIconAsUrl({ extension: filename.split('.').pop() ?? '', type, size })}
            alt={filename}
        />
    );
};


=== File: workbench-app/src/components/Conversations/ConversationRemove.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogTrigger } from '@fluentui/react-components';
import { PlugDisconnected24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Conversation } from '../../models/Conversation';
import { useAppDispatch, useAppSelector } from '../../redux/app/hooks';
import { setActiveConversationId } from '../../redux/features/app/appSlice';
import { useRemoveConversationParticipantMutation } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';
import { DialogControl } from '../App/DialogControl';

const useConversationRemoveControls = () => {
    const activeConversationId = useAppSelector((state) => state.app.activeConversationId);
    const dispatch = useAppDispatch();
    const [removeConversationParticipant] = useRemoveConversationParticipantMutation();
    const [submitted, setSubmitted] = React.useState(false);

    const handleRemove = React.useCallback(
        async (conversations: Conversation[], participantId: string, onRemove?: () => void) => {
            if (submitted) {
                return;
            }
            setSubmitted(true);

            try {
                for (const conversation of conversations) {
                    const conversationId = conversation.id;
                    if (activeConversationId === conversationId) {
                        // Clear the active conversation if it is the one being removed
                        dispatch(setActiveConversationId(undefined));
                    }

                    await removeConversationParticipant({
                        conversationId,
                        participantId,
                    });
                }
                onRemove?.();
            } finally {
                setSubmitted(false);
            }
        },
        [activeConversationId, dispatch, removeConversationParticipant, submitted],
    );

    const removeConversationForm = React.useCallback(
        (hasMultipleConversations: boolean) =>
            hasMultipleConversations ? (
                <p>Are you sure you want to remove these conversations from your list ?</p>
            ) : (
                <p>Are you sure you want to remove this conversation from your list ?</p>
            ),
        [],
    );

    const removeConversationButton = React.useCallback(
        (conversations: Conversation[], participantId: string, onRemove?: () => void) => (
            <DialogTrigger disableButtonEnhancement>
                <Button
                    appearance="primary"
                    onClick={() => handleRemove(conversations, participantId, onRemove)}
                    disabled={submitted}
                >
                    {submitted ? 'Removing...' : 'Remove'}
                </Button>
            </DialogTrigger>
        ),
        [handleRemove, submitted],
    );

    return {
        removeConversationForm,
        removeConversationButton,
    };
};

interface ConversationRemoveDialogProps {
    conversations: Conversation | Conversation[];
    participantId: string;
    onRemove: () => void;
    onCancel: () => void;
}

export const ConversationRemoveDialog: React.FC<ConversationRemoveDialogProps> = (props) => {
    const { conversations, participantId, onRemove, onCancel } = props;
    const { removeConversationForm, removeConversationButton } = useConversationRemoveControls();

    const hasMultipleConversations = Array.isArray(conversations);
    const conversationsToRemove = hasMultipleConversations ? conversations : [conversations];

    return (
        <DialogControl
            open={true}
            onOpenChange={onCancel}
            title={hasMultipleConversations ? 'Remove Conversations' : 'Remove Conversation'}
            content={removeConversationForm(hasMultipleConversations)}
            additionalActions={[removeConversationButton(conversationsToRemove, participantId, onRemove)]}
        />
    );
};

interface ConversationRemoveProps {
    conversations: Conversation | Conversation[];
    participantId: string;
    onRemove?: () => void;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const ConversationRemove: React.FC<ConversationRemoveProps> = (props) => {
    const { conversations, onRemove, iconOnly, asToolbarButton, participantId } = props;
    const { removeConversationForm, removeConversationButton } = useConversationRemoveControls();

    const hasMultipleConversations = Array.isArray(conversations);
    const conversationsToRemove = hasMultipleConversations ? conversations : [conversations];
    const description = hasMultipleConversations ? 'Remove Conversations' : 'Remove Conversation';

    return (
        <CommandButton
            description={description}
            icon={<PlugDisconnected24Regular />}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
            label="Remove"
            dialogContent={{
                title: description,
                content: removeConversationForm(hasMultipleConversations),
                closeLabel: 'Cancel',
                additionalActions: [removeConversationButton(conversationsToRemove, participantId, onRemove)],
            }}
        />
    );
};


=== File: workbench-app/src/components/Conversations/ConversationRename.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogOpenChangeData, DialogOpenChangeEvent, Field, Input } from '@fluentui/react-components';
import { EditRegular } from '@fluentui/react-icons';
import React from 'react';
import { useNotify } from '../../libs/useNotify';
import { Utility } from '../../libs/Utility';
import { useUpdateConversationMutation } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';
import { DialogControl } from '../App/DialogControl';

export const useConversationRenameControls = (id: string, value: string) => {
    const [updateConversation] = useUpdateConversationMutation();
    const [newTitle, setNewTitle] = React.useState(value);
    const [submitted, setSubmitted] = React.useState(false);

    const handleRename = React.useCallback(
        async (onRename?: (id: string, value: string) => Promise<void>, onError?: (error: Error) => void) => {
            try {
                await Utility.withStatus(setSubmitted, async () => {
                    await updateConversation({ id, title: newTitle });
                    await onRename?.(id, newTitle);
                });
            } catch (error) {
                onError?.(error as Error);
            }
        },
        [id, newTitle, updateConversation],
    );

    const renameConversationForm = React.useCallback(
        (onRename?: (id: string, value: string) => Promise<void>) => (
            <form
                onSubmit={(event) => {
                    event.preventDefault();
                    handleRename(onRename);
                }}
            >
                <Field label="Title">
                    <Input disabled={submitted} value={newTitle} onChange={(_event, data) => setNewTitle(data.value)} />
                </Field>
            </form>
        ),
        [handleRename, newTitle, submitted],
    );

    const renameConversationButton = React.useCallback(
        (onRename?: (id: string, value: string) => Promise<void>, onError?: (error: Error) => void) => (
            <Button
                key="rename"
                disabled={!newTitle || submitted}
                onClick={() => handleRename(onRename, onError)}
                appearance="primary"
            >
                {submitted ? 'Renaming...' : 'Rename'}
            </Button>
        ),
        [handleRename, newTitle, submitted],
    );

    return {
        renameConversationForm,
        renameConversationButton,
    };
};

interface ConversationRenameDialogProps {
    conversationId: string;
    value: string;
    onRename: (id: string, value: string) => Promise<void>;
    open?: boolean;
    onOpenChange: (event: DialogOpenChangeEvent, data: DialogOpenChangeData) => void;
}

export const ConversationRenameDialog: React.FC<ConversationRenameDialogProps> = (props) => {
    const { conversationId, value, onRename, open, onOpenChange } = props;
    const { renameConversationForm, renameConversationButton } = useConversationRenameControls(conversationId, value);
    const { notifyWarning } = useNotify();

    const handleError = React.useCallback(
        (error: Error) => {
            notifyWarning({
                id: 'conversation-rename-error',
                title: 'Rename conversation failed',
                message: error.message,
            });
        },
        [notifyWarning],
    );

    return (
        <DialogControl
            open={open}
            onOpenChange={onOpenChange}
            title="Rename conversation"
            content={renameConversationForm(onRename)}
            closeLabel="Cancel"
            additionalActions={[renameConversationButton(onRename, handleError)]}
        />
    );
};

interface ConversationRenameProps {
    conversationId: string;
    disabled?: boolean;
    value: string;
    onRename?: (conversationId: string, value: string) => Promise<void>;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const ConversationRename: React.FC<ConversationRenameProps> = (props) => {
    const { conversationId, value, onRename, disabled, iconOnly, asToolbarButton } = props;
    const { renameConversationForm, renameConversationButton } = useConversationRenameControls(conversationId, value);

    return (
        <CommandButton
            iconOnly={iconOnly}
            icon={<EditRegular />}
            label="Rename"
            disabled={disabled}
            description="Rename conversation"
            asToolbarButton={asToolbarButton}
            dialogContent={{
                title: 'Rename conversation',
                content: renameConversationForm(),
                closeLabel: 'Cancel',
                additionalActions: [renameConversationButton(onRename)],
            }}
        />
    );
};


=== File: workbench-app/src/components/Conversations/ConversationShare.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Share24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Conversation } from '../../models/Conversation';
import { CommandButton } from '../App/CommandButton';
import { DialogControl } from '../App/DialogControl';
import { ConversationShareList } from './ConversationShareList';

const useConversationShareControls = () => {
    return {
        shareConversationForm: React.useCallback(
            (conversation: Conversation) => (
                <p>
                    <ConversationShareList conversation={conversation} />
                </p>
            ),
            [],
        ),
    };
};

interface ConversationShareDialogProps {
    conversation: Conversation;
    onClose: () => void;
}

export const ConversationShareDialog: React.FC<ConversationShareDialogProps> = (props) => {
    const { conversation, onClose } = props;
    const { shareConversationForm } = useConversationShareControls();

    return (
        <DialogControl
            open={true}
            onOpenChange={onClose}
            title="Share conversation"
            content={shareConversationForm(conversation)}
        />
    );
};

interface ConversationShareProps {
    conversation: Conversation;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const ConversationShare: React.FC<ConversationShareProps> = (props) => {
    const { conversation, iconOnly, asToolbarButton } = props;
    if (!conversation) {
        throw new Error('ConversationId is required');
    }

    const { shareConversationForm } = useConversationShareControls();

    const readOnly = conversation.conversationPermission !== 'read_write';

    const dialogContent = readOnly
        ? undefined
        : {
              title: 'Manage Shares for Conversation',
              content: shareConversationForm(conversation),
          };

    return (
        <CommandButton
            icon={<Share24Regular />}
            iconOnly={iconOnly}
            disabled={readOnly}
            asToolbarButton={asToolbarButton}
            label="Share"
            description="Share conversation"
            dialogContent={dialogContent}
        />
    );
};


=== File: workbench-app/src/components/Conversations/ConversationShareCreate.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    DialogOpenChangeData,
    DialogOpenChangeEvent,
    DialogTrigger,
    Field,
    Input,
    makeStyles,
    Radio,
    RadioGroup,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { ConversationShareType, useConversationUtility } from '../../libs/useConversationUtility';
import { Conversation } from '../../models/Conversation';
import { ConversationShare } from '../../models/ConversationShare';
import { useCreateShareMutation } from '../../services/workbench/share';
import { DialogControl } from '../App/DialogControl';

const useClasses = makeStyles({
    dialogContent: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
});

interface ConversationShareCreateProps {
    conversation: Conversation;
    linkToMessageId?: string;
    onCreated?: (conversationShare: ConversationShare) => void;
    onClosed?: () => void;
}

export const ConversationShareCreate: React.FC<ConversationShareCreateProps> = (props) => {
    const { conversation, linkToMessageId, onCreated, onClosed } = props;
    const classes = useClasses();
    const [createShare] = useCreateShareMutation();
    const [submitted, setSubmitted] = React.useState(false);
    const defaultShareLabel = conversation.title + (linkToMessageId ? ' - message link' : '');
    const [shareLabel, setShareLabel] = React.useState(defaultShareLabel);
    const defaultShareType = ConversationShareType.InvitedToParticipate;
    const [shareType, setShareType] = React.useState(defaultShareType);
    const conversationUtility = useConversationUtility();

    const handleCreate = React.useCallback(async () => {
        if (submitted) {
            return;
        }
        setSubmitted(true);

        try {
            // Get the permission and metadata for the share type.
            const { permission, metadata } = conversationUtility.getShareTypeMetadata(shareType, linkToMessageId);
            // Create the share.
            const conversationShare = await createShare({
                conversationId: conversation!.id,
                label: shareLabel,
                conversationPermission: permission,
                metadata: metadata,
            }).unwrap();
            onCreated?.(conversationShare);
        } finally {
            setSubmitted(false);
        }
    }, [submitted, conversationUtility, shareType, linkToMessageId, createShare, conversation, shareLabel, onCreated]);

    const handleFocus = React.useCallback((event: React.FocusEvent<HTMLInputElement>) => event.target.select(), []);

    const createTitle = React.useMemo(
        () => (linkToMessageId ? 'Create a new message share link' : 'Create a new share link'),
        [linkToMessageId],
    );

    const handleOpenChange = React.useCallback(
        (_: DialogOpenChangeEvent, data: DialogOpenChangeData) => {
            if (!data.open) {
                onClosed?.();
            }
        },
        [onClosed],
    );

    return (
        <DialogControl
            defaultOpen={true}
            onOpenChange={handleOpenChange}
            title={createTitle}
            classNames={{
                dialogContent: classes.dialogContent,
            }}
            content={
                <>
                    <Field label="Label for display in your Shared links list" required={true}>
                        <Input
                            disabled={submitted}
                            value={shareLabel}
                            onChange={(_event, data) => setShareLabel(data.value)}
                            onFocus={handleFocus}
                            required={true}
                        />
                    </Field>
                    <Field label="Permissions" required={true}>
                        <RadioGroup
                            defaultValue={shareType}
                            onChange={(_, data) => setShareType(data.value as ConversationShareType)}
                            required={true}
                        >
                            <Radio
                                value={ConversationShareType.InvitedToParticipate}
                                label={`${ConversationShareType.InvitedToParticipate} in the conversation (read/write)`}
                            />
                            <Radio
                                value={ConversationShareType.InvitedToObserve}
                                label={`${ConversationShareType.InvitedToObserve} the conversation (read-only)`}
                            />
                            {!linkToMessageId && (
                                <Radio
                                    value={ConversationShareType.InvitedToDuplicate}
                                    label={`${ConversationShareType.InvitedToDuplicate} the conversation (read-only)`}
                                />
                            )}
                        </RadioGroup>
                    </Field>
                </>
            }
            closeLabel="Cancel"
            additionalActions={[
                <DialogTrigger key="create" disableButtonEnhancement>
                    <Button disabled={!shareLabel || submitted} onClick={handleCreate} appearance="primary">
                        {submitted ? 'Creating...' : 'Create'}
                    </Button>
                </DialogTrigger>,
            ]}
        />
    );
};


=== File: workbench-app/src/components/Conversations/ConversationShareList.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { Conversation } from '../../models/Conversation';
import { useGetSharesQuery } from '../../services/workbench/share';
import { Loading } from '../App/Loading';
import { MyShares } from './MyShares';

interface ConversationShareListProps {
    conversation: Conversation;
}

export const ConversationShareList: React.FC<ConversationShareListProps> = (props) => {
    const { conversation } = props;
    const {
        data: conversationShares,
        error: conversationSharesError,
        isLoading: conversationSharesLoading,
    } = useGetSharesQuery({
        conversationId: conversation.id,
        includeUnredeemable: false,
    });

    if (!conversation) {
        throw new Error('Conversation is required');
    }

    if (conversationSharesError) {
        throw new Error(`Error loading conversation shares: ${JSON.stringify(conversationSharesError)}`);
    }

    if (conversationSharesLoading || !conversationShares) {
        return <Loading />;
    }

    return (
        <MyShares
            conversation={conversation}
            shares={conversationShares}
            title={`Shares for "${conversation.title}"`}
        />
    );
};


=== File: workbench-app/src/components/Conversations/ConversationShareView.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import {
    DialogOpenChangeData,
    DialogOpenChangeEvent,
    Field,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { useConversationUtility } from '../../libs/useConversationUtility';
import { ConversationShare } from '../../models/ConversationShare';
import { CopyButton } from '../App/CopyButton';
import { DialogControl } from '../App/DialogControl';

const useClasses = makeStyles({
    dialogContent: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
    shareLink: {
        display: 'flex',
        flexDirection: 'row',
        gap: tokens.spacingHorizontalS,
        alignItems: 'center',
        ...shorthands.padding(tokens.spacingVerticalXXS, 0, tokens.spacingVerticalXXS),
    },
});

interface ConversationShareViewProps {
    conversationShare: ConversationShare;
    showDetails?: boolean;
    onClosed?: () => void;
}

export const ConversationShareView: React.FC<ConversationShareViewProps> = (props) => {
    const { conversationShare, onClosed, showDetails } = props;
    const conversationUtility = useConversationUtility();
    const classes = useClasses();

    const { shareType, linkToMessageId } = conversationUtility.getShareType(conversationShare);
    const link = conversationUtility.getShareLink(conversationShare);

    const handleOpenChange = React.useCallback(
        (_: DialogOpenChangeEvent, data: DialogOpenChangeData) => {
            if (!data.open) {
                onClosed?.();
            }
        },
        [onClosed],
    );

    const linkToConversation = (conversationId: string) => `${window.location.origin}/conversation/${conversationId}`;

    return (
        <DialogControl
            defaultOpen={true}
            onOpenChange={handleOpenChange}
            classNames={{
                dialogContent: classes.dialogContent,
            }}
            title="Share link details"
            content={
                <>
                    <Field label="Share label">
                        <strong>{conversationShare.label}</strong>
                    </Field>
                    <Field label="Share link">
                        <div className={classes.shareLink}>
                            <a href={link}>{link}</a>
                            <CopyButton appearance="primary" data={link} tooltip="Copy share link" />
                        </div>
                    </Field>
                    {showDetails && (
                        <>
                            <Field label="Conversation">
                                <a href={linkToConversation(conversationShare.conversationId)}>
                                    {conversationShare.conversationTitle}
                                </a>
                            </Field>
                            {linkToMessageId && <Field label="Links to message">{linkToMessageId}</Field>}
                            <Field label="Permission">{shareType.toString()}</Field>
                            <Field label="Created">
                                {new Date(Date.parse(conversationShare.createdDateTime + 'Z')).toLocaleString()}
                            </Field>
                        </>
                    )}
                </>
            }
        />
    );
};


=== File: workbench-app/src/components/Conversations/ConversationTranscript.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { ArrowDownload24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useWorkbenchService } from '../../libs/useWorkbenchService';
import { Conversation } from '../../models/Conversation';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { CommandButton } from '../App/CommandButton';

interface ConversationTranscriptProps {
    conversation: Conversation;
    participants: ConversationParticipant[];
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const ConversationTranscript: React.FC<ConversationTranscriptProps> = (props) => {
    const { conversation, participants, iconOnly, asToolbarButton } = props;
    const workbenchService = useWorkbenchService();
    const [submitted, setSubmitted] = React.useState(false);

    const getTranscript = React.useCallback(async () => {
        if (submitted) {
            return;
        }
        setSubmitted(true);

        try {
            const { blob, filename } = await workbenchService.exportTranscriptAsync(conversation, participants);
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            URL.revokeObjectURL(url);
        } finally {
            setSubmitted(false);
        }
    }, [submitted, workbenchService, conversation, participants]);

    return (
        <div>
            <CommandButton
                description={`Download transcript`}
                icon={<ArrowDownload24Regular />}
                iconOnly={iconOnly}
                asToolbarButton={asToolbarButton}
                disabled={submitted}
                label={submitted ? 'Downloading...' : 'Download'}
                onClick={getTranscript}
            />
        </div>
    );
};


=== File: workbench-app/src/components/Conversations/ConversationsImport.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { useWorkbenchService } from '../../libs/useWorkbenchService';
import { ContentImport } from '../App/ContentImport';

interface ConversationsImportProps {
    disabled?: boolean;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
    appearance?: 'primary' | 'secondary' | 'outline' | 'subtle' | 'transparent';
    size?: 'small' | 'medium' | 'large';
    onImport?: (conversationIds: string[]) => void;
    onError?: (error: Error) => void;
}

export const ConversationsImport: React.FC<ConversationsImportProps> = (props) => {
    const { disabled, iconOnly, asToolbarButton, appearance, size, onImport, onError } = props;
    const workbenchService = useWorkbenchService();

    const importFile = async (file: File) => {
        const result = await workbenchService.importConversationsAsync(file);
        return result.conversationIds;
    };

    return (
        <ContentImport
            contentTypeLabel="conversations"
            importFunction={importFile}
            onImport={onImport}
            onError={onError}
            disabled={disabled}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
            appearance={appearance}
            size={size}
        />
    );
};


=== File: workbench-app/src/components/Conversations/DebugInspector.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogOpenChangeData, DialogOpenChangeEvent, Tooltip, makeStyles } from '@fluentui/react-components';
import { Info16Regular } from '@fluentui/react-icons';
import React from 'react';
import { JSONTree, KeyPath } from 'react-json-tree';
import { DialogControl } from '../App/DialogControl';
import { Loading } from '../App/Loading';
import { ContentRenderer } from './ContentRenderers/ContentRenderer';

const useClasses = makeStyles({
    root: {
        maxWidth: 'calc(100vw - 32px)',
        minWidth: 'min(600px, 100vw)',
        width: 'fit-content',
    },
    content: {
        height: 'calc(100vh - 150px)',
        width: 'calc(100vw - 100px)',
        paddingRight: '8px',
        boxSizing: 'border-box',
    },
});

interface DebugInspectorProps {
    debug?: { [key: string]: any };
    loading?: boolean;
    trigger?: JSX.Element;
    onOpen?: () => void;
    onClose?: () => void;
}

export const DebugInspector: React.FC<DebugInspectorProps> = (props) => {
    const { debug, loading, trigger, onOpen, onClose } = props;
    const classes = useClasses();

    const onOpenChanged = React.useCallback(
        (_: DialogOpenChangeEvent, data: DialogOpenChangeData) => {
            if (data.open) {
                onOpen?.();
                return;
            }
            onClose?.();
        },
        [onOpen, onClose],
    );

    if (!debug) {
        return null;
    }

    return (
        <DialogControl
            trigger={
                trigger || (
                    <Tooltip
                        content="Display debug information to indicate how this content was created."
                        relationship="label"
                    >
                        <Button appearance="subtle" size="small" icon={<Info16Regular />} />
                    </Tooltip>
                )
            }
            classNames={{ dialogSurface: classes.root }}
            title="Debug Inspection"
            onOpenChange={onOpenChanged}
            content={
                loading ? (
                    <Loading />
                ) : debug.content ? (
                    <ContentRenderer content={debug.content} contentType={debug.contentType} />
                ) : (
                    <div className={classes.content}>
                        <JSONTree
                            data={debug}
                            hideRoot
                            invertTheme
                            collectionLimit={10}
                            shouldExpandNodeInitially={(keyPath, _data, level) => {
                                // Intended to be processed in order of appearance, written to
                                // exit early if the criteria is met, fallthrough to the next
                                // condition if it is not and eventually return true.

                                // Expressed as an array of arrays to allow for multiple paths
                                // to be checked against the keyPath. Each path is checked in
                                // order of appearance, if any of the paths match the keyPath,
                                // the node will be collapsed.

                                // Behavior: If only a single key is provided, it will be
                                // treated as a single level, if multiple keys are provided,
                                // it will be treated as a path to the desired level.
                                // Paths do not need to be complete, they will be matched
                                // from the end of the keyPath and support skipping levels.

                                // Leave any of the following collapsed
                                // NOTE: the key path is expressed in _reverse_ order, so we need to
                                // compare it in reverse order (leaf first) as well.
                                const keepCollapsed = [
                                    ['content_safety'],
                                    ['content_filter_results'],
                                    ['image_url'],
                                    // Reversed from ['tools', 'parameters'] to match keyPath order
                                    ['parameters', 'tools'],
                                    ['message'],
                                ];

                                // Check if the current node should be kept collapsed
                                if (shouldKeepNodeCollapsed(keyPath, keepCollapsed)) {
                                    return false;
                                }

                                // Expand the following keys by default
                                const keepExpanded = ['choices'];
                                if (keepExpanded.includes(String(keyPath[0]))) {
                                    return true;
                                }

                                // Collapse at specified level by default.
                                // By only returning false for the specified level, we can collapse
                                // all nodes at that level but still expand the rest, including their
                                // children so that they are easy to view after expanding the parent.
                                if (level === 3) {
                                    return false;
                                }

                                // Expand all other nodes by default.
                                return true;
                            }}
                            theme={{
                                base00: '#000000',
                                base01: '#303030',
                                base02: '#505050',
                                base03: '#b0b0b0',
                                base04: '#d0d0d0',
                                base05: '#e0e0e0',
                                base06: '#f5f5f5',
                                base07: '#ffffff',
                                base08: '#fb0120',
                                base09: '#fc6d24',
                                base0A: '#fda331',
                                base0B: '#a1c659',
                                base0C: '#76c7b7',
                                base0D: '#6fb3d2',
                                base0E: '#d381c3',
                                base0F: '#be643c',
                            }}
                        />
                    </div>
                )
            }
        />
    );
};

// Helper function to determine if a node path should be kept collapsed
const shouldKeepNodeCollapsed = (keyPath: KeyPath, keepCollapsed: string[][]) => {
    // Filter out numeric indices to only work with string keys
    const stringPath = keyPath.filter((key) => typeof key === 'string') as string[];

    for (const collapsePath of keepCollapsed) {
        if (collapsePath.length === 1) {
            // Single value case: collapse if this value appears anywhere
            if (stringPath.includes(collapsePath[0])) {
                return true;
            }
        } else if (collapsePath.length > 1) {
            // Multiple value case: items must appear in order (not necessarily adjacent)
            // First check if all items exist in the path
            const allExist = collapsePath.every((item) => stringPath.includes(item));

            if (allExist) {
                // Then check if they appear in the correct order
                let inOrder = true;
                for (let i = 0; i < collapsePath.length - 1; i++) {
                    const currentIndex = stringPath.indexOf(collapsePath[i]);
                    const nextIndex = stringPath.indexOf(collapsePath[i + 1]);

                    // The "next" item should appear later in the path (higher up in the tree)
                    if (currentIndex >= nextIndex || nextIndex === -1) {
                        inOrder = false;
                        break;
                    }
                }

                if (inOrder) {
                    return true;
                }
            }
        }
    }

    return false;
};


=== File: workbench-app/src/components/Conversations/FileItem.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Caption1,
    Card,
    CardHeader,
    DialogOpenChangeData,
    DialogOpenChangeEvent,
    makeStyles,
    Menu,
    MenuItem,
    MenuList,
    MenuPopover,
    MenuTrigger,
    Text,
} from '@fluentui/react-components';
import { ArrowDownloadRegular, DeleteRegular, MoreHorizontalRegular } from '@fluentui/react-icons';
import React from 'react';
import * as StreamSaver from 'streamsaver';
import { useWorkbenchService } from '../../libs/useWorkbenchService';
import { Utility } from '../../libs/Utility';
import { Conversation } from '../../models/Conversation';
import { ConversationFile } from '../../models/ConversationFile';
import { useDeleteConversationFileMutation } from '../../services/workbench';
import { DialogControl } from '../App/DialogControl';
import { TooltipWrapper } from '../App/TooltipWrapper';
import { ConversationFileIcon } from './ConversationFileIcon';

const useClasses = makeStyles({
    cardHeader: {
        '> .fui-CardHeader__header': {
            overflow: 'hidden',
        },
    },
    actions: {
        display: 'flex',
        flexDirection: 'row',
        gap: '8px',
    },
});

interface FileItemProps {
    conversation: Conversation;
    conversationFile: ConversationFile;
    readOnly?: boolean;
    onFileSelect?: (file: ConversationFile) => void;
}

export const FileItem: React.FC<FileItemProps> = (props) => {
    const { conversation, conversationFile, readOnly } = props;
    const classes = useClasses();
    const workbenchService = useWorkbenchService();
    const [deleteConversationFile] = useDeleteConversationFileMutation();
    const [submitted, setSubmitted] = React.useState(false);
    const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false);

    const time = React.useMemo(
        () => Utility.toFormattedDateString(conversationFile.updated, 'M/D/YYYY h:mm A'),
        [conversationFile.updated],
    );

    const sizeToDisplay = (size: number) => {
        if (size < 1024) {
            return `${size} B`;
        } else if (size < 1024 * 1024) {
            return `${(size / 1024).toFixed(1).toString().replaceAll('.0', '')} KB`;
        } else {
            return `${(size / 1024 / 1024).toFixed(1).toString().replaceAll('.0', '')} MB`;
        }
    };

    const tokenCountToDisplay = (count: number) => {
        const label = `token${count !== 1 ? 's' : ''}`;
        if (count < 1_000) {
            return `${count} ${label}`;
        } else if (count < 1_000_000) {
            return `${(count / 1_000).toFixed(1).toString().replaceAll('.0', '')}k ${label}`;
        } else {
            return `${(count / 1_000_000).toFixed(1).toString().replaceAll('.0', '')}m ${label}`;
        }
    };

    const handleDeleteMenuItemClick = React.useCallback(() => {
        if (deleteDialogOpen) {
            return;
        }
        setDeleteDialogOpen(true);
    }, [deleteDialogOpen]);

    const onDeleteDialogOpenChange = React.useCallback((_: DialogOpenChangeEvent, data: DialogOpenChangeData) => {
        setDeleteDialogOpen(data.open);
    }, []);

    const handleDelete = React.useCallback(async () => {
        if (submitted) {
            return;
        }
        setSubmitted(true);

        try {
            await deleteConversationFile({ conversationId: conversation.id, filename: conversationFile.name });
        } finally {
            setSubmitted(false);
        }
    }, [conversation.id, conversationFile.name, deleteConversationFile, submitted]);

    const handleDownload = React.useCallback(async () => {
        if (submitted) {
            return;
        }
        setSubmitted(true);

        try {
            const response: Response = await workbenchService.downloadConversationFileAsync(
                conversation.id,
                conversationFile,
            );

            if (!response.ok || !response.body) {
                throw new Error('Failed to fetch file');
            }

            // Create a file stream using StreamSaver
            const fileStream = StreamSaver.createWriteStream(conversationFile.name);

            const readableStream = response.body;

            // Check if the browser supports pipeTo (most modern browsers do)
            if (readableStream.pipeTo) {
                await readableStream.pipeTo(fileStream);
            } else {
                // Fallback for browsers that don't support pipeTo
                const reader = readableStream.getReader();
                const writer = fileStream.getWriter();

                const pump = () =>
                    reader.read().then(({ done, value }) => {
                        if (done) {
                            writer.close();
                            return;
                        }
                        writer.write(value).then(pump);
                    });

                await pump();
            }
        } finally {
            setSubmitted(false);
        }
    }, [conversation.id, conversationFile, workbenchService, submitted]);

    return (
        <>
            <Card key={conversationFile.name} size="small">
                <CardHeader
                    className={classes.cardHeader}
                    image={<ConversationFileIcon file={conversationFile} size={24} />}
                    header={
                        <TooltipWrapper content={conversationFile.name}>
                            <Text truncate wrap={false} weight="semibold">
                                {conversationFile.name}
                            </Text>
                        </TooltipWrapper>
                    }
                    description={
                        <Caption1 truncate wrap={false}>
                            {time}
                            <br />
                            {sizeToDisplay(conversationFile.size)}{' '}
                            {conversationFile.metadata?.token_count !== undefined
                                ? `| ${tokenCountToDisplay(conversationFile.metadata?.token_count)}`
                                : ''}
                        </Caption1>
                    }
                    action={
                        <div className={classes.actions}>
                            <Menu>
                                <MenuTrigger disableButtonEnhancement>
                                    <Button icon={<MoreHorizontalRegular />} />
                                </MenuTrigger>
                                <MenuPopover>
                                    <MenuList>
                                        <MenuItem
                                            icon={<ArrowDownloadRegular />}
                                            onClick={handleDownload}
                                            disabled={submitted}
                                        >
                                            Download
                                        </MenuItem>
                                        <MenuItem
                                            icon={<DeleteRegular />}
                                            onClick={handleDeleteMenuItemClick}
                                            disabled={submitted || readOnly}
                                        >
                                            Delete
                                        </MenuItem>
                                    </MenuList>
                                </MenuPopover>
                            </Menu>
                        </div>
                    }
                />
            </Card>
            <DialogControl
                open={deleteDialogOpen}
                onOpenChange={onDeleteDialogOpenChange}
                title="Delete file"
                content={
                    <p>
                        Are you sure you want to delete <strong>{conversationFile.name}</strong>?
                    </p>
                }
                closeLabel="Cancel"
                additionalActions={[
                    <Button appearance="primary" onClick={handleDelete} disabled={submitted} key="delete">
                        {submitted ? 'Deleting...' : 'Delete'}
                    </Button>,
                ]}
            />
        </>
    );
};


=== File: workbench-app/src/components/Conversations/FileList.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { Conversation } from '../../models/Conversation';
import { ConversationFile } from '../../models/ConversationFile';
import { FileItem } from './FileItem';

interface FileListProps {
    conversation: Conversation;
    conversationFiles: ConversationFile[];
    readOnly?: boolean;
}

export const FileList: React.FC<FileListProps> = (props) => {
    const { conversation, conversationFiles, readOnly } = props;

    if (conversationFiles.length === 0) {
        return 'No conversation files found';
    }

    return (
        <>
            {conversationFiles
                .toSorted((a, b) => a.name.localeCompare(b.name))
                .map((file) => (
                    <FileItem key={file.name} readOnly={readOnly} conversation={conversation} conversationFile={file} />
                ))}
        </>
    );
};


=== File: workbench-app/src/components/Conversations/InputAttachmentList.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Attachment, AttachmentList, AttachmentProps } from '@fluentui-copilot/react-attachments';
import { makeStyles } from '@fluentui/react-components';
import debug from 'debug';
import React from 'react';
import { Constants } from '../../Constants';
import { TooltipWrapper } from '../App/TooltipWrapper';
import { ConversationFileIcon } from './ConversationFileIcon';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
    },
    media: {
        maxWidth: '20px',
        maxHeight: '20px',
    },
});

const log = debug(Constants.debug.root).extend('InputAttachmentList');

interface InputAttachmentProps {
    attachments: File[];
    onDismissAttachment: (file: File) => void;
}

export const InputAttachmentList: React.FC<InputAttachmentProps> = (props) => {
    const { attachments, onDismissAttachment } = props;
    const classes = useClasses();

    const attachmentList: AttachmentProps[] = attachments.map((file) => ({
        id: file.name,
        media: <ConversationFileIcon file={file} className={classes.media} />,
        children: (
            <TooltipWrapper content={file.name}>
                <span>{file.name}</span>
            </TooltipWrapper>
        ),
    }));

    return (
        <AttachmentList
            maxVisibleAttachments={3}
            onAttachmentDismiss={(_event, data) => {
                const file = attachments.find((file) => file.name === data.id);
                if (file) {
                    log('Dismissing attachment', file.name);
                    onDismissAttachment(file);
                } else {
                    log('Attachment not found while dismissing', data.id);
                }
            }}
        >
            {attachmentList.map((attachment) => (
                <Attachment id={attachment.id} key={attachment.id} media={attachment.media}>
                    {attachment.children}
                </Attachment>
            ))}
        </AttachmentList>
    );
};


=== File: workbench-app/src/components/Conversations/InputOptionsControl.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Caption1, Dropdown, makeStyles, mergeClasses, Option, tokens } from '@fluentui/react-components';
import React from 'react';
import { ConversationParticipant } from '../../models/ConversationParticipant';

const useClasses = makeStyles({
    row: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        width: '100%',
        gap: tokens.spacingHorizontalS,
    },
    rowEnd: {
        justifyContent: 'end',
    },
    fullWidth: {
        width: '100%',
        maxWidth: '100%',
    },
    collapsible: {
        minWidth: 'initial',
    },
});

interface InputOptionsControlProps {
    disabled?: boolean;
    messageTypeValue: string;
    participants?: ConversationParticipant[];
    onDirectedAtChange: (participantId?: string) => void;
}

const directedAtDefaultKey = 'all';
const directedAtDefaultValue = 'All assistants';

export const InputOptionsControl: React.FC<InputOptionsControlProps> = (props) => {
    const { messageTypeValue, participants, onDirectedAtChange, disabled } = props;
    const classes = useClasses();
    const [directedAtId, setDirectedAtId] = React.useState<string>(directedAtDefaultKey);
    const [directedAtName, setDirectedAtName] = React.useState<string>(directedAtDefaultValue);

    const assistantParticipants =
        participants
            ?.filter((participant) => participant.role === 'assistant')
            .filter((participant) => participant.active)
            .toSorted((a, b) => a.name.localeCompare(b.name)) ?? [];

    const handleDirectedToChange = (participantId?: string, participantName?: string) => {
        setDirectedAtId(participantId ?? directedAtDefaultKey);
        setDirectedAtName(participantName ?? directedAtDefaultValue);

        onDirectedAtChange(participantId);
    };

    return (
        <div className={classes.row}>
            <div className={classes.row}>
                <Caption1>Mode: {messageTypeValue}</Caption1>
            </div>
            <div className={mergeClasses(classes.row, classes.rowEnd)}>
                <Caption1>Directed: </Caption1>
                <Dropdown
                    className={classes.collapsible}
                    disabled={disabled || assistantParticipants.length < 2 || messageTypeValue !== 'Command'}
                    placeholder="Select participant"
                    value={directedAtName}
                    selectedOptions={[directedAtId]}
                    onOptionSelect={(_event, data) => handleDirectedToChange(data.optionValue, data.optionText)}
                >
                    <Option key={directedAtDefaultKey} value={directedAtDefaultKey}>
                        {directedAtDefaultValue}
                    </Option>
                    {assistantParticipants.map((participant) => (
                        <Option key={participant.id} value={participant.id}>
                            {participant.name}
                        </Option>
                    ))}
                </Dropdown>
            </div>
        </div>
    );
};


=== File: workbench-app/src/components/Conversations/InteractHistory.tsx ===
// Copyright (c) Microsoft. All rights reserved.
import { CopilotChat, ResponseCount } from '@fluentui-copilot/react-copilot';
import { makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import dayjs from 'dayjs';
import timezone from 'dayjs/plugin/timezone';
import utc from 'dayjs/plugin/utc';
import React from 'react';
import { useLocation } from 'react-router-dom';
import AutoSizer from 'react-virtualized-auto-sizer';
import { Virtuoso, VirtuosoHandle } from 'react-virtuoso';
import { Constants } from '../../Constants';
import { Utility } from '../../libs/Utility';
import { useConversationUtility } from '../../libs/useConversationUtility';
import { Conversation } from '../../models/Conversation';
import { ConversationMessage } from '../../models/ConversationMessage';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { useUpdateConversationParticipantMutation } from '../../services/workbench';
import { MemoizedInteractMessage } from './Message/InteractMessage';
import { MemoizedToolResultMessage } from './Message/ToolResultMessage';
import { ParticipantStatus } from './ParticipantStatus';

dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.tz.guess();

const useClasses = makeStyles({
    root: {
        height: '100%',
    },
    loading: {
        ...shorthands.margin(tokens.spacingVerticalXXXL, 0),
    },
    virtuoso: {
        '::-webkit-scrollbar-thumb': {
            backgroundColor: tokens.colorNeutralStencil1Alpha,
        },
    },
    item: {
        lineHeight: tokens.lineHeightBase400,
        ...shorthands.padding(0, tokens.spacingHorizontalM),
    },
    counter: {
        ...shorthands.padding(tokens.spacingVerticalL, tokens.spacingHorizontalXXXL, 0),
    },
    status: {
        ...shorthands.padding(tokens.spacingVerticalL, tokens.spacingHorizontalXXXL, 0),
    },
});

interface InteractHistoryProps {
    conversation: Conversation;
    messages: ConversationMessage[];
    participants: ConversationParticipant[];
    readOnly: boolean;
    className?: string;
    onRewindToBefore?: (message: ConversationMessage, redo: boolean) => Promise<void>;
}

export const InteractHistory: React.FC<InteractHistoryProps> = (props) => {
    const { conversation, messages, participants, readOnly, className, onRewindToBefore } = props;
    const classes = useClasses();
    const { hash } = useLocation();
    const { debouncedSetLastRead } = useConversationUtility();
    const [scrollToIndex, setScrollToIndex] = React.useState<number>();
    const [items, setItems] = React.useState<React.ReactNode[]>([]);
    const [isAtBottom, setIsAtBottom] = React.useState<boolean>(true);
    const [updateParticipantState] = useUpdateConversationParticipantMutation();

    // handler for when a message is read
    const handleOnRead = React.useCallback(
        // update the last read timestamp for the conversation
        async (message: ConversationMessage) => debouncedSetLastRead(conversation, message.timestamp),
        [debouncedSetLastRead, conversation],
    );

    const timeoutRef = React.useRef<NodeJS.Timeout | null>(null);
    const debouncedUpdateViewingMessage = React.useCallback(
        (conversationId: string, messageTimestamp: string) => {
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
            }
            timeoutRef.current = setTimeout(
                () =>
                    updateParticipantState({
                        conversationId,
                        participantId: 'me',
                        metadata: {
                            viewing_message_timestamp: messageTimestamp,
                        },
                    })?.unwrap(),
                300,
            );
        },
        [updateParticipantState],
    );

    // handler for when a message is visible
    const handleOnVisible = React.useCallback(
        async (message: ConversationMessage) => {
            debouncedUpdateViewingMessage(conversation.id, message.timestamp);
        },
        [conversation.id, debouncedUpdateViewingMessage],
    );

    // create a ref for the virtuoso component for using its methods directly
    const virtuosoRef = React.useRef<VirtuosoHandle>(null);

    // set the scrollToIndex to the last item if the user is at the bottom of the history
    const triggerAutoScroll = React.useCallback(() => {
        if (isAtBottom) {
            setScrollToIndex(items.length - 1);
        }
    }, [isAtBottom, items.length]);

    // trigger auto scroll when the items change
    React.useEffect(() => {
        triggerAutoScroll();
    }, [items, triggerAutoScroll]);

    // scroll to the bottom of the history when the scrollToIndex changes
    React.useEffect(() => {
        if (!scrollToIndex) {
            return;
        }

        const index = scrollToIndex;
        setScrollToIndex(undefined);

        // wait a tick for the DOM to update
        setTimeout(() => virtuosoRef.current?.scrollToIndex({ index, align: 'start' }), 0);
    }, [scrollToIndex]);

    // create a list of memoized interact message components for rendering in the virtuoso component
    React.useEffect(() => {
        let lastMessageInfo = {
            participantId: '',
            attribution: undefined as string | undefined,
            time: undefined as dayjs.Dayjs | undefined,
        };
        let lastDate = '';
        let generatedResponseCount = 0;

        const updatedItems = messages
            .filter((message) => message.messageType !== 'log')
            .map((message, index) => {
                // if a hash is provided, check if the message id matches the hash
                if (hash === `#${message.id}`) {
                    // set the hash item index to scroll to the item
                    setScrollToIndex(index);
                }

                const senderParticipant = participants.find(
                    (participant) => participant.id === message.sender.participantId,
                );
                if (!senderParticipant) {
                    // if the sender participant is not found, do not render the message.
                    // this can happen temporarily if the provided conversation was just
                    // re-retrieved, but the participants have not been re-retrieved yet
                    return (
                        <div key={message.id} className={classes.item}>
                            Participant not found: {message.sender.participantId} in conversation {conversation.id}
                        </div>
                    );
                }

                const date = Utility.toFormattedDateString(message.timestamp, 'M/D/YY');
                let displayDate = false;
                if (date !== lastDate) {
                    displayDate = true;
                    lastDate = date;
                }

                if (
                    message.messageType === 'chat' &&
                    message.sender.participantRole !== 'user' &&
                    message.metadata?.generated_content !== false
                ) {
                    generatedResponseCount += 1;
                }

                // avoid duplicate header for messages from the same participant, if the
                // attribution is the same and the message is within a minute of the last
                let hideParticipant = message.messageType !== 'chat';
                const messageTime = dayjs.utc(message.timestamp);
                if (
                    lastMessageInfo.participantId === senderParticipant.id &&
                    lastMessageInfo.attribution === message.metadata?.attribution &&
                    messageTime.diff(lastMessageInfo.time, 'minute') < 1
                ) {
                    hideParticipant = true;
                }
                lastMessageInfo = {
                    participantId: senderParticipant.id,
                    attribution: message.metadata?.attribution,
                    time: messageTime,
                };

                // FIXME: add new message type in workbench service/app for tool results
                const isToolResult = message.messageType === 'note' && message.metadata?.['tool_result'];

                // Use memoized message components to prevent re-rendering all messages when one changes
                const messageContent = isToolResult ? (
                    <MemoizedToolResultMessage conversation={conversation} message={message} readOnly={readOnly} />
                ) : (
                    <MemoizedInteractMessage
                        readOnly={readOnly}
                        conversation={conversation}
                        message={message}
                        participant={senderParticipant}
                        hideParticipant={hideParticipant}
                        displayDate={displayDate}
                        onRead={handleOnRead}
                        onVisible={handleOnVisible}
                        onRewind={onRewindToBefore}
                    />
                );

                return (
                    <div className={classes.item} key={message.id}>
                        {messageContent}
                    </div>
                );
            });

        if (generatedResponseCount > 0) {
            updatedItems.push(
                <div className={classes.counter} key="response-count">
                    <ResponseCount status="success">
                        {generatedResponseCount} generated response{generatedResponseCount === 1 ? '' : 's'}
                    </ResponseCount>
                </div>,
            );
        }

        updatedItems.push(
            <div className={classes.status} key="participant-status">
                <ParticipantStatus participants={participants} onChange={() => triggerAutoScroll()} />
            </div>,
        );

        setItems(updatedItems);
    }, [
        messages,
        classes.status,
        classes.item,
        classes.counter,
        participants,
        hash,
        readOnly,
        conversation,
        handleOnRead,
        onRewindToBefore,
        isAtBottom,
        items.length,
        triggerAutoScroll,
        handleOnVisible,
    ]);

    // render the history
    return (
        <CopilotChat className={mergeClasses(classes.root, className)}>
            <AutoSizer>
                {({ height, width }: { height: number; width: number }) => (
                    <Virtuoso
                        ref={virtuosoRef}
                        style={{ height, width }}
                        className={classes.virtuoso}
                        data={items}
                        itemContent={(_index, item) => item}
                        initialTopMostItemIndex={items.length}
                        atBottomThreshold={Constants.app.autoScrollThreshold}
                        atBottomStateChange={(isAtBottom) => setIsAtBottom(isAtBottom)}
                    />
                )}
            </AutoSizer>
        </CopilotChat>
    );
};


=== File: workbench-app/src/components/Conversations/InteractInput.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import {
    $createTextNode,
    $getRoot,
    ChatInput,
    ChatInputEntityNode,
    ChatInputSubmitEvents,
    ChatInputTokenNode,
    EditorInputValueData,
    EditorState,
    LexicalEditor,
    LexicalEditorRefPlugin,
    TextNode,
} from '@fluentui-copilot/react-copilot';
import { Button, makeStyles, mergeClasses, shorthands, Title3, tokens } from '@fluentui/react-components';
import { Attach20Regular } from '@fluentui/react-icons';
import debug from 'debug';
import { getEncoding } from 'js-tiktoken';
import {
    $createLineBreakNode,
    CLEAR_EDITOR_COMMAND,
    COMMAND_PRIORITY_LOW,
    LineBreakNode,
    PASTE_COMMAND,
    SerializedTextNode,
} from 'lexical';
import React from 'react';
import { Constants } from '../../Constants';
import useDragAndDrop from '../../libs/useDragAndDrop';
import { useNotify } from '../../libs/useNotify';
import { AssistantCapability } from '../../models/AssistantCapability';
import { Conversation } from '../../models/Conversation';
import { ConversationMessage } from '../../models/ConversationMessage';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { useAppDispatch, useAppSelector } from '../../redux/app/hooks';
import {
    updateGetConversationMessagesQueryData,
    useCreateConversationMessageMutation,
    useUploadConversationFilesMutation,
} from '../../services/workbench';
import { ClearEditorPlugin } from './ChatInputPlugins/ClearEditorPlugin';
import { ParticipantMentionsPlugin } from './ChatInputPlugins/ParticipantMentionsPlugin';
import { InputAttachmentList } from './InputAttachmentList';
import { InputOptionsControl } from './InputOptionsControl';
import { SpeechButton } from './SpeechButton';

const log = debug(Constants.debug.root).extend('InteractInput');

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        width: '100%',
        gap: tokens.spacingVerticalS,
        ...shorthands.padding(tokens.spacingVerticalM),
    },
    readOnly: {
        pointerEvents: 'none',
        opacity: 0.5,
    },
    content: {
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'stretch',
        width: '100%',
        maxWidth: `${Constants.app.maxContentWidth}px`,
        gap: tokens.spacingVerticalS,

        // ...shorthands.padding(0, tokens.spacingHorizontalXXL, 0, tokens.spacingHorizontalM),
        boxSizing: 'border-box',
    },
    row: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        width: '100%',
        gap: tokens.spacingHorizontalS,
    },
    rowEnd: {
        justifyContent: 'end',
    },
    fullWidth: {
        width: '100%',
        maxWidth: '100%',
    },
    commandTextbox: {
        '& [role=textbox]': {
            fontFamily: 'monospace',
        },
    },
    dragTarget: {
        transition: 'border 0.3s',
        border: `2px dashed transparent`,
    },
    dragOverBody: {
        border: `2px dashed ${tokens.colorPaletteBlueBorderActive}`,
        borderRadius: tokens.borderRadiusLarge,
    },
    dragOverTarget: {
        cursor: 'copy',
        border: `2px dashed ${tokens.colorPaletteGreenBorderActive}`,
        borderRadius: tokens.borderRadiusLarge,
    },
});

interface InteractInputProps {
    conversation: Conversation;
    messages: ConversationMessage[];
    participants: ConversationParticipant[];
    additionalContent?: React.ReactNode;
    readOnly: boolean;
    assistantCapabilities: Set<AssistantCapability>;
}

interface SerializedTemporaryTextNode extends SerializedTextNode {}

class TemporaryTextNode extends TextNode {
    static getType() {
        return 'temporary';
    }

    static clone(node: TemporaryTextNode) {
        return new TemporaryTextNode(node.__text, node.__key);
    }

    static importJSON(serializedNode: SerializedTextNode): TextNode {
        return super.importJSON(serializedNode) as TemporaryTextNode;
    }

    exportJSON(): SerializedTextNode {
        return super.exportJSON() as SerializedTemporaryTextNode;
    }
}

export const InteractInput: React.FC<InteractInputProps> = (props) => {
    const { conversation, messages, participants, additionalContent, readOnly, assistantCapabilities } = props;
    const classes = useClasses();
    const dropTargetRef = React.useRef<HTMLDivElement>(null);
    const localUserId = useAppSelector((state) => state.localUser.id);
    const isDraggingOverBody = useAppSelector((state) => state.app.isDraggingOverBody);
    const isDraggingOverTarget = useDragAndDrop(dropTargetRef.current, log);
    const [createMessage] = useCreateConversationMessageMutation();
    const [uploadConversationFiles] = useUploadConversationFilesMutation();
    const [messageTypeValue, setMessageTypeValue] = React.useState<'Chat' | 'Command'>('Chat');
    const [tokenCount, setTokenCount] = React.useState(0);
    const [directedAtId, setDirectedAtId] = React.useState<string>();
    const [attachmentFiles, setAttachmentFiles] = React.useState<Map<string, File>>(new Map());
    const [isSubmitting, setIsSubmitting] = React.useState(false);
    const [isListening, setIsListening] = React.useState(false);
    const [editorIsInitialized, setEditorIsInitialized] = React.useState(false);
    const editorRef = React.useRef<LexicalEditor | null>();
    const attachmentInputRef = React.useRef<HTMLInputElement>(null);
    const { notifyWarning } = useNotify();
    const dispatch = useAppDispatch();

    const editorRefCallback = React.useCallback((editor: LexicalEditor) => {
        editorRef.current = editor;

        // set the editor as initialized
        setEditorIsInitialized(true);
    }, []);

    // add a set of attachments to the list of attachments
    const addAttachments = React.useCallback(
        (files: Iterable<File>) => {
            setAttachmentFiles((prevFiles) => {
                const updatedFiles = new Map(prevFiles);
                const duplicates = new Map<string, number>();

                for (const file of files) {
                    // limit the number of attachments to the maximum allowed
                    if (updatedFiles.size >= Constants.app.maxFileAttachmentsPerMessage) {
                        notifyWarning({
                            id: 'attachment-limit-reached',
                            title: 'Attachment limit reached',
                            message: `Only ${Constants.app.maxFileAttachmentsPerMessage} files can be attached per message`,
                        });
                        return updatedFiles;
                    }

                    if (updatedFiles.has(file.name)) {
                        duplicates.set(file.name, (duplicates.get(file.name) || 0) + 1);
                        continue;
                    }

                    updatedFiles.set(file.name, file);
                }

                for (const [filename, count] of duplicates.entries()) {
                    notifyWarning({
                        id: `duplicate-attachment-${filename}`,
                        title: `Attachment with duplicate filename`,
                        message: `Attachment with filename '${filename}' ${count !== 1 ? 'was' : 'were'} ignored`,
                    });
                }
                return updatedFiles;
            });
        },
        [notifyWarning],
    );

    React.useEffect(() => {
        if (!editorIsInitialized) return;

        if (!editorRef.current) {
            console.error('Failed to get editor reference after initialization');
            return;
        }
        const editor = editorRef.current;

        const removePasteListener = editor.registerCommand(
            PASTE_COMMAND,
            (event: ClipboardEvent) => {
                log('paste event', event);

                const clipboardItems = event.clipboardData?.items;
                if (!clipboardItems) return false;

                for (const item of clipboardItems) {
                    if (item.kind !== 'file') continue;
                    const file = item.getAsFile();
                    if (!file) continue;
                    // ensure the filename is unique by appending a timestamp before the extension
                    const timestamp = new Date().getTime();
                    const filename = `${file.name.replace(/\.[^/.]+$/, '')}_${timestamp}${file.name.match(
                        /\.[^/.]+$/,
                    )}`;

                    // file.name is read-only, so create a new file object with the new name
                    // make sure to use the same file contents, content type, etc.
                    const updatedFile = filename !== file.name ? new File([file], filename, { type: file.type }) : file;

                    // add the file to the list of attachments
                    log('calling add attachment from paste', file);
                    addAttachments([updatedFile]);

                    // Prevent default paste for file items
                    event.preventDefault();
                    event.stopPropagation();

                    // Indicate command was handled
                    return true;
                }

                // Allow default handling for non-file paste
                return false;
            },
            COMMAND_PRIORITY_LOW,
        );

        return () => {
            // Clean up listeners on unmount
            removePasteListener();
        };
    }, [editorIsInitialized, addAttachments]);

    const tokenizer = React.useMemo(() => getEncoding('cl100k_base'), []);

    const onAttachmentChanged = React.useCallback(() => {
        if (!attachmentInputRef.current) {
            return;
        }
        addAttachments(attachmentInputRef.current.files ?? []);
        attachmentInputRef.current.value = '';
    }, [addAttachments]);

    const handleDrop = React.useCallback(
        (event: React.DragEvent) => {
            addAttachments(event.dataTransfer.files);
        },
        [addAttachments],
    );

    const handleSend = (_event: ChatInputSubmitEvents, data: EditorInputValueData) => {
        if (data.value.trim() === '' || isSubmitting) {
            return;
        }

        (async () => {
            if (!localUserId) {
                throw new Error('Local user ID is not set');
            }

            setIsSubmitting(true);
            const content = data.value.trim();
            const metadata: Record<string, any> = directedAtId ? { directed_at: directedAtId } : {};

            const messageType = messageTypeValue.toLowerCase() as 'chat' | 'command';

            const mentions: string[] = [];
            const nodes = editorRef.current?.getEditorState()._nodeMap;
            if (nodes) {
                for (const node of nodes.values()) {
                    if (node.__type !== 'entity') continue;
                    try {
                        const nodeData = (node as any).__data as { type: string; participant: ConversationParticipant };
                        if (nodeData.type === 'mention') {
                            mentions.push(nodeData.participant.id);
                        }
                    } catch (error) {
                        // ignore, not a mention
                    }
                }
            }

            if (mentions.length > 0) {
                metadata.mentions = mentions;
            }

            // optimistically update the UI
            // this will be replaced by the actual message when the mutation completes
            // need to define the extra fields for the message such as sender, timestamp, etc.
            // so that the message can be rendered correctly
            dispatch(
                updateGetConversationMessagesQueryData({ conversationId: conversation.id }, [
                    ...(messages ?? []),
                    {
                        id: 'optimistic',
                        sender: {
                            participantId: localUserId,
                            participantRole: 'user',
                        },
                        timestamp: new Date().toISOString(),
                        messageType,
                        content,
                        contentType: 'text/plain',
                        filenames: [],
                        metadata,
                        hasDebugData: false,
                    },
                ]),
            );

            editorRef.current?.dispatchCommand(CLEAR_EDITOR_COMMAND, undefined);

            // upload attachments
            const filenames = attachmentFiles.size > 0 ? [...attachmentFiles.keys()] : undefined;
            const files = attachmentFiles.size > 0 ? [...attachmentFiles.values()] : undefined;
            // reset the attachment files so that the same files are not uploaded again
            setAttachmentFiles(new Map());
            // reset the files form input
            if (attachmentInputRef.current) {
                attachmentInputRef.current.value = '';
            }
            if (files) {
                await uploadConversationFiles({ conversationId: conversation.id, files });
            }

            // create the message
            await createMessage({
                conversationId: conversation.id,
                content,
                messageType,
                filenames,
                metadata,
            });

            // reset for the next message
            setMessageTypeValue('Chat');

            setIsSubmitting(false);
        })();
    };

    const updateInput = (newInput: string) => {
        const newMessageType = newInput.startsWith('/') ? 'Command' : 'Chat';
        if (newMessageType !== messageTypeValue) {
            setMessageTypeValue(newMessageType);
        }

        const tokens = tokenizer.encode(newInput);
        setTokenCount(tokens.length);
    };

    const onAttachment = () => {
        attachmentInputRef.current?.click();
    };

    // update the listening state when the speech recognizer starts or stops
    // so that we can disable the input send while listening
    const handleListeningChange = (listening: boolean) => {
        setIsListening(listening);
    };

    // update the editor with the in-progress recognized text while the speech recognizer is recognizing,
    // which is not the final text yet, but it will give the user an idea of what is being recognized
    const handleSpeechRecognizing = (text: string) => {
        const editor = editorRef.current;
        if (!editor) {
            console.error('Failed to get editor reference');
            return;
        }

        editor.update(() => {
            // get the editor state
            const editorState: EditorState = editor.getEditorState();

            // check if there is a temporary text node in the editor
            // if found, update the text content of the temporary text node
            let foundTemporaryNode = false;
            editorState._nodeMap.forEach((node) => {
                if (node instanceof TemporaryTextNode) {
                    node.setTextContent(text);
                    foundTemporaryNode = true;
                }
            });

            // get the root node of the editor
            const root = $getRoot();

            // if no temporary text node was found, insert a new temporary text node at the end of the editor
            if (!foundTemporaryNode) {
                const selection = root.selectEnd();
                if (!selection) {
                    console.error('Failed to get selection');
                    return;
                }

                // insert a line break before the temporary text node if the editor is not empty
                if (root.getTextContentSize() > 0) {
                    selection.insertNodes([$createLineBreakNode()]);
                }

                // insert the temporary text node at the end of the editor
                selection.insertNodes([new TemporaryTextNode(text)]);
            }

            // select the end of the editor to ensure the temporary text node is visible
            root.selectEnd();
        });
    };

    // update the editor with the final recognized text when the speech recognizer has recognized the speech
    // this will replace the in-progress recognized text in the editor
    const handleSpeechRecognized = (text: string) => {
        const editor = editorRef.current;
        if (!editor) {
            console.error('Failed to get editor reference');
            return;
        }

        editor.update(() => {
            // get the editor state
            const editorState: EditorState = editor.getEditorState();

            // remove any temporary text nodes from the editor
            editorState._nodeMap.forEach((node) => {
                if (node instanceof TemporaryTextNode) {
                    node.remove();
                }
            });

            // get the root node of the editor
            const root = $getRoot();

            // insert the recognized text as a text node at the end of the editor
            const selection = root.selectEnd();
            if (!selection) {
                console.error('Failed to get selection');
                return;
            }
            selection.insertNodes([$createTextNode(text)]);

            // select the end of the editor to ensure the text node is visible
            root.selectEnd();
        });
    };

    const disableSend = readOnly || isSubmitting || tokenCount === 0;
    const disableInputs = readOnly || isSubmitting || isListening;
    const disableAttachments =
        readOnly || isSubmitting || !assistantCapabilities.has(AssistantCapability.SupportsConversationFiles);

    const tokenCounts = `${tokenCount} token${tokenCount !== 1 ? 's' : ''}`;
    const attachmentCount = disableAttachments
        ? ''
        : `${attachmentFiles.size} attachments (max ${Constants.app.maxFileAttachmentsPerMessage})`;
    const inputCounts = [tokenCounts, attachmentCount].filter((count) => count !== '').join(' | ');
    const attachFilesButtonTitle = disableAttachments
        ? 'Attachments are not supported by the assistants in this conversation'
        : 'Attach files';

    return (
        <div className={classes.root}>
            {readOnly ? (
                <div className={classes.readOnly}>
                    <Title3>You are currently observing this conversation.</Title3>
                </div>
            ) : (
                <div className={classes.content}>
                    {/* this is for injecting controls for other features */}
                    {additionalContent}
                    <InputOptionsControl
                        disabled={readOnly}
                        messageTypeValue={messageTypeValue}
                        participants={participants}
                        onDirectedAtChange={setDirectedAtId}
                    />
                    <div
                        ref={dropTargetRef}
                        onDrop={handleDrop}
                        className={mergeClasses(
                            classes.row,
                            classes.dragTarget,
                            isDraggingOverTarget
                                ? classes.dragOverTarget
                                : isDraggingOverBody
                                ? classes.dragOverBody
                                : '',
                        )}
                    >
                        <ChatInput
                            className={mergeClasses(
                                classes.fullWidth,
                                messageTypeValue === 'Command' ? classes.commandTextbox : '',
                            )}
                            onChange={(_event, data) => updateInput(data.value)}
                            maxLength={Constants.app.maxInputLength}
                            characterCount={tokenCount}
                            charactersRemainingMessage={(charactersRemaining) =>
                                `${charactersRemaining} characters remaining`
                            }
                            count={<span>{inputCounts}</span>}
                            disabled={readOnly}
                            placeholderValue="Ask a question or request assistance or type / to enter a command."
                            customNodes={[ChatInputTokenNode, ChatInputEntityNode, LineBreakNode, TemporaryTextNode]}
                            disableSend={disableSend}
                            onSubmit={handleSend}
                            trimWhiteSpace
                            showCount
                            actions={
                                <span style={{ display: 'flex', alignItems: 'center' }}>
                                    <span>
                                        <input
                                            hidden
                                            ref={attachmentInputRef}
                                            type="file"
                                            onChange={onAttachmentChanged}
                                            multiple
                                        />
                                        <Button
                                            appearance="transparent"
                                            title={attachFilesButtonTitle}
                                            disabled={disableAttachments}
                                            icon={<Attach20Regular />}
                                            onClick={onAttachment}
                                        />
                                        <SpeechButton
                                            disabled={disableInputs}
                                            onListeningChange={handleListeningChange}
                                            onSpeechRecognizing={handleSpeechRecognizing}
                                            onSpeechRecognized={handleSpeechRecognized}
                                        />
                                    </span>
                                </span>
                            }
                            attachments={
                                <InputAttachmentList
                                    attachments={[...attachmentFiles.values()]}
                                    onDismissAttachment={(dismissedFile) =>
                                        setAttachmentFiles((prevFiles) => {
                                            const updatedFiles = new Map(prevFiles);
                                            updatedFiles.delete(dismissedFile.name);
                                            return updatedFiles;
                                        })
                                    }
                                />
                            }
                        >
                            <ClearEditorPlugin />
                            {participants && (
                                <ParticipantMentionsPlugin
                                    participants={participants.filter((participant) => participant.id !== localUserId)}
                                    parent={document.getElementById('app')}
                                />
                            )}
                            <LexicalEditorRefPlugin editorRef={editorRefCallback} />
                        </ChatInput>
                    </div>
                </div>
            )}
        </div>
    );
};


=== File: workbench-app/src/components/Conversations/Message/AttachmentSection.tsx ===
import { Attachment, AttachmentList } from '@fluentui-copilot/react-copilot';
import { makeStyles, mergeClasses, tokens } from '@fluentui/react-components';
import React from 'react';
import { TooltipWrapper } from '../../App/TooltipWrapper';
import { ConversationFileIcon } from '../ConversationFileIcon';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalS,
    },
});

interface AttachmentSectionProps {
    filenames?: string[];
    className?: string;
}

export const AttachmentSection: React.FC<AttachmentSectionProps> = (props) => {
    const { filenames, className } = props;
    const classes = useClasses();

    const attachmentList =
        filenames && filenames.length > 0 ? (
            <AttachmentList>
                {filenames.map((filename) => (
                    <TooltipWrapper content={filename} key={filename}>
                        <Attachment media={<ConversationFileIcon file={filename} />} content={filename} />
                    </TooltipWrapper>
                ))}
            </AttachmentList>
        ) : null;

    return <div className={mergeClasses(classes.root, className)}>{attachmentList}</div>;
};


=== File: workbench-app/src/components/Conversations/Message/ContentRenderer.tsx ===
import { SystemMessage } from '@fluentui-copilot/react-copilot';
import {
    AlertUrgent24Regular,
    KeyCommandRegular,
    Note24Regular,
    TextBulletListSquareSparkleRegular,
} from '@fluentui/react-icons';
import React from 'react';
import { Conversation } from '../../../models/Conversation';
import { ConversationMessage } from '../../../models/ConversationMessage';
import { AssistantCard } from '../../FrontDoor/Controls/AssistantCard';
import { MessageContent } from './MessageContent';

interface ContentRendererProps {
    conversation: Conversation;
    message: ConversationMessage;
}

export const ContentRenderer: React.FC<ContentRendererProps> = (props) => {
    const { conversation, message } = props;

    const appComponent = message.metadata?._appComponent;
    if (appComponent) {
        switch (appComponent.type) {
            case 'AssistantCard':
                return (
                    <AssistantCard
                        assistantServiceId={appComponent.props.assistantServiceId}
                        templateId={appComponent.props.templateId}
                        existingConversationId={appComponent.props.existingConversationId}
                        participantMetadata={appComponent.props.participantMetadata}
                        hideContent
                    />
                );
            default:
                return null;
        }
    }

    const messageContent = <MessageContent message={message} conversation={conversation} />;

    const renderedContent =
        message.messageType === 'notice' ||
        message.messageType === 'note' ||
        message.messageType === 'command' ||
        message.messageType === 'command-response' ? (
            <NoticeRenderer content={messageContent} messageType={message.messageType} />
        ) : (
            messageContent
        );

    return renderedContent;
};

interface MessageRendererProps {
    content: JSX.Element;
    messageType: string;
}

const NoticeRenderer: React.FC<MessageRendererProps> = (props) => {
    const { content, messageType } = props;

    let icon = null;
    switch (messageType) {
        case 'notice':
            icon = <AlertUrgent24Regular />;
            break;
        case 'note':
            icon = <Note24Regular />;
            break;
        case 'command':
            icon = <KeyCommandRegular />;
            break;
        case 'command-response':
            icon = <TextBulletListSquareSparkleRegular />;
            break;
        default:
            break;
    }

    return (
        <SystemMessage icon={icon} message={content}>
            {content}
        </SystemMessage>
    );
};


=== File: workbench-app/src/components/Conversations/Message/ContentSafetyNotice.tsx ===
import { makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';

const useClasses = makeStyles({
    root: {
        width: 'fit-content',
        fontSize: tokens.fontSizeBase200,
        flexDirection: 'row',
        gap: tokens.spacingHorizontalS,
        alignItems: 'center',
        color: tokens.colorPaletteRedForeground1,
        ...shorthands.padding(tokens.spacingVerticalXS, tokens.spacingHorizontalS),
    },
});

interface ContentSafetyNoticeProps {
    contentSafety?: { result: string; note?: string };
}

export const ContentSafetyNotice: React.FC<ContentSafetyNoticeProps> = (props) => {
    const { contentSafety } = props;
    const classes = useClasses();

    if (!contentSafety || !contentSafety.result || contentSafety.result === 'pass') return null;

    const messageNote = `[Content Safety: ${contentSafety.result}] ${
        contentSafety.note || 'this message has been flagged as potentially unsafe'
    }`;

    return <div className={classes.root}>{messageNote}</div>;
};


=== File: workbench-app/src/components/Conversations/Message/InteractMessage.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { MessageBase } from './MessageBase';

import { CopilotMessageV2, Timestamp, UserMessageV2 } from '@fluentui-copilot/react-copilot';
import { Divider, makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';

import { useConversationUtility } from '../../../libs/useConversationUtility';
import { Utility } from '../../../libs/Utility';
import { Conversation } from '../../../models/Conversation';
import { ConversationMessage } from '../../../models/ConversationMessage';
import { ConversationParticipant } from '../../../models/ConversationParticipant';

import { ParticipantAvatar } from '../ParticipantAvatar';
import { ToolCalls } from '../ToolCalls';
import { MessageActions } from './MessageActions';
import { MessageBody } from './MessageBody';
import { MessageFooter } from './MessageFooter';
import { MessageHeader } from './MessageHeader';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
        width: '100%',
        boxSizing: 'border-box',
        paddingTop: tokens.spacingVerticalXXXL,

        '&.no-header': {
            paddingTop: 0,
        },
    },
    alignForUser: {
        justifyContent: 'flex-end',
        alignItems: 'flex-end',
    },
    hideParticipant: {
        paddingLeft: tokens.spacingHorizontalXXL,

        '> .fai-CopilotMessage__avatar': {
            display: 'none',
        },

        '> .fai-CopilotMessage__name': {
            display: 'none',
        },

        '> .fai-CopilotMessage__disclaimer': {
            display: 'none',
        },
    },
    header: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        ...shorthands.margin(tokens.spacingVerticalM, 0, tokens.spacingVerticalXS, 0),
        ...shorthands.padding(0, 0, 0, tokens.spacingHorizontalS),
        gap: tokens.spacingHorizontalS,
    },
    note: {
        boxSizing: 'border-box',
        paddingLeft: tokens.spacingHorizontalXXXL,
    },
    user: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalS,
        alignItems: 'flex-end',
    },
    userContent: {
        ...shorthands.padding(0, 0, 0, tokens.spacingHorizontalXXXL),
    },
    assistantContent: {
        gridTemplateColumns: 'max-content max-content 1fr',
        rowGap: 0,
        maxWidth: 'unset',

        '> .fai-CopilotMessage__content': {
            width: '100%',
            ...shorthands.margin(tokens.spacingVerticalM, 0),
        },
    },
});

interface InteractMessageProps {
    conversation: Conversation;
    message: ConversationMessage;
    participant: ConversationParticipant;
    hideParticipant?: boolean;
    displayDate?: boolean;
    readOnly: boolean;
    onRead?: (message: ConversationMessage) => void;
    onVisible?: (message: ConversationMessage) => void;
    onRewind?: (message: ConversationMessage, redo: boolean) => void;
}

export const InteractMessage: React.FC<InteractMessageProps> = (props) => {
    const { conversation, message, participant, hideParticipant, displayDate, readOnly, onRead, onVisible, onRewind } =
        props;
    const classes = useClasses();
    const { isMessageVisible, isMessageVisibleRef, isUnread } = useConversationUtility();

    const isUser = participant.role === 'user';
    const date = Utility.toFormattedDateString(message.timestamp, 'dddd, MMMM D');

    React.useEffect(() => {
        if (isMessageVisible) {
            onVisible?.(message);

            // Check if the message is visible and unread. If so, trigger the onRead handler to mark it read.
            // If the message is visible, mark it as read by invoking the onRead handler.
            if (isUnread(conversation, message.timestamp)) {
                onRead?.(message);
            }
        }
    }, [isMessageVisible, isUnread, message.timestamp, onRead, onVisible, conversation, message]);

    const header = hideParticipant ? null : (
        <MessageHeader
            message={message}
            participant={participant}
            className={mergeClasses(classes.header, isUser ? classes.alignForUser : undefined)}
        />
    );

    const actions = (
        <MessageActions
            readOnly={readOnly}
            message={message}
            conversation={conversation}
            onRewind={isUser ? onRewind : undefined}
        />
    );

    const body = <MessageBody message={message} conversation={conversation} />;

    const footer = (
        <div ref={isMessageVisibleRef}>
            <MessageFooter message={message} />
        </div>
    );

    const composedMessage =
        participant.role === 'assistant' ? (
            <CopilotMessageV2
                className={mergeClasses(
                    classes.assistantContent,
                    hideParticipant ? classes.hideParticipant : undefined,
                )}
                avatar={<ParticipantAvatar hideName participant={participant} />}
                name={participant.name}
                actions={actions}
                footnote={footer}
            >
                {body}
                <ToolCalls message={message} />
            </CopilotMessageV2>
        ) : message.messageType === 'chat' ? (
            <div className={classes.user}>
                {header}
                <UserMessageV2 className={classes.userContent}>{body}</UserMessageV2>
                {actions}
                {footer}
            </div>
        ) : (
            <MessageBase className={classes.note} header={header} body={body} footer={footer} />
        );

    return (
        <div className={mergeClasses(classes.root, hideParticipant ? 'no-header' : undefined)}>
            {displayDate && (
                <Divider>
                    <Timestamp>{date}</Timestamp>
                </Divider>
            )}
            {composedMessage}
        </div>
    );
};

export const MemoizedInteractMessage = React.memo(InteractMessage);


=== File: workbench-app/src/components/Conversations/Message/MessageActions.tsx ===
import { makeStyles } from '@fluentui/react-components';
import React from 'react';
import { Conversation } from '../../../models/Conversation';
import { ConversationMessage } from '../../../models/ConversationMessage';
import { useGetConversationMessageDebugDataQuery } from '../../../services/workbench';
import { CopyButton } from '../../App/CopyButton';
import { DebugInspector } from '../DebugInspector';
import { MessageDelete } from '../MessageDelete';
import { MessageLink } from '../MessageLink';
import { RewindConversation } from '../RewindConversation';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'row',
        flexShrink: 1,
    },
});

interface MessageActionsProps {
    readOnly: boolean;
    message: ConversationMessage;
    conversation: Conversation;
    onRewind?: (message: ConversationMessage, redo: boolean) => void;
}

export const MessageActions: React.FC<MessageActionsProps> = (props) => {
    const { readOnly, message, conversation, onRewind } = props;

    const [skipDebugLoad, setSkipDebugLoad] = React.useState(true);
    const {
        data: debugData,
        isLoading: isLoadingDebugData,
        isUninitialized: isUninitializedDebugData,
    } = useGetConversationMessageDebugDataQuery(
        { conversationId: conversation.id, messageId: message.id },
        { skip: skipDebugLoad },
    );

    const classes = useClasses();

    return (
        <div className={classes.root}>
            {!readOnly && <MessageLink conversation={conversation} messageId={message.id} />}
            <DebugInspector
                debug={{
                    debug: message.hasDebugData ? debugData?.debugData || { loading: true } : null,
                    message: message,
                }}
                loading={isLoadingDebugData || isUninitializedDebugData}
                onOpen={() => {
                    setSkipDebugLoad(false);
                }}
            />
            <CopyButton data={message.content} tooltip="Copy message" size="small" appearance="transparent" />
            {!readOnly && (
                <>
                    <MessageDelete conversationId={conversation.id} message={message} />
                    {onRewind && <RewindConversation onRewind={(redo) => onRewind?.(message, redo)} />}
                </>
            )}
        </div>
    );
};


=== File: workbench-app/src/components/Conversations/Message/MessageBase.tsx ===
import { makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
    },
    actions: {
        display: 'flex',
        flexDirection: 'row',
        gap: '8px',
        ...shorthands.margin(0, tokens.spacingHorizontalS),
    },
    body: {
        marginTop: tokens.spacingVerticalXS,
    },
});

interface MessageBaseProps {
    className?: string;
    header: React.ReactNode;
    body: React.ReactNode;
    actions?: React.ReactNode;
    footer?: React.ReactNode;
}

export const MessageBase: React.FC<MessageBaseProps> = (props) => {
    const { className, header, body, actions, footer } = props;
    const classes = useClasses();

    return (
        <div className={mergeClasses(classes.root, className)}>
            {header}
            <div className={classes.body}>{body}</div>
            {actions && <div className={classes.actions}>{actions}</div>}
            {footer}
        </div>
    );
};


=== File: workbench-app/src/components/Conversations/Message/MessageBody.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { Link } from 'react-router-dom';

import { Conversation } from '../../../models/Conversation';
import { ConversationMessage } from '../../../models/ConversationMessage';

import { makeStyles, tokens } from '@fluentui/react-components';
import { ContentRenderer } from './ContentRenderer';
import { ContentSafetyNotice } from './ContentSafetyNotice';

interface InteractMessageProps {
    conversation: Conversation;
    message: ConversationMessage;
}

const useClasses = makeStyles({
    help: {
        backgroundColor: '#e3ecef',
        padding: tokens.spacingVerticalS,
        borderRadius: tokens.borderRadiusMedium,
        marginTop: tokens.spacingVerticalL,
        fontColor: '#707a7d',
        '& h3': {
            marginTop: 0,
            marginBottom: 0,
            fontSize: tokens.fontSizeBase200,
            fontWeight: tokens.fontWeightSemibold,
        },
        '& p': {
            marginTop: 0,
            marginBottom: 0,
            fontSize: tokens.fontSizeBase200,
            lineHeight: tokens.lineHeightBase300,
            fontStyle: 'italic',
        },
    },
});

export const MessageBody: React.FC<InteractMessageProps> = (props) => {
    const { conversation, message } = props;
    const classes = useClasses();
    const body = (
        <>
            <ContentSafetyNotice contentSafety={message.metadata?.['content_safety']} />
            <ContentRenderer conversation={conversation} message={message} />
            {message.metadata?.['help'] && (
                <div className={classes.help}>
                    <h3>Next step?</h3>
                    <p>{message.metadata['help']}</p>
                </div>
            )}
        </>
    );

    if (message.metadata?.href) {
        return <Link to={message.metadata.href}>{body}</Link>;
    }
    return body;
};


=== File: workbench-app/src/components/Conversations/Message/MessageContent.tsx ===
import React from 'react';

import { Conversation } from '../../../models/Conversation';
import { ConversationMessage } from '../../../models/ConversationMessage';
import { useCreateConversationMessageMutation } from '../../../services/workbench';
import { ContentRenderer } from '../ContentRenderers/ContentRenderer';

interface MessageContentProps {
    conversation: Conversation;
    message: ConversationMessage;
}

export const MessageContent: React.FC<MessageContentProps> = (props) => {
    const { conversation, message } = props;

    const [createConversationMessage] = useCreateConversationMessageMutation();

    const onSubmit = async (data: string) => {
        if (message.metadata?.command) {
            await createConversationMessage({
                conversationId: conversation.id,
                content: JSON.stringify({
                    command: message.metadata.command,
                    parameters: data,
                }),
                messageType: 'command',
            });
        }
    };

    return (
        <ContentRenderer
            content={message.content}
            contentType={message.contentType}
            metadata={message.metadata}
            onSubmit={onSubmit}
        />
    );
};


=== File: workbench-app/src/components/Conversations/Message/MessageFooter.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { AiGeneratedDisclaimer } from '@fluentui-copilot/react-copilot';
import { makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';

import { ConversationMessage } from '../../../models/ConversationMessage';

import { AttachmentSection } from './AttachmentSection';

const useClasses = makeStyles({
    alignForUser: {
        justifyContent: 'flex-end',
        alignItems: 'flex-end',
    },
    footer: {
        display: 'flex',
        color: tokens.colorNeutralForeground3,
        flexDirection: 'row',
        gap: tokens.spacingHorizontalS,
        alignItems: 'center',
    },
    generated: {
        width: 'fit-content',
        marginTop: tokens.spacingVerticalS,
    },
});

interface MessageFooterProps {
    message: ConversationMessage;
}

export const MessageFooter: React.FC<MessageFooterProps> = (props) => {
    const { message } = props;
    const classes = useClasses();

    const attachments = React.useMemo(() => {
        if (message.filenames && message.filenames.length > 0) {
            return <AttachmentSection filenames={message.filenames} className={classes.alignForUser} />;
        }
        return null;
    }, [message.filenames, classes.alignForUser]);

    const footerContent = React.useMemo(() => {
        if (message.metadata?.['footer_items']) {
            const footerItemsArray = Array.isArray(message.metadata['footer_items'])
                ? message.metadata['footer_items']
                : [message.metadata['footer_items']];
            return (
                <div className={classes.footer}>
                    {footerItemsArray.map((item) => (
                        <AiGeneratedDisclaimer key={item} className={classes.generated}>
                            {item}
                        </AiGeneratedDisclaimer>
                    ))}
                </div>
            );
        }
        return null;
    }, [message.metadata, classes.footer, classes.generated]);

    const footer = (
        <>
            {attachments}
            {footerContent}
        </>
    );

    return footer;
};


=== File: workbench-app/src/components/Conversations/Message/MessageHeader.tsx ===
import { Timestamp } from '@fluentui-copilot/react-copilot';
import { Text } from '@fluentui/react-components';
import React from 'react';
import { Utility } from '../../../libs/Utility';
import { ConversationMessage } from '../../../models/ConversationMessage';
import { ConversationParticipant } from '../../../models/ConversationParticipant';
import { ParticipantAvatar } from '../ParticipantAvatar';

interface HeaderProps {
    message: ConversationMessage;
    participant: ConversationParticipant;
    className?: string;
}

export const MessageHeader: React.FC<HeaderProps> = (props) => {
    const { message, participant, className } = props;

    const time = Utility.toFormattedDateString(message.timestamp, 'h:mm A');
    const attribution = message.metadata?.['attribution'];

    return (
        <div className={className}>
            <ParticipantAvatar participant={participant} />
            {attribution && <Text size={300}>[{attribution}]</Text>}
            <div>
                <Timestamp>{time}</Timestamp>
            </div>
        </div>
    );
};


=== File: workbench-app/src/components/Conversations/Message/ToolResultMessage.tsx ===
import {
    Accordion,
    AccordionHeader,
    AccordionItem,
    AccordionPanel,
    makeStyles,
    shorthands,
    Text,
    tokens,
} from '@fluentui/react-components';
import { Toolbox24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Conversation } from '../../../models/Conversation';
import { ConversationMessage } from '../../../models/ConversationMessage';
import { useGetConversationMessageDebugDataQuery } from '../../../services/workbench';
import { CodeLabel } from '../../App/CodeLabel';
import { CodeContentRenderer } from '../ContentRenderers/CodeContentRenderer';
import { DebugInspector } from '../DebugInspector';
import { MessageDelete } from '../MessageDelete';

const useClasses = makeStyles({
    root: {
        backgroundColor: tokens.colorNeutralBackground3,
        borderRadius: tokens.borderRadiusMedium,
        ...shorthands.border('none'),
        ...shorthands.margin(tokens.spacingVerticalM, 0, tokens.spacingVerticalM, tokens.spacingHorizontalXXXL),
    },
    header: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: tokens.spacingHorizontalS,
    },
    actions: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
    },
});

interface ToolResultMessageProps {
    conversation: Conversation;
    message: ConversationMessage;
    readOnly: boolean;
}

/**
 * Allows experimental support for displaying tool call results that are attached to a message
 * via the metadata property. To use this, the message must have a metadata property
 * with a 'tool_result' key, which is an object with a 'tool_call_id' key, and a 'tool_calls'
 * key, which is an array of tool calls, each with an 'id', 'name', and 'arguments' property.
 * The result of the tool call should be in the message content.
 *
 * [Read more about special metadata support in UX...](../../../docs/MESSAGE_METADATA.md)
 *
 * This component will display each tool call result in an accordion, with the tool name
 * as the header and the result as the content.
 */
export const ToolResultMessage: React.FC<ToolResultMessageProps> = (props) => {
    const { conversation, message, readOnly } = props;
    const classes = useClasses();

    const [skipDebugLoad, setSkipDebugLoad] = React.useState(true);
    const {
        data: debugData,
        isLoading: isLoadingDebugData,
        isUninitialized: isUninitializedDebugData,
    } = useGetConversationMessageDebugDataQuery(
        { conversationId: conversation.id, messageId: message.id },
        { skip: skipDebugLoad },
    );

    const toolCallId = message.metadata?.['tool_result']?.['tool_call_id'] as string;
    const toolCalls: { id: string; name: string }[] = message.metadata?.['tool_calls'];
    const toolName = toolCalls?.find((toolCall) => toolCall.id === toolCallId)?.name;

    const messageContent = React.useMemo(
        () => <CodeContentRenderer content={message.content} language="bash" />,
        [message],
    );

    return (
        <div className={classes.root}>
            <Accordion collapsible>
                <AccordionItem value="1">
                    <AccordionHeader icon={<Toolbox24Regular />}>
                        <div className={classes.header}>
                            <Text>Received tool result </Text>
                            <CodeLabel>{toolName}</CodeLabel>
                        </div>
                    </AccordionHeader>
                    <AccordionPanel>{messageContent}</AccordionPanel>
                </AccordionItem>
            </Accordion>
            <div className={classes.actions}>
                <DebugInspector
                    debug={{
                        debug: message.hasDebugData ? debugData?.debugData || { loading: true } : null,
                        message: message,
                    }}
                    loading={isLoadingDebugData || isUninitializedDebugData}
                    onOpen={() => {
                        setSkipDebugLoad(false);
                    }}
                />
                {!readOnly && (
                    <>
                        <MessageDelete conversationId={conversation.id} message={message} />
                    </>
                )}
            </div>
        </div>
    );
};

export const MemoizedToolResultMessage = React.memo(ToolResultMessage);


=== File: workbench-app/src/components/Conversations/MessageDelete.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogTrigger } from '@fluentui/react-components';
import { Delete16Regular, Delete24Regular } from '@fluentui/react-icons';
import React from 'react';
import { ConversationMessage } from '../../models/ConversationMessage';
import { useDeleteConversationMessageMutation } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';

interface MessageDeleteProps {
    conversationId: string;
    message: ConversationMessage;
    onDelete?: (message: ConversationMessage) => void;
    disabled?: boolean;
}

export const MessageDelete: React.FC<MessageDeleteProps> = (props) => {
    const { conversationId, message, onDelete, disabled } = props;
    const [deleteMessage] = useDeleteConversationMessageMutation();
    const [submitted, setSubmitted] = React.useState(false);

    const handleDelete = React.useCallback(async () => {
        if (submitted) {
            return;
        }
        setSubmitted(true);

        try {
            await deleteMessage({ conversationId, messageId: message.id });

            onDelete?.(message);
        } finally {
            setSubmitted(false);
        }
    }, [conversationId, deleteMessage, message, onDelete, submitted]);

    return (
        <CommandButton
            description="Delete message"
            icon={<Delete24Regular />}
            iconOnly={true}
            disabled={disabled}
            dialogContent={{
                trigger: <Button appearance="subtle" icon={<Delete16Regular />} size="small" />,
                title: 'Delete Message',
                content: (
                    <>
                        <p>Are you sure you want to delete this message? This action cannot be undone.</p>
                        <p>
                            <em>
                                NOTE: This is an experimental feature. This will remove the message from the
                                conversation history in the Semantic Workbench, but it is up to the individual assistant
                                implementations to handle message deletion and making decisions on what to do with other
                                systems that may have received the message (such as synthetic memories that may have
                                been created or summaries, etc.)
                            </em>
                        </p>
                    </>
                ),
                closeLabel: 'Cancel',
                additionalActions: [
                    <DialogTrigger key="delete" disableButtonEnhancement>
                        <Button appearance="primary" onClick={handleDelete} disabled={submitted}>
                            {submitted ? 'Deleting...' : 'Delete'}
                        </Button>
                    </DialogTrigger>,
                ],
            }}
        />
    );
};


=== File: workbench-app/src/components/Conversations/MessageLink.tsx ===
// Copyright (c) Microsoft. All rights reserved.
import { makeStyles } from '@fluentui/react-components';
import { LinkRegular } from '@fluentui/react-icons';
import React from 'react';
import { Conversation } from '../../models/Conversation';
import { ConversationShare } from '../../models/ConversationShare';
import { CommandButton } from '../App/CommandButton';
import { ConversationShareCreate } from './ConversationShareCreate';
import { ConversationShareView } from './ConversationShareView';

const useClasses = makeStyles({
    root: {
        display: 'inline-block',
    },
});

interface MessageLinkProps {
    conversation: Conversation;
    messageId: string;
}

export const MessageLink: React.FC<MessageLinkProps> = ({ conversation, messageId }) => {
    const classes = useClasses();
    const [createDialogOpen, setCreateDialogOpen] = React.useState(false);
    const [createdShare, setCreatedShare] = React.useState<ConversationShare | undefined>(undefined);

    if (!conversation || !messageId) {
        throw new Error('Invalid conversation or message ID');
    }

    return (
        <>
            <div className={classes.root}>
                <CommandButton
                    icon={<LinkRegular />}
                    appearance="subtle"
                    title="Share message link"
                    size="small"
                    onClick={() => setCreateDialogOpen(true)}
                />
            </div>
            {createDialogOpen && (
                <ConversationShareCreate
                    conversation={conversation}
                    linkToMessageId={messageId}
                    onCreated={(share) => setCreatedShare(share)}
                    onClosed={() => setCreateDialogOpen(false)}
                />
            )}
            {createdShare && (
                <ConversationShareView conversationShare={createdShare} onClosed={() => setCreatedShare(undefined)} />
            )}
        </>
    );
};


=== File: workbench-app/src/components/Conversations/MyConversations.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Chat24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Conversation } from '../../models/Conversation';
import { useAppSelector } from '../../redux/app/hooks';
import { useGetAssistantsQuery, useGetConversationsQuery } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';
import { MiniControl } from '../App/MiniControl';
import { MyItemsManager } from '../App/MyItemsManager';
import { ConversationCreate } from './ConversationCreate';
import { ConversationDuplicate } from './ConversationDuplicate';
import { ConversationExport } from './ConversationExport';
import { ConversationRemove } from './ConversationRemove';
import { ConversationRename } from './ConversationRename';
import { ConversationShare } from './ConversationShare';
import { ConversationsImport } from './ConversationsImport';

interface MyConversationsProps {
    conversations?: Conversation[];
    participantId: string;
    title?: string;
    hideInstruction?: boolean;
    onCreate?: (conversation: Conversation) => void;
}

export const MyConversations: React.FC<MyConversationsProps> = (props) => {
    const { conversations, title, hideInstruction, onCreate, participantId } = props;
    const { refetch: refetchAssistants } = useGetAssistantsQuery();
    const { refetch: refetchConversations } = useGetConversationsQuery();
    const [conversationCreateOpen, setConversationCreateOpen] = React.useState(false);
    const localUserId = useAppSelector((state) => state.localUser.id);

    const handleConversationCreate = async (conversation: Conversation) => {
        await refetchConversations();
        onCreate?.(conversation);
    };

    const handleConversationsImport = async (_conversationIds: string[]) => {
        await refetchAssistants();
        await refetchConversations();
    };

    return (
        <MyItemsManager
            items={conversations
                ?.toSorted((a, b) => a.title.toLocaleLowerCase().localeCompare(b.title.toLocaleLowerCase()))
                .map((conversation) => (
                    <MiniControl
                        key={conversation.id}
                        icon={<Chat24Regular />}
                        label={conversation.title}
                        linkUrl={`/${encodeURIComponent(conversation.id)}`}
                        actions={
                            <>
                                <ConversationRename
                                    disabled={conversation.ownerId !== localUserId}
                                    conversationId={conversation.id}
                                    value={conversation.title}
                                    iconOnly
                                />
                                <ConversationExport conversationId={conversation.id} iconOnly />
                                <ConversationDuplicate conversationId={conversation.id} iconOnly />
                                <ConversationShare conversation={conversation} iconOnly />
                                <ConversationRemove
                                    conversations={conversation}
                                    participantId={participantId}
                                    iconOnly
                                />
                            </>
                        }
                    />
                ))}
            title={title ?? 'My Conversations'}
            itemLabel="Conversation"
            hideInstruction={hideInstruction}
            actions={
                <>
                    <CommandButton
                        icon={<Chat24Regular />}
                        label={`New Conversation`}
                        description={`Create a new conversation`}
                        onClick={() => setConversationCreateOpen(true)}
                    />
                    <ConversationCreate
                        open={conversationCreateOpen}
                        onOpenChange={(open) => setConversationCreateOpen(open)}
                        onCreate={handleConversationCreate}
                    />
                    <ConversationsImport onImport={handleConversationsImport} />
                </>
            }
        />
    );
};


=== File: workbench-app/src/components/Conversations/MyShares.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Copy24Regular, Info24Regular, Share24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useConversationUtility } from '../../libs/useConversationUtility';
import { Conversation } from '../../models/Conversation';
import { ConversationShare } from '../../models/ConversationShare';
import { CommandButton } from '../App/CommandButton';
import { CopyButton } from '../App/CopyButton';
import { MiniControl } from '../App/MiniControl';
import { MyItemsManager } from '../App/MyItemsManager';
import { ConversationShareCreate } from './ConversationShareCreate';
import { ConversationShareView } from './ConversationShareView';
import { ShareRemove } from './ShareRemove';

interface MySharesProps {
    shares: ConversationShare[];
    title?: string;
    hideInstruction?: boolean;
    conversation?: Conversation;
}

export const MyShares: React.FC<MySharesProps> = (props) => {
    const { shares, hideInstruction, title, conversation } = props;
    const [newOpen, setNewOpen] = React.useState(Boolean(conversation && shares.length === 0));
    const [conversationShareForDetails, setConversationShareForDetails] = React.useState<ConversationShare>();
    const conversationUtility = useConversationUtility();

    const createTitle = 'Create a new share link';

    // The create share button is internal to the MyShares component so that we're always
    // presenting the list of current shares for the conversation in case the user wants to
    // reuse a previously created share link.
    const actions = conversation ? (
        <CommandButton label="New Share" description={createTitle} onClick={() => setNewOpen(true)} />
    ) : (
        <></>
    );

    const titleFor = (share: ConversationShare) => {
        const { shareType } = conversationUtility.getShareType(share);
        return `${share.label} (${shareType.toLowerCase()})`;
    };

    const linkFor = (share: ConversationShare) => {
        return conversationUtility.getShareLink(share);
    };

    return (
        <>
            <MyItemsManager
                items={shares.map((share) => (
                    <MiniControl
                        key={share.id}
                        icon={<Share24Regular />}
                        label={titleFor(share)}
                        linkUrl={linkFor(share)}
                        tooltip="Open share link"
                        actions={
                            <>
                                <CommandButton
                                    icon={<Info24Regular />}
                                    iconOnly
                                    onClick={() => setConversationShareForDetails(share)}
                                    description="View details"
                                />
                                <CopyButton data={linkFor(share)} icon={<Copy24Regular />} tooltip="Copy share link" />
                                <ShareRemove share={share} iconOnly />
                            </>
                        }
                    />
                ))}
                title={title ?? 'My Shared Links'}
                itemLabel="Share Link"
                hideInstruction={hideInstruction}
                actions={actions}
            />
            {newOpen && conversation && (
                <ConversationShareCreate
                    conversation={conversation}
                    onClosed={() => setNewOpen(false)}
                    onCreated={(createdShare) => setConversationShareForDetails(createdShare)}
                />
            )}
            {conversationShareForDetails && (
                <ConversationShareView
                    conversationShare={conversationShareForDetails}
                    showDetails
                    onClosed={() => setConversationShareForDetails(undefined)}
                />
            )}
        </>
    );
};


=== File: workbench-app/src/components/Conversations/ParticipantAvatar.tsx ===
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


=== File: workbench-app/src/components/Conversations/ParticipantAvatarGroup.tsx ===
import {
    AvatarGroup,
    AvatarGroupItem,
    AvatarGroupPopover,
    makeStyles,
    partitionAvatarGroupItems,
    Persona,
    Popover,
    PopoverSurface,
    PopoverTrigger,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { useParticipantUtility } from '../../libs/useParticipantUtility';
import { ConversationParticipant } from '../../models/ConversationParticipant';

const useClasses = makeStyles({
    popover: {
        display: 'flex',
        flexDirection: 'row',
        gap: tokens.spacingHorizontalM,
        alignItems: 'center',
    },
});

interface ParticipantAvatarGroupProps {
    participants: ConversationParticipant[];
    layout?: 'pie' | 'spread' | 'stack';
    maxInlineItems?: number;
}

interface ParticipantAvatarGroupItemProps {
    participant: ConversationParticipant;
    enablePopover?: boolean;
}

const ParticipantAvatarGroupItem: React.FC<ParticipantAvatarGroupItemProps> = (props) => {
    const { participant, enablePopover } = props;
    const classes = useClasses();
    const { getAvatarData } = useParticipantUtility();

    const avatar = getAvatarData(participant);

    if (!enablePopover) {
        return <AvatarGroupItem name={participant.name} avatar={avatar} />;
    }

    return (
        <Popover>
            <PopoverTrigger>
                <AvatarGroupItem name={participant.name} avatar={avatar} />
            </PopoverTrigger>
            <PopoverSurface className={classes.popover}>
                <Persona name={participant.name} avatar={avatar} textAlignment="center" />
            </PopoverSurface>
        </Popover>
    );
};

export const ParticipantAvatarGroup: React.FC<ParticipantAvatarGroupProps> = (props) => {
    const { participants, layout, maxInlineItems } = props;

    const avatarLayout = layout ?? 'pie';

    const partitionedParticipants = partitionAvatarGroupItems({
        items: participants.map((participant) => participant.name),
        layout: avatarLayout,
        maxInlineItems:
            maxInlineItems ??
            {
                pie: 0,
                spread: 3,
                stack: 3,
            }[avatarLayout],
    });

    return (
        <AvatarGroup layout={avatarLayout}>
            {partitionedParticipants.inlineItems.map((_, index) => (
                <ParticipantAvatarGroupItem
                    key={index}
                    participant={participants[index]}
                    enablePopover={layout !== 'pie'}
                />
            ))}
            {partitionedParticipants.overflowItems && (
                <AvatarGroupPopover>
                    {partitionedParticipants.overflowItems.map((_, index) => (
                        <ParticipantAvatarGroupItem key={index} participant={participants[index]} />
                    ))}
                </AvatarGroupPopover>
            )}
        </AvatarGroup>
    );
};

export const MemoizedParticipantAvatarGroup = React.memo(ParticipantAvatarGroup);


=== File: workbench-app/src/components/Conversations/ParticipantItem.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Menu,
    MenuItem,
    MenuList,
    MenuPopover,
    MenuTrigger,
    Persona,
    makeStyles,
    tokens,
} from '@fluentui/react-components';
import {
    DatabaseRegular,
    EditRegular,
    MoreHorizontalRegular,
    PlugDisconnectedRegular,
    SettingsRegular,
} from '@fluentui/react-icons';
import React from 'react';
import { useParticipantUtility } from '../../libs/useParticipantUtility';
import { Assistant } from '../../models/Assistant';
import { Conversation } from '../../models/Conversation';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { useGetAssistantQuery } from '../../services/workbench';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingHorizontalM,
    },
    participant: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
    },
    actions: {
        display: 'flex',
        flexDirection: 'row',
        gap: tokens.spacingHorizontalS,
    },
});

interface ParticipantItemProps {
    conversation: Conversation;
    participant: ConversationParticipant;
    readOnly?: boolean;
    onConfigure?: (assistant: Assistant) => void;
    onRename?: (assistant: Assistant) => void;
    onServiceInfo?: (assistant: Assistant) => void;
    onRemove?: (assistant: Assistant) => void;
}

export const ParticipantItem: React.FC<ParticipantItemProps> = (props) => {
    const { conversation, participant, readOnly, onConfigure, onRename, onServiceInfo, onRemove } = props;
    const classes = useClasses();
    const { getAvatarData } = useParticipantUtility();

    const { data: assistant, error: assistantError } = useGetAssistantQuery(participant.id, {
        skip: participant.role !== 'assistant',
    });

    if (assistantError) {
        const errorMessage = JSON.stringify(assistantError);
        throw new Error(`Error loading assistant (${participant.id}): ${errorMessage}`);
    }

    const handleMenuItemClick = React.useCallback(
        (event: React.MouseEvent<HTMLDivElement>, handler?: (conversation: Conversation) => void) => {
            event.stopPropagation();
            handler?.(conversation);
        },
        [conversation],
    );

    const assistantActions = React.useMemo(() => {
        if (participant.role !== 'assistant' || !assistant || readOnly) {
            return null;
        }

        return (
            <Menu>
                <MenuTrigger disableButtonEnhancement>
                    <Button icon={<MoreHorizontalRegular />} />
                </MenuTrigger>
                <MenuPopover>
                    <MenuList>
                        {/* FIXME: complete the menu items */}
                        {onConfigure && (
                            <MenuItem
                                icon={<SettingsRegular />}
                                onClick={(event) => handleMenuItemClick(event, () => onConfigure(assistant))}
                            >
                                Configure
                            </MenuItem>
                        )}
                        {onRename && (
                            <MenuItem
                                icon={<EditRegular />}
                                onClick={(event) => handleMenuItemClick(event, () => onRename(assistant))}
                            >
                                Rename
                            </MenuItem>
                        )}
                        {onServiceInfo && (
                            <MenuItem
                                icon={<DatabaseRegular />}
                                onClick={(event) => handleMenuItemClick(event, () => onServiceInfo(assistant))}
                            >
                                Service Info
                            </MenuItem>
                        )}
                        {onRemove && (
                            <MenuItem
                                icon={<PlugDisconnectedRegular />}
                                onClick={(event) => handleMenuItemClick(event, () => onRemove(assistant))}
                            >
                                Remove
                            </MenuItem>
                        )}
                    </MenuList>
                </MenuPopover>
            </Menu>
        );
    }, [participant.role, assistant, readOnly, onConfigure, onRename, onServiceInfo, onRemove, handleMenuItemClick]);

    return (
        <div className={classes.participant} key={participant.id}>
            <Persona
                name={participant.name}
                avatar={getAvatarData(participant)}
                secondaryText={
                    participant.role + { read: ' (observer)', read_write: '' }[participant.conversationPermission]
                }
                presence={
                    participant.online === undefined
                        ? undefined
                        : {
                              status: participant.online ? 'available' : 'offline',
                          }
                }
            />
            {assistantActions}
        </div>
    );
};


=== File: workbench-app/src/components/Conversations/ParticipantList.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { useParticipantUtility } from '../../libs/useParticipantUtility';
import { Assistant } from '../../models/Assistant';
import { Conversation } from '../../models/Conversation';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { useAddConversationParticipantMutation, useCreateConversationMessageMutation } from '../../services/workbench';
import { AssistantAdd } from '../Assistants/AssistantAdd';
import { AssistantConfigureDialog } from '../Assistants/AssistantConfigure';
import { AssistantRemoveDialog } from '../Assistants/AssistantRemove';
import { AssistantRenameDialog } from '../Assistants/AssistantRename';
import { AssistantServiceInfoDialog } from '../Assistants/AssistantServiceInfo';
import { ParticipantItem } from './ParticipantItem';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingHorizontalM,
    },
    participant: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
    },
    actions: {
        display: 'flex',
        flexDirection: 'row',
        gap: tokens.spacingHorizontalS,
    },
});

interface ParticipantListProps {
    conversation: Conversation;
    participants: ConversationParticipant[];
    preventAssistantModifyOnParticipantIds?: string[];
    readOnly: boolean;
}

export const ParticipantList: React.FC<ParticipantListProps> = (props) => {
    const { conversation, participants, preventAssistantModifyOnParticipantIds = [], readOnly } = props;
    const classes = useClasses();

    const { sortParticipants } = useParticipantUtility();

    const [addConversationParticipant] = useAddConversationParticipantMutation();
    const [createConversationMessage] = useCreateConversationMessageMutation();

    const [configureAssistant, setConfigureAssistant] = React.useState<Assistant>();
    const [renameAssistant, setRenameAssistant] = React.useState<Assistant>();
    const [serviceInfoAssistant, setServiceInfoAssistant] = React.useState<Assistant>();
    const [removeAssistant, setRemoveAssistant] = React.useState<Assistant>();

    const handleAssistantAdd = async (assistant: Assistant) => {
        // send notice message first, to announce before assistant reacts to create event
        await createConversationMessage({
            conversationId: conversation.id,
            content: `${assistant.name} added to conversation`,
            messageType: 'notice',
        });

        await addConversationParticipant({
            conversationId: conversation.id,
            participantId: assistant.id,
        });
    };

    const actionHelpers = React.useMemo(
        () => (
            <>
                <AssistantConfigureDialog
                    assistant={configureAssistant}
                    open={configureAssistant !== undefined}
                    onOpenChange={() => setConfigureAssistant(undefined)}
                />
                <AssistantRenameDialog
                    assistant={renameAssistant}
                    conversationId={conversation.id}
                    open={renameAssistant !== undefined}
                    onOpenChange={() => setRenameAssistant(undefined)}
                    onRename={async () => setRenameAssistant(undefined)}
                />
                <AssistantServiceInfoDialog
                    assistant={serviceInfoAssistant}
                    open={serviceInfoAssistant !== undefined}
                    onOpenChange={() => setServiceInfoAssistant(undefined)}
                />
                <AssistantRemoveDialog
                    assistant={removeAssistant}
                    conversationId={conversation.id}
                    open={removeAssistant !== undefined}
                    onOpenChange={() => setRemoveAssistant(undefined)}
                    onRemove={async () => setRemoveAssistant(undefined)}
                />
            </>
        ),
        [configureAssistant, conversation.id, removeAssistant, renameAssistant, serviceInfoAssistant],
    );

    const exceptAssistantIds = participants
        .filter((participant) => participant.active && participant.role === 'assistant')
        .map((participant) => participant.id);

    return (
        <div className={classes.root}>
            {actionHelpers}
            <AssistantAdd disabled={readOnly} exceptAssistantIds={exceptAssistantIds} onAdd={handleAssistantAdd} />
            {sortParticipants(participants).map((participant) => (
                <ParticipantItem
                    key={participant.id}
                    conversation={conversation}
                    participant={participant}
                    readOnly={readOnly || preventAssistantModifyOnParticipantIds?.includes(participant.id)}
                    onConfigure={(assistant) => setConfigureAssistant(assistant)}
                    onRename={(assistant) => setRenameAssistant(assistant)}
                    onServiceInfo={(assistant) => setServiceInfoAssistant(assistant)}
                    onRemove={(assistant) => setRemoveAssistant(assistant)}
                />
            ))}
        </div>
    );
};


=== File: workbench-app/src/components/Conversations/ParticipantStatus.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { LatencyLoader } from '@fluentui-copilot/react-copilot';
import { Text, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { useAppSelector } from '../../redux/app/hooks';

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
    const localUserId = useAppSelector((state) => state.localUser.id);

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
            if (participant.id === localUserId) return false;
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


=== File: workbench-app/src/components/Conversations/RewindConversation.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogTrigger } from '@fluentui/react-components';
import { RewindRegular } from '@fluentui/react-icons';
import React from 'react';
import { CommandButton } from '../App/CommandButton';

// TODO: consider removing attachments to messages that are deleted
// and send the appropriate events to the assistants

interface RewindConversationProps {
    onRewind?: (redo: boolean) => void;
    disabled?: boolean;
}

export const RewindConversation: React.FC<RewindConversationProps> = (props) => {
    const { onRewind, disabled } = props;
    const [submitted, setSubmitted] = React.useState(false);

    const handleRewind = React.useCallback(
        async (redo: boolean = false) => {
            if (submitted) {
                return;
            }
            setSubmitted(true);

            try {
                onRewind?.(redo);
            } finally {
                setSubmitted(false);
            }
        },
        [onRewind, submitted],
    );

    return (
        <CommandButton
            disabled={disabled}
            description="Rewind conversation to before this message, with optional redo."
            icon={<RewindRegular />}
            iconOnly={true}
            dialogContent={{
                trigger: <Button appearance="subtle" icon={<RewindRegular />} size="small" />,
                title: 'Rewind Conversation',
                content: (
                    <>
                        <p>
                            Are you sure you want to rewind the conversation to before this message? This action cannot
                            be undone.
                        </p>
                        <p>
                            Optionally, you can choose to rewind the conversation and then redo the chosen message. This
                            will rewind the conversation to before the chosen message and then re-add the message back
                            to the conversation, effectively replaying the message.
                        </p>
                        <p>
                            <em>NOTE: This is an experimental feature.</em>
                        </p>
                        <p>
                            <em>
                                This will remove the messages from the conversation history in the Semantic Workbench,
                                but it is up to the individual assistant implementations to handle message deletion and
                                making decisions on what to do with other systems that may have received the message
                                (such as synthetic memories that may have been created or summaries, etc.)
                            </em>
                        </p>
                        <p>
                            <em>
                                Files or other data associated with the messages will not be removed from the system.
                            </em>
                        </p>
                    </>
                ),
                closeLabel: 'Cancel',
                additionalActions: [
                    <DialogTrigger key="rewind" disableButtonEnhancement>
                        <Button appearance="primary" onClick={() => handleRewind()} disabled={submitted}>
                            {submitted ? 'Rewinding...' : 'Rewind'}
                        </Button>
                    </DialogTrigger>,
                    <DialogTrigger key="rewindWithRedo" disableButtonEnhancement>
                        <Button onClick={() => handleRewind(true)} disabled={submitted}>
                            {submitted ? 'Rewinding and redoing...' : 'Rewind with Redo'}
                        </Button>
                    </DialogTrigger>,
                ],
            }}
        />
    );
};


=== File: workbench-app/src/components/Conversations/ShareRemove.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogTrigger } from '@fluentui/react-components';
import { Delete24Regular } from '@fluentui/react-icons';
import React from 'react';
import { ConversationShare } from '../../models/ConversationShare';
import { useDeleteShareMutation } from '../../services/workbench/share';
import { CommandButton } from '../App/CommandButton';

interface ShareRemoveProps {
    share: ConversationShare;
    onRemove?: () => void;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const ShareRemove: React.FC<ShareRemoveProps> = (props) => {
    const { share, onRemove: onDelete, iconOnly, asToolbarButton } = props;
    const [deleteShare] = useDeleteShareMutation();
    const [isDeleting, setIsDeleting] = React.useState(false);

    const handleDelete = React.useCallback(async () => {
        if (isDeleting) {
            return;
        }
        setIsDeleting(true);

        try {
            await deleteShare(share.id);
            onDelete?.();
        } finally {
            setIsDeleting(false);
        }
    }, [isDeleting, deleteShare, share.id, onDelete]);

    return (
        <CommandButton
            description="Delete share"
            icon={<Delete24Regular />}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
            label="Delete"
            disabled={isDeleting}
            dialogContent={{
                title: 'Delete Share',
                content: <p>Are you sure you want to delete this share?</p>,
                closeLabel: 'Cancel',
                additionalActions: [
                    <DialogTrigger key="delete" disableButtonEnhancement>
                        <Button appearance="primary" onClick={handleDelete} disabled={isDeleting}>
                            {isDeleting ? 'Deleting...' : 'Delete'}
                        </Button>
                    </DialogTrigger>,
                ],
            }}
        />
    );
};


=== File: workbench-app/src/components/Conversations/SpeechButton.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button } from '@fluentui/react-components';
import { Mic20Regular } from '@fluentui/react-icons';
import debug from 'debug';
import * as speechSdk from 'microsoft-cognitiveservices-speech-sdk';
import React from 'react';
import { Constants } from '../../Constants';
import { useWorkbenchService } from '../../libs/useWorkbenchService';
import { TooltipWrapper } from '../App/TooltipWrapper';

const log = debug(Constants.debug.root).extend('SpeechButton');

interface SpeechButtonProps {
    disabled?: boolean;
    onListeningChange: (isListening: boolean) => void;
    onSpeechRecognizing?: (text: string) => void;
    onSpeechRecognized: (text: string) => void;
}

export const SpeechButton: React.FC<SpeechButtonProps> = (props) => {
    const { disabled, onListeningChange, onSpeechRecognizing, onSpeechRecognized } = props;
    const [recognizer, setRecognizer] = React.useState<speechSdk.SpeechRecognizer>();
    const [isInitialized, setIsInitialized] = React.useState(false);
    const [isListening, setIsListening] = React.useState(false);
    const [lastSpeechResultTimestamp, setLastSpeechResultTimestamp] = React.useState(0);

    const [azureSpeechTokenAcquisitionTimestamp, setAzureSpeechTokenAcquisitionTimestamp] = React.useState(0);
    const [tokenResult, setTokenResult] = React.useState({ token: '', region: '' });

    const workbenchService = useWorkbenchService();

    const getAzureSpeechTokenAsync = React.useCallback(async () => {
        if (Date.now() - azureSpeechTokenAcquisitionTimestamp <= Constants.app.azureSpeechTokenRefreshIntervalMs) {
            return tokenResult;
        }

        log('Refreshing Azure Speech token');
        // Fetch the Azure Speech token
        const { token, region } = await workbenchService.getAzureSpeechTokenAsync();

        // Save the token acquisition timestamp
        setAzureSpeechTokenAcquisitionTimestamp(Date.now());
        setTokenResult({ token, region });
        return { token, region };
    }, [azureSpeechTokenAcquisitionTimestamp, workbenchService, tokenResult]);

    const getRecognizer = React.useCallback(async () => {
        // Get the Azure Speech token
        const { token, region } = await getAzureSpeechTokenAsync();
        if (!token || !region) {
            log('No Azure Speech token or region available, disabling speech input');
            return;
        }

        // Create the speech recognizer
        const speechConfig = speechSdk.SpeechConfig.fromAuthorizationToken(token, region);
        speechConfig.outputFormat = speechSdk.OutputFormat.Detailed;
        const speechRecognizer = new speechSdk.SpeechRecognizer(speechConfig);

        // Setup the recognizer

        // Triggered when the speech recognizer has started listening
        speechRecognizer.sessionStarted = (_sender, event) => {
            log('Session started', event);
            setIsListening(true);
            setLastSpeechResultTimestamp(Date.now());
        };

        // Triggered when the speech recognizer has detected that speech has started
        speechRecognizer.speechStartDetected = (_sender, event) => {
            log('Speech started', event);
            setLastSpeechResultTimestamp(Date.now());
        };

        // Triggered periodically while the speech recognizer is recognizing speech
        speechRecognizer.recognizing = (_sender, event) => {
            log('Speech Recognizing', event);

            const text = event.result.text;
            if (text.trim() === '') return;

            onSpeechRecognizing?.(text);
            setLastSpeechResultTimestamp(Date.now());
        };

        // Triggered when the speech recognizer has recognized speech
        speechRecognizer.recognized = (_sender, event) => {
            log('Speech Recognized', event);

            const text = event.result.text;
            if (text.trim() === '') return;

            onSpeechRecognized(text);
            setLastSpeechResultTimestamp(Date.now());
        };

        // Triggered when the speech recognizer has detected that speech has stopped
        speechRecognizer.speechEndDetected = (_sender, event) => {
            log('Speech ended', event);
        };

        // Triggered when the speech recognizer has stopped listening
        speechRecognizer.sessionStopped = (_sender, event) => {
            log('Session stopped', event);
            setIsListening(false);
        };

        // Triggered when the speech recognizer has canceled
        speechRecognizer.canceled = (_sender, event) => {
            log('Speech Canceled', event);
            setIsListening(false);
        };

        setRecognizer(speechRecognizer);
    }, [getAzureSpeechTokenAsync, onSpeechRecognized, onSpeechRecognizing]);

    React.useEffect(() => {
        // If the recognizer is already initialized, return
        if (isInitialized) return;

        // Set the recognizer as initialized
        setIsInitialized(true);

        (async () => {
            // Fetch the recognizer
            await getRecognizer();
        })();
    }, [getRecognizer, isInitialized, recognizer]);

    React.useEffect(() => {
        onListeningChange(isListening);
    }, [isListening, onListeningChange]);

    // Call this function to stop the speech recognizer
    const stopListening = React.useCallback(() => {
        if (!isListening) return;
        recognizer?.stopContinuousRecognitionAsync();
        setIsListening(false);
    }, [isListening, recognizer]);

    // Call this function to start the speech recognizer to recognize speech continuously until stopped
    const recognizeContinuously = React.useCallback(async () => {
        if (isListening || !recognizer) return;

        const { token } = await getAzureSpeechTokenAsync();
        if (token === '') {
            log('No Azure Speech token available for refresh');
            return;
        }

        recognizer.authorizationToken = token;

        // Start the speech recognizer
        recognizer.startContinuousRecognitionAsync();
    }, [getAzureSpeechTokenAsync, isListening, recognizer]);

    // check if the last speech result is too old, if so, stop listening
    React.useEffect(() => {
        // check in an interval
        const interval = setInterval(() => {
            if (isListening && Date.now() - lastSpeechResultTimestamp > Constants.app.speechIdleTimeoutMs) {
                stopListening();
            }
        }, 1000);

        return () => clearInterval(interval);
    }, [isListening, lastSpeechResultTimestamp, stopListening]);

    if (!recognizer) return null;

    return (
        <TooltipWrapper content={isListening ? 'Click to stop listening.' : 'Click to start listening.'}>
            <Button
                appearance="transparent"
                // should ignore the disabled prop when isListening is true so that
                // the button can still be clicked to stop listening
                disabled={(!isListening && disabled) || !recognizer}
                style={{ color: isListening ? 'red' : undefined }}
                icon={<Mic20Regular color={isListening ? 'green' : undefined} />}
                onClick={isListening ? stopListening : recognizeContinuously}
            />
        </TooltipWrapper>
    );
};


=== File: workbench-app/src/components/Conversations/ToolCalls.tsx ===
import {
    Accordion,
    AccordionHeader,
    AccordionItem,
    AccordionPanel,
    makeStyles,
    shorthands,
    Text,
    tokens,
} from '@fluentui/react-components';
import { Toolbox24Regular } from '@fluentui/react-icons';
import React from 'react';
import { ConversationMessage } from '../../models/ConversationMessage';
import { CodeLabel } from '../App/CodeLabel';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
    },
    item: {
        backgroundColor: tokens.colorNeutralBackground3,
        borderRadius: tokens.borderRadiusMedium,
        ...shorthands.border('none'),
        marginTop: tokens.spacingVerticalM,
    },
    header: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: tokens.spacingHorizontalS,
    },
});

interface ToolCallsProps {
    message: ConversationMessage;
}

/**
 * Allows experimental support for displaying tool calls that are attached to a message
 * via the metadata property. To use this, the message must have a metadata property
 * with a 'tool_calls' key, which is an array of tool calls, each with an 'id', 'name',
 * and 'arguments' property.
 *
 * [Read more about special metadata support in UX...](../../../docs/MESSAGE_METADATA.md)
 *
 * This component will display each tool call in an accordion, with the tool name
 * as the header and the arguments as the content.
 */
export const ToolCalls: React.FC<ToolCallsProps> = (props) => {
    const { message } = props;
    const classes = useClasses();

    const toolCalls: { id: string; name: string; arguments: string }[] = message.metadata?.['tool_calls'];

    if (!toolCalls || toolCalls.length === 0) {
        return null;
    }

    return (
        <div className={classes.root}>
            {toolCalls.map((toolCall) => {
                const content = JSON.stringify(toolCall.arguments, null, 4);

                return (
                    <Accordion key={toolCall.id} collapsible className={classes.item}>
                        <AccordionItem value="1">
                            <AccordionHeader icon={<Toolbox24Regular />}>
                                <div className={classes.header}>
                                    <Text>Invoking tool</Text>
                                    <CodeLabel>{toolCall.name}</CodeLabel>
                                </div>
                            </AccordionHeader>
                            <AccordionPanel>{content}</AccordionPanel>
                        </AccordionItem>
                    </Accordion>
                );
            })}
        </div>
    );
};

export const MemoizedToolResultMessage = React.memo(ToolCalls);


=== File: workbench-app/src/components/FrontDoor/Chat/AssistantDrawer.tsx ===
import { makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { Assistant } from '../../../models/Assistant';
import { Conversation } from '../../../models/Conversation';
import { AssistantCanvasList } from '../../Conversations/Canvas/AssistantCanvasList';
import { CanvasDrawer, CanvasDrawerOptions } from './CanvasDrawer';

const useClasses = makeStyles({
    noContent: {
        padding: tokens.spacingHorizontalM,
    },
});

interface AssistantDrawerProps {
    drawerOptions: CanvasDrawerOptions;
    conversation: Conversation;
    conversationAssistants?: Assistant[];
    selectedAssistant?: Assistant;
}

export const AssistantDrawer: React.FC<AssistantDrawerProps> = (props) => {
    const { drawerOptions, conversation, conversationAssistants, selectedAssistant } = props;
    const classes = useClasses();

    let title = '';
    if (!conversationAssistants || conversationAssistants.length === 0 || conversationAssistants.length > 1) {
        title = 'Assistants';
    } else {
        title = conversationAssistants[0].name;
    }

    const canvasContent =
        conversationAssistants && conversationAssistants.length > 0 ? (
            <AssistantCanvasList
                selectedAssistant={selectedAssistant}
                conversation={conversation}
                conversationAssistants={conversationAssistants}
            />
        ) : (
            <div className={classes.noContent}>No assistants participating in conversation.</div>
        );

    const options = React.useMemo(
        () => ({
            ...drawerOptions,
            title,
            resizable: true,
        }),
        [drawerOptions, title],
    );

    return <CanvasDrawer options={options}>{canvasContent}</CanvasDrawer>;
};


=== File: workbench-app/src/components/FrontDoor/Chat/CanvasDrawer.tsx ===
import {
    DialogModalType,
    Drawer,
    DrawerBody,
    DrawerHeader,
    DrawerHeaderTitle,
    makeStyles,
    mergeClasses,
    Title3,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { Constants } from '../../../Constants';
import { useAppDispatch, useAppSelector } from '../../../redux/app/hooks';
import { setChatWidthPercent } from '../../../redux/features/app/appSlice';

const useClasses = makeStyles({
    root: {
        position: 'relative',
        overflow: 'hidden',

        display: 'flex',
        height: '100%',
        boxSizing: 'border-box',
        backgroundColor: '#fff',
    },
    drawer: {
        willChange: 'width',
        transitionProperty: 'width',
        // approximate 60fps (1000ms / 60 = 16.666ms)
        transitionDuration: '16.666ms',
    },
    resizable: {
        minWidth: Constants.app.resizableCanvasDrawerMinWidth,
        maxWidth: Constants.app.resizableCanvasDrawerMaxWidth,
    },
    title: {
        marginTop: tokens.spacingVerticalXL,
    },
    resizer: {
        width: tokens.spacingHorizontalXL,
        position: 'absolute',
        top: 0,
        bottom: 0,
        cursor: 'col-resize',
        resize: 'horizontal',
        zIndex: tokens.zIndexContent,
        boxSizing: 'border-box',
        userSelect: 'none',

        // if drawer is coming from the right, set resizer on the left
        '&.right': {
            left: 0,
            borderLeft: `${tokens.strokeWidthThick} solid ${tokens.colorNeutralStroke2}`,

            '&:hover': {
                borderLeftWidth: tokens.strokeWidthThickest,
            },
        },

        // if drawer is coming from the left, set resizer on the right
        '&.left': {
            right: 0,
            borderRight: `${tokens.strokeWidthThick} solid ${tokens.colorNeutralStroke2}`,

            '&:hover': {
                borderRightWidth: tokens.strokeWidthThickest,
            },
        },
    },
    resizerActive: {
        borderRightWidth: '4px',
        borderRightColor: tokens.colorNeutralBackground5Pressed,
    },
});

// create types for CanvasDrawer
export type CanvasDrawerSize = 'small' | 'medium' | 'large' | 'full';
export type CanvasDrawerSide = 'left' | 'right';
export type CanvasDrawerMode = 'inline' | 'overlay';
export type CanvasDrawerOptions = {
    classNames?: {
        container?: string;
        drawer?: string;
        header?: string;
        title?: string;
        body?: string;
    };
    open?: boolean;
    title?: string | React.ReactNode;
    size?: CanvasDrawerSize;
    side?: CanvasDrawerSide;
    mode?: CanvasDrawerMode;
    modalType?: DialogModalType;
    resizable?: boolean;
};

interface CanvasDrawerProps {
    options: CanvasDrawerOptions;
    children?: React.ReactNode;
}

export const CanvasDrawer: React.FC<CanvasDrawerProps> = (props) => {
    const { options, children } = props;
    const { classNames, open, title, size, side, mode, modalType, resizable } = options;
    const classes = useClasses();
    const animationFrame = React.useRef<number>(0);
    const sidebarRef = React.useRef<HTMLDivElement>(null);
    const [isResizing, setIsResizing] = React.useState(false);
    const chatWidthPercent = useAppSelector((state) => state.app.chatWidthPercent);
    const dispatch = useAppDispatch();

    const titleContent = typeof title === 'string' ? <Title3>{title}</Title3> : title;

    const startResizing = React.useCallback(() => setIsResizing(true), []);
    const stopResizing = React.useCallback(() => setIsResizing(false), []);

    const resize = React.useCallback(
        (event: MouseEvent) => {
            const { clientX } = event;
            animationFrame.current = requestAnimationFrame(() => {
                if (isResizing && sidebarRef.current) {
                    const clientRect = sidebarRef.current.getBoundingClientRect();
                    const resizerPosition = side === 'left' ? clientRect.left : clientRect.right;
                    const desiredWidth = resizerPosition - clientX;
                    const desiredWidthPercent = (desiredWidth / window.innerWidth) * 100;
                    console.log(
                        `clientRect: ${clientRect}`,
                        `clientX: ${clientX}`,
                        `desiredWidth: ${desiredWidth}`,
                        `desiredWidthPercent: ${desiredWidthPercent}`,
                    );
                    dispatch(setChatWidthPercent(desiredWidthPercent));
                }
            });
        },
        [dispatch, isResizing, side],
    );

    const ResizeComponent: React.FC<{ className?: string }> = (props: { className?: string }) => (
        <div
            className={mergeClasses(
                classes.resizer,
                side ?? 'right',
                isResizing && classes.resizerActive,
                props.className,
            )}
            onMouseDown={startResizing}
        />
    );

    React.useEffect(() => {
        window.addEventListener('mousemove', resize);
        window.addEventListener('mouseup', stopResizing);

        return () => {
            cancelAnimationFrame(animationFrame.current);
            window.removeEventListener('mousemove', resize);
            window.removeEventListener('mouseup', stopResizing);
        };
    }, [resize, stopResizing]);

    return (
        <div className={mergeClasses(classes.root, classNames?.container)}>
            {resizable && <ResizeComponent className={side} />}
            <Drawer
                className={mergeClasses(classes.drawer, classNames?.drawer, resizable && classes.resizable)}
                ref={sidebarRef}
                size={resizable ? undefined : size}
                style={resizable ? { width: `${chatWidthPercent}vw` } : undefined}
                position={side === 'left' ? 'start' : 'end'}
                open={open}
                modalType={modalType}
                type={mode ?? 'inline'}
            >
                <DrawerHeader className={classNames?.header}>
                    <DrawerHeaderTitle className={mergeClasses(classes.title, classNames?.title)}>
                        {titleContent}
                    </DrawerHeaderTitle>
                </DrawerHeader>
                <DrawerBody className={classNames?.body}>{children}</DrawerBody>
            </Drawer>
        </div>
    );
};


=== File: workbench-app/src/components/FrontDoor/Chat/Chat.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import { EventSourceMessage } from '@microsoft/fetch-event-source';
import React from 'react';
import { Constants } from '../../../Constants';
import { useHistoryUtility } from '../../../libs/useHistoryUtility';
import { useParticipantUtility } from '../../../libs/useParticipantUtility';
import { useSiteUtility } from '../../../libs/useSiteUtility';
import { Assistant } from '../../../models/Assistant';
import { useAppSelector } from '../../../redux/app/hooks';
import { workbenchConversationEvents } from '../../../routes/FrontDoor';
import { ExperimentalNotice } from '../../App/ExperimentalNotice';
import { Loading } from '../../App/Loading';
import { ConversationShare } from '../../Conversations/ConversationShare';
import { InteractHistory } from '../../Conversations/InteractHistory';
import { InteractInput } from '../../Conversations/InteractInput';
import { ParticipantAvatarGroup } from '../../Conversations/ParticipantAvatarGroup';
import { ChatCanvas } from './ChatCanvas';
import { ChatControls } from './ChatControls';

const useClasses = makeStyles({
    // centered content, two rows
    // first is for chat history, fills the space and scrolls
    // second is for input, anchored to the bottom
    root: {
        position: 'relative',
        flex: '1 1 auto',
        display: 'flex',
        flexDirection: 'row',
        height: '100%',
    },
    header: {
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        pointerEvents: 'none',
        zIndex: tokens.zIndexOverlay,
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'space-between',
        backgroundImage: `linear-gradient(to bottom, ${tokens.colorNeutralBackground1}, ${tokens.colorNeutralBackground1}, transparent, transparent)`,
        ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM, tokens.spacingVerticalXXXL),
    },
    headerControls: {
        position: 'relative',
        pointerEvents: 'auto',
        display: 'flex',
        flexDirection: 'row',
        gap: tokens.spacingHorizontalM,
        justifyContent: 'center',
        flex: '1 1 auto',
        overflowX: 'hidden',

        '&.before': {
            left: 0,
            flex: '0 0 auto',
        },

        '&.center': {
            overflow: 'visible',
        },

        '&.after': {
            right: 0,
            flex: '0 0 auto',
        },
    },
    centerContent: {
        position: 'absolute',
        top: 0,
        left: tokens.spacingHorizontalM,
        right: tokens.spacingHorizontalM,
    },
    content: {
        flex: '1 1 auto',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        minWidth: Constants.app.conversationHistoryMinWidth,
    },
    canvas: {
        flex: '0 0 auto',
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'center',
    },
    history: {
        flex: '1 1 auto',
        position: 'relative',
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'center',
        gap: tokens.spacingVerticalM,
    },
    historyContent: {
        // do not use flexbox here, it breaks the virtuoso
        width: '100%',
        maxWidth: `${Constants.app.maxContentWidth}px`,
    },
    historyRoot: {
        paddingTop: tokens.spacingVerticalXXXL,
        boxSizing: 'border-box',
    },
    input: {
        flex: '0 0 auto',
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'center',
        backgroundImage: `linear-gradient(to right, ${tokens.colorNeutralBackground1}, ${tokens.colorBrandBackground2})`,
        ...shorthands.borderTop(tokens.strokeWidthThick, 'solid', tokens.colorNeutralStroke3),
    },
});

interface ChatProps {
    conversationId: string;
    headerBefore?: React.ReactNode;
    headerAfter?: React.ReactNode;
}

export const Chat: React.FC<ChatProps> = (props) => {
    const { conversationId, headerBefore, headerAfter } = props;
    const classes = useClasses();
    const { sortParticipants } = useParticipantUtility();
    const siteUtility = useSiteUtility();
    const localUserId = useAppSelector((state) => state.localUser.id);

    const {
        conversation,
        allConversationMessages,
        conversationParticipants,
        assistants,
        conversationFiles,
        assistantCapabilities,
        error: historyError,
        isLoading: historyIsLoading,
        assistantsRefetch,
        assistantCapabilitiesIsFetching,
        rewindToBefore,
        refetchConversation,
    } = useHistoryUtility(conversationId);

    if (historyError) {
        const errorMessage = JSON.stringify(historyError);
        throw new Error(`Error loading conversation (${conversationId}): ${errorMessage}`);
    }

    React.useEffect(() => {
        if (historyIsLoading) {
            return;
        }

        // handle new message events
        const conversationHandler = async (_event: EventSourceMessage) => {
            await refetchConversation();
        };

        workbenchConversationEvents.addEventListener('conversation.updated', conversationHandler);

        return () => {
            // remove event listeners
            workbenchConversationEvents.removeEventListener('conversation.updated', conversationHandler);
        };
    }, [historyIsLoading, refetchConversation]);

    React.useEffect(() => {
        if (conversation) {
            siteUtility.setDocumentTitle(conversation.title);
        }
    }, [conversation, siteUtility]);

    const conversationAssistants = React.useMemo(() => {
        const results: Assistant[] = [];

        // If the conversation or assistants are not loaded, return early
        if (!conversationParticipants || !assistants) {
            return results;
        }

        for (let conversationParticipant of conversationParticipants) {
            // Only include active assistants
            if (!conversationParticipant.active || conversationParticipant.role !== 'assistant') continue;

            // Find the assistant in the list of assistants
            const assistant = assistants.find((assistant) => assistant.id === conversationParticipant.id);

            if (assistant) {
                // If the assistant is found, add it to the list of assistants
                results.push(assistant);
            } else {
                // If the assistant is not found, refetch the assistants
                assistantsRefetch();
                // Return early to avoid returning an incomplete list of assistants
                return;
            }
        }

        return results.sort((a, b) => a.name.localeCompare(b.name));
    }, [assistants, conversationParticipants, assistantsRefetch]);

    if (historyIsLoading || assistantCapabilitiesIsFetching) {
        return <Loading />;
    }

    if (!conversation) {
        throw new Error(`Conversation (${conversationId}) not found`);
    }

    if (!allConversationMessages) {
        throw new Error(`All conversation messages (${conversationId}) not found`);
    }

    if (!conversationParticipants) {
        throw new Error(`Conversation participants (${conversationId}) not found`);
    }

    if (!assistants) {
        throw new Error(`Assistants (${conversationId}) not found`);
    }

    if (!conversationFiles) {
        throw new Error(`Conversation files (${conversationId}) not found`);
    }

    const readOnly = conversation.conversationPermission === 'read';

    const otherParticipants = sortParticipants(conversationParticipants).filter(
        (participant) => participant.id !== localUserId,
    );

    return (
        <div className={classes.root}>
            <div className={classes.header}>
                <div className={mergeClasses(classes.headerControls, 'before')}>{headerBefore}</div>
                <div className={mergeClasses(classes.headerControls, 'center')}>
                    <ExperimentalNotice className={classes.centerContent} />
                </div>
                <div className={mergeClasses(classes.headerControls, 'after')}>
                    {otherParticipants.length === 1 && (
                        <ParticipantAvatarGroup participants={otherParticipants} layout="spread" />
                    )}
                    {otherParticipants.length > 1 && (
                        <ParticipantAvatarGroup layout="pie" participants={otherParticipants} />
                    )}
                    <ConversationShare iconOnly conversation={conversation} />
                    <ChatControls conversationId={conversation.id} />
                    {headerAfter}
                </div>
            </div>
            <div className={classes.content}>
                <div className={classes.history}>
                    <div className={classes.historyContent}>
                        <InteractHistory
                            className={classes.historyRoot}
                            readOnly={readOnly}
                            conversation={conversation}
                            messages={allConversationMessages}
                            participants={conversationParticipants}
                            onRewindToBefore={rewindToBefore}
                        />
                    </div>
                </div>
                <div className={classes.input}>
                    <InteractInput
                        readOnly={readOnly}
                        conversation={conversation}
                        messages={allConversationMessages}
                        participants={conversationParticipants}
                        assistantCapabilities={assistantCapabilities}
                    />
                </div>
            </div>
            <div className={classes.canvas}>
                <ChatCanvas
                    readOnly={readOnly}
                    conversation={conversation}
                    conversationParticipants={conversationParticipants}
                    conversationFiles={conversationFiles}
                    conversationAssistants={conversationAssistants}
                />
            </div>
        </div>
    );
};


=== File: workbench-app/src/components/FrontDoor/Chat/ChatCanvas.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import debug from 'debug';
import React from 'react';
import { Constants } from '../../../Constants';
import { useChatCanvasController } from '../../../libs/useChatCanvasController';
import { Assistant } from '../../../models/Assistant';
import { Conversation } from '../../../models/Conversation';
import { ConversationFile } from '../../../models/ConversationFile';
import { ConversationParticipant } from '../../../models/ConversationParticipant';
import { useAppSelector } from '../../../redux/app/hooks';
import { AssistantDrawer } from './AssistantDrawer';
import { ConversationDrawer } from './ConversationDrawer';

const log = debug(Constants.debug.root).extend('ChatCanvas');

interface ChatCanvasProps {
    conversationAssistants?: Assistant[];
    conversationParticipants: ConversationParticipant[];
    conversationFiles: ConversationFile[];
    conversation: Conversation;
    preventAssistantModifyOnParticipantIds?: string[];
    readOnly: boolean;
}

export const ChatCanvas: React.FC<ChatCanvasProps> = (props) => {
    const {
        conversationAssistants,
        conversationParticipants,
        conversationFiles,
        conversation,
        preventAssistantModifyOnParticipantIds,
        readOnly,
    } = props;
    const { open, mode, selectedAssistantId } = useAppSelector((state) => state.chatCanvas);
    const chatCanvasController = useChatCanvasController();
    const [firstRun, setFirstRun] = React.useState(true);
    const [selectedAssistant, setSelectedAssistant] = React.useState<Assistant>();

    // Set the selected assistant based on the chat canvas state
    React.useEffect(() => {
        if (!selectedAssistantId || !open || mode !== 'assistant') {
            // If the assistant id is not set, the canvas is closed, or the mode is not assistant, clear
            // the selected assistant and exit early
            setSelectedAssistant(undefined);
            return;
        }

        // If no assistants are in the conversation, unset the selected assistant
        if (!conversationAssistants || conversationAssistants.length === 0) {
            if (selectedAssistant) setSelectedAssistant(undefined);
            // If this is the first run, transition to the conversation mode to add an assistant
            if (firstRun) {
                log('No assistants in the conversation on first run, transitioning to conversation mode');
                chatCanvasController.transitionToState({ open: true, mode: 'conversation' });
                setFirstRun(false);
            }
            return;
        }

        // Find the assistant that corresponds to the selected assistant id
        const assistant = conversationAssistants.find((assistant) => assistant.id === selectedAssistantId);

        // If the selected assistant is not found in the conversation, select the first assistant in the conversation
        if (!assistant) {
            log('Selected assistant not found in conversation, selecting the first assistant in the conversation');
            chatCanvasController.setState({ selectedAssistantId: conversationAssistants[0].id });
            return;
        }

        // If the requested assistant is different from the selected assistant, set the selected assistant
        if (selectedAssistant?.id !== assistant?.id) {
            log(`Setting selected assistant to ${assistant.id}`);
            setSelectedAssistant(assistant);
        }
    }, [conversationAssistants, chatCanvasController, selectedAssistant, firstRun, selectedAssistantId, open, mode]);

    // Determine which drawer to open, default to none
    const openDrawer = open ? mode : 'none';
    return (
        <>
            <ConversationDrawer
                drawerOptions={{
                    open: openDrawer === 'conversation',
                }}
                readOnly={readOnly}
                conversation={conversation}
                conversationParticipants={conversationParticipants}
                conversationFiles={conversationFiles}
                preventAssistantModifyOnParticipantIds={preventAssistantModifyOnParticipantIds}
            />
            <AssistantDrawer
                drawerOptions={{
                    open: openDrawer === 'assistant',
                }}
                conversation={conversation}
                conversationAssistants={conversationAssistants}
                selectedAssistant={selectedAssistant}
            />
        </>
    );
};


=== File: workbench-app/src/components/FrontDoor/Chat/ChatControls.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button, makeStyles, tokens } from '@fluentui/react-components';
import { BookInformation24Regular, ChatSettingsRegular, Dismiss24Regular } from '@fluentui/react-icons';
import { EventSourceMessage } from '@microsoft/fetch-event-source';
import React from 'react';
import { useChatCanvasController } from '../../../libs/useChatCanvasController';
import { useEnvironment } from '../../../libs/useEnvironment';
import { useAppSelector } from '../../../redux/app/hooks';
import { workbenchConversationEvents } from '../../../routes/FrontDoor';
import { TooltipWrapper } from '../../App/TooltipWrapper';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'row',
        gap: tokens.spacingHorizontalM,
    },
});

interface ChatControlsProps {
    conversationId: string;
}

export const ChatControls: React.FC<ChatControlsProps> = (props) => {
    const { conversationId } = props;
    const classes = useClasses();
    const chatCanvasState = useAppSelector((state) => state.chatCanvas);
    const environment = useEnvironment();
    const chatCanvasController = useChatCanvasController();

    React.useEffect(() => {
        const handleFocusEvent = async (event: EventSourceMessage) => {
            const { data } = JSON.parse(event.data);
            chatCanvasController.transitionToState({
                open: true,
                mode: 'assistant',
                selectedAssistantId: data['assistant_id'],
                selectedAssistantStateId: data['state_id'],
            });
        };

        workbenchConversationEvents.addEventListener('assistant.state.focus', handleFocusEvent);

        return () => {
            workbenchConversationEvents.removeEventListener('assistant.state.focus', handleFocusEvent);
        };
    }, [environment, conversationId, chatCanvasController]);

    const handleActivateConversation = () => {
        chatCanvasController.transitionToState({ open: true, mode: 'conversation' });
    };

    const handleActivateAssistant = () => {
        chatCanvasController.transitionToState({ open: true, mode: 'assistant' });
    };

    const handleDismiss = async () => {
        chatCanvasController.transitionToState({ open: false });
    };

    const conversationActive = chatCanvasState.mode === 'conversation' && chatCanvasState.open;
    const assistantActive = chatCanvasState.mode === 'assistant' && chatCanvasState.open;

    return (
        <div className={classes.root}>
            <TooltipWrapper content="Open conversation canvas">
                <Button
                    disabled={conversationActive || chatCanvasController.isTransitioning}
                    icon={<ChatSettingsRegular />}
                    onClick={handleActivateConversation}
                />
            </TooltipWrapper>
            <TooltipWrapper content="Open assistant canvas">
                <Button
                    disabled={assistantActive || chatCanvasController.isTransitioning}
                    icon={<BookInformation24Regular />}
                    onClick={handleActivateAssistant}
                />
            </TooltipWrapper>
            {conversationActive || assistantActive ? (
                <TooltipWrapper content="Close canvas">
                    <Button icon={<Dismiss24Regular />} onClick={handleDismiss} />
                </TooltipWrapper>
            ) : null}
        </div>
    );
};


=== File: workbench-app/src/components/FrontDoor/Chat/ConversationDrawer.tsx ===
import React from 'react';
import { Conversation } from '../../../models/Conversation';
import { ConversationFile } from '../../../models/ConversationFile';
import { ConversationParticipant } from '../../../models/ConversationParticipant';
import { ConversationCanvas } from '../../Conversations/Canvas/ConversationCanvas';
import { CanvasDrawer, CanvasDrawerOptions } from './CanvasDrawer';

interface ConversationDrawerProps {
    drawerOptions: CanvasDrawerOptions;
    readOnly: boolean;
    conversation: Conversation;
    conversationParticipants: ConversationParticipant[];
    conversationFiles: ConversationFile[];
    preventAssistantModifyOnParticipantIds?: string[];
}

export const ConversationDrawer: React.FC<ConversationDrawerProps> = (props) => {
    const {
        drawerOptions,
        readOnly,
        conversation,
        conversationParticipants,
        conversationFiles,
        preventAssistantModifyOnParticipantIds,
    } = props;

    const options: CanvasDrawerOptions = React.useMemo(
        () => ({
            ...drawerOptions,
            size: 'small',
        }),
        [drawerOptions],
    );

    return (
        <CanvasDrawer options={options}>
            <ConversationCanvas
                readOnly={readOnly}
                conversation={conversation}
                conversationParticipants={conversationParticipants}
                conversationFiles={conversationFiles}
                preventAssistantModifyOnParticipantIds={preventAssistantModifyOnParticipantIds}
            />
        </CanvasDrawer>
    );
};


=== File: workbench-app/src/components/FrontDoor/Controls/AssistantCard.tsx ===
import {
    Button,
    Card,
    CardHeader,
    CardPreview,
    makeStyles,
    Menu,
    MenuButtonProps,
    MenuItem,
    MenuList,
    MenuPopover,
    MenuTrigger,
    SplitButton,
    Title3,
    tokens,
} from '@fluentui/react-components';
import { ChatAdd24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useConversationUtility } from '../../../libs/useConversationUtility';
import { useCreateConversation } from '../../../libs/useCreateConversation';
import { Assistant } from '../../../models/Assistant';
import { useGetAssistantServiceInfosQuery } from '../../../services/workbench';
import { MarkdownContentRenderer } from '../../Conversations/ContentRenderers/MarkdownContentRenderer';

interface CardContent {
    contentType: string;
    content: string;
}

interface DashboardCardConfig {
    assistantServiceId: string;
    templateId: string;
    name: string;
    backgroundColor: string;
    cardContent: CardContent;
    icon: string;
}

const useClasses = makeStyles({
    card: {
        padding: 0,
        width: '420px',
    },
    cardHeader: {
        padding: tokens.spacingHorizontalM,
        borderRadius: tokens.borderRadiusMedium,
        borderBottomRightRadius: 0,
        borderBottomLeftRadius: 0,
    },
    cardHeaderNoContent: {
        padding: tokens.spacingHorizontalM,
        borderRadius: tokens.borderRadiusMedium,
    },
    cardHeaderBody: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxSizing: 'border-box',
        width: '100%',
    },
    cardPreview: {
        padding: tokens.spacingHorizontalM,
        paddingBottom: tokens.spacingVerticalL,
        margin: '0 !important',
        width: '100%',
        boxSizing: 'border-box',
        wordWrap: 'break-word',
        overflowWrap: 'break-word',
        '& ul': {
            boxSizing: 'border-box',
        },
    },
});

interface AssistantCardProps {
    assistantServiceId: string;
    templateId: string;
    participantMetadata?: { [key: string]: any };
    hideContent?: boolean;
    includeAssistantIds?: string[];
    requireEnabled?: boolean;
    existingConversationId?: string;
}

export const AssistantCard: React.FC<AssistantCardProps> = (props) => {
    const { assistantServiceId, templateId, hideContent, participantMetadata, requireEnabled, existingConversationId } =
        props;
    const { isFetching: createConversationIsFetching, assistants } = useCreateConversation();
    const {
        data: assistantServices,
        isLoading: assistantServicesIsLoading,
        isError: assistantServicesIsError,
    } = useGetAssistantServiceInfosQuery({ userIds: ['me'] });
    const { navigateToConversation } = useConversationUtility();
    const { createConversation } = useCreateConversation();
    const [submitted, setSubmitted] = React.useState(false);

    const classes = useClasses();

    const createConversationWithAssistant = React.useCallback(
        (assistantId: string) => {
            return async () => {
                setSubmitted(true);
                try {
                    const { conversation } = await createConversation({
                        assistantId,
                        participantMetadata: participantMetadata,
                        existingConversationId,
                    });
                    navigateToConversation(conversation.id);
                } finally {
                    setSubmitted(false);
                }
            };
        },
        [createConversation, navigateToConversation, participantMetadata, existingConversationId],
    );

    const quickAssistantCreateButton = React.useCallback(
        (assistants: Assistant[]) => {
            if (assistants.length === 0) {
                return null;
            }

            if (assistants.length === 1) {
                return (
                    <Button
                        onClick={createConversationWithAssistant(assistants[0].id)}
                        disabled={submitted}
                        icon={<ChatAdd24Regular />}
                    ></Button>
                );
            }

            return (
                <Menu positioning="below-end">
                    <MenuTrigger disableButtonEnhancement>
                        {(triggerProps: MenuButtonProps) => (
                            <SplitButton
                                menuButton={triggerProps}
                                primaryActionButton={{
                                    onClick: createConversationWithAssistant(assistants[0].id),
                                }}
                                disabled={submitted}
                                icon={<ChatAdd24Regular />}
                            ></SplitButton>
                        )}
                    </MenuTrigger>

                    <MenuPopover>
                        <MenuList>
                            {assistants.map((assistant) => (
                                <MenuItem
                                    key={assistant.id}
                                    onClick={createConversationWithAssistant(assistant.id)}
                                    disabled={submitted}
                                >
                                    {assistant.name}
                                </MenuItem>
                            ))}
                        </MenuList>
                    </MenuPopover>
                </Menu>
            );
        },
        [createConversationWithAssistant, submitted],
    );

    const assistantInstances = React.useMemo(() => {
        if (createConversationIsFetching) {
            return [];
        }

        const matches = assistants?.filter(
            (assistant) => assistant.assistantServiceId === assistantServiceId && assistant.templateId === templateId,
        );

        if (matches && matches.length > 0) {
            return matches;
        }
        return [];
    }, [assistantServiceId, assistants, createConversationIsFetching, templateId]);

    const dashboardCard: DashboardCardConfig | undefined = React.useMemo(() => {
        if (
            assistantServicesIsLoading ||
            assistantServicesIsError ||
            !assistantServices ||
            !assistantInstances ||
            assistantInstances.length === 0
        ) {
            return undefined;
        }
        const service = assistantServices.find(
            (service) =>
                service.metadata._dashboard_card &&
                service.assistantServiceId === assistantServiceId &&
                service.metadata._dashboard_card[templateId] &&
                (!requireEnabled || service.metadata._dashboard_card[templateId].enabled),
        );

        if (!service) {
            return undefined;
        }
        const templateConfig = service.metadata._dashboard_card[templateId];
        const cardConfig = {
            templateId: templateId,
            assistantServiceId: service.assistantServiceId,
            name: service.templates.find((template) => template.id === templateId)?.name || service.assistantServiceId,
            icon: templateConfig.icon,
            backgroundColor: templateConfig.background_color,
            cardContent: {
                contentType: templateConfig.card_content.content_type,
                content: templateConfig.card_content.content,
            },
        };
        return cardConfig;
    }, [
        assistantServicesIsLoading,
        assistantServicesIsError,
        assistantServices,
        assistantInstances,
        templateId,
        assistantServiceId,
        requireEnabled,
    ]);

    if (!dashboardCard) {
        return null;
    }

    return (
        <Card className={classes.card} appearance="filled">
            <CardHeader
                image={<img src={dashboardCard.icon} alt="Assistant Icon" />}
                header={
                    <div className={classes.cardHeaderBody}>
                        <Title3>{dashboardCard.name}</Title3>

                        {quickAssistantCreateButton(assistantInstances)}
                    </div>
                }
                className={hideContent ? classes.cardHeaderNoContent : classes.cardHeader}
                style={{ backgroundColor: dashboardCard.backgroundColor }}
            ></CardHeader>
            {!hideContent && (
                <CardPreview className={classes.cardPreview}>
                    {dashboardCard.cardContent.contentType === 'text/markdown' ? (
                        <MarkdownContentRenderer content={dashboardCard.cardContent.content} />
                    ) : (
                        dashboardCard.cardContent.content
                    )}
                </CardPreview>
            )}
        </Card>
    );
};


=== File: workbench-app/src/components/FrontDoor/Controls/AssistantSelector.tsx ===
import { Dropdown, Option, OptionGroup } from '@fluentui/react-components';
import React from 'react';
import { Assistant } from '../../../models/Assistant';

interface AssistantSelectorProps {
    assistants?: Assistant[];
    defaultAssistant?: Assistant;
    onChange: (assistantId: string) => void;
    disabled?: boolean;
}

export const AssistantSelector: React.FC<AssistantSelectorProps> = (props) => {
    const { defaultAssistant, assistants, onChange, disabled } = props;
    const [emittedDefaultAssistant, setEmittedDefaultAssistant] = React.useState<boolean>(false);

    // Call onChange when defaultAssistant changes or on initial mount
    React.useEffect(() => {
        if (defaultAssistant && !emittedDefaultAssistant) {
            setEmittedDefaultAssistant(true);
            onChange(defaultAssistant.id);
        }
    }, [defaultAssistant, emittedDefaultAssistant, onChange]);

    return (
        <Dropdown
            placeholder="Select an assistant"
            disabled={disabled}
            onOptionSelect={(_event, data) => onChange(data.optionValue as string)}
            defaultSelectedOptions={defaultAssistant ? [defaultAssistant.id] : []}
            defaultValue={defaultAssistant ? defaultAssistant.name : undefined}
        >
            <OptionGroup>
                {assistants
                    ?.slice()
                    .sort((a, b) => a.name.localeCompare(b.name))
                    .map((assistant) => (
                        <Option key={assistant.id} text={assistant.name} value={assistant.id}>
                            {assistant.name}
                        </Option>
                    ))}
            </OptionGroup>
            <Option text="Create new assistant" value="new">
                Create new assistant
            </Option>
        </Dropdown>
    );
};


=== File: workbench-app/src/components/FrontDoor/Controls/AssistantServiceSelector.tsx ===
import { Divider, Dropdown, Label, makeStyles, Option, tokens, Tooltip } from '@fluentui/react-components';
import { Info16Regular, PresenceAvailableRegular } from '@fluentui/react-icons';
import React from 'react';
import { AssistantServiceTemplate } from '../../../libs/useCreateConversation';

const useClasses = makeStyles({
    option: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: tokens.spacingHorizontalXS,
    },
    optionDescription: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalXS,
    },
});

interface AssistantServiceSelectorProps {
    assistantServicesByCategory: Array<{
        category: string;
        assistantServices: AssistantServiceTemplate[];
    }>;
    onChange: (value: AssistantServiceTemplate) => void;
    disabled?: boolean;
}

export const AssistantServiceSelector: React.FC<AssistantServiceSelectorProps> = (props) => {
    const { assistantServicesByCategory, onChange, disabled } = props;
    const classes = useClasses();

    const assistantServiceOption = React.useCallback(
        (assistantService: AssistantServiceTemplate) => {
            const key = JSON.stringify([assistantService.service.assistantServiceId, assistantService.template.id]);
            return (
                <Option key={key} text={assistantService.template.name} value={key}>
                    <div className={classes.option}>
                        <PresenceAvailableRegular color="green" />
                        <Label weight="semibold">{assistantService.template.name}</Label>
                        <Tooltip
                            content={
                                <div className={classes.optionDescription}>
                                    <Label size="small">
                                        <em>{assistantService.template.description}</em>
                                    </Label>
                                    <Divider />
                                    <Label size="small">Assistant service ID:</Label>
                                    <Label size="small">{assistantService.service.assistantServiceId}</Label>
                                </div>
                            }
                            relationship="description"
                        >
                            <Info16Regular />
                        </Tooltip>
                    </div>
                </Option>
            );
        },
        [classes],
    );

    return (
        <Dropdown
            placeholder="Select an assistant service"
            disabled={disabled}
            onOptionSelect={(_event, data) => {
                const [assistantServiceId, templateId] = JSON.parse(data.optionValue as string);
                const assistantService = assistantServicesByCategory
                    .flatMap((category) => category.assistantServices)
                    .find(
                        (assistantService) =>
                            assistantService.service.assistantServiceId === assistantServiceId &&
                            assistantService.template.id === templateId,
                    );
                if (assistantService) {
                    onChange(assistantService);
                }
            }}
        >
            {assistantServicesByCategory.map(({ assistantServices }) =>
                assistantServices
                    .sort((a, b) => a.template.name.localeCompare(b.template.name))
                    .map((assistantService) => assistantServiceOption(assistantService)),
            )}
        </Dropdown>
    );
};


=== File: workbench-app/src/components/FrontDoor/Controls/ConversationItem.tsx ===
import {
    Button,
    Caption1,
    Card,
    CardHeader,
    Checkbox,
    makeStyles,
    Menu,
    MenuItem,
    MenuList,
    MenuPopover,
    MenuTrigger,
    mergeClasses,
    Text,
    tokens,
    Tooltip,
} from '@fluentui/react-components';
import {
    ArrowDownloadRegular,
    EditRegular,
    GlassesOffRegular,
    GlassesRegular,
    MoreHorizontalRegular,
    Pin12Regular,
    PinOffRegular,
    PinRegular,
    PlugDisconnectedRegular,
    SaveCopyRegular,
    ShareRegular,
} from '@fluentui/react-icons';
import React from 'react';
import { useConversationUtility } from '../../../libs/useConversationUtility';
import { Utility } from '../../../libs/Utility';
import { Conversation } from '../../../models/Conversation';
import { ConversationParticipant } from '../../../models/ConversationParticipant';
import { useAppSelector } from '../../../redux/app/hooks';
import { MemoizedParticipantAvatarGroup } from '../../Conversations/ParticipantAvatarGroup';

const useClasses = makeStyles({
    cardHeader: {
        overflow: 'hidden',

        // Required to prevent overflow of the header and description
        // to support ellipsis and text overflow handling
        '& .fui-CardHeader__header': {
            overflow: 'hidden',
        },

        '& .fui-CardHeader__description': {
            overflow: 'hidden',
        },
    },
    header: {
        display: 'flex',
        flexDirection: 'row',
        flex: 1,
        gap: tokens.spacingHorizontalXS,
        alignItems: 'center',
        justifyContent: 'space-between',
        width: '100%',
    },
    action: {
        flex: '0 0 auto',
        display: 'flex',
        flexDirection: 'column',
    },
    pin: {
        flex: '0 0 auto',
    },
    title: {
        flexGrow: 1,
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
        minWidth: 0,
    },
    date: {
        marginLeft: tokens.spacingHorizontalXS,
        flexShrink: 0,
    },
    unread: {
        color: tokens.colorStrokeFocus2,
        fontWeight: '600',
    },
    description: {
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        width: '100%',
    },
    showingActions: {
        '& .fui-CardHeader__header': {
            width: 'calc(100% - 40px)',
        },

        '& .fui-CardHeader__description': {
            width: 'calc(100% - 40px)',
        },
    },
    selectCheckbox: {
        height: '24px',
    },
    moreButton: {
        paddingTop: 0,
        paddingBottom: 0,
    },
});

interface ConversationItemProps {
    conversation: Conversation;
    owned?: boolean;
    selected?: boolean;
    showSelectForActions?: boolean;
    selectedForActions?: boolean;
    onSelect?: (conversation: Conversation) => void;
    onExport?: (conversation: Conversation) => void;
    onRename?: (conversation: Conversation) => void;
    onDuplicate?: (conversation: Conversation) => void;
    onShare?: (conversation: Conversation) => void;
    onRemove?: (conversation: Conversation) => void;
    onSelectForActions?: (conversation: Conversation, selected: boolean) => void;
}

export const ConversationItem: React.FC<ConversationItemProps> = (props) => {
    const {
        conversation,
        owned,
        selected,
        onSelect,
        onExport,
        onRename,
        onDuplicate,
        onShare,
        onRemove,
        showSelectForActions,
        selectedForActions,
        onSelectForActions,
    } = props;
    const classes = useClasses();
    const {
        getOwnerParticipant,
        wasSharedWithMe,
        hasUnreadMessages,
        isPinned,
        setPinned,
        markAllAsRead,
        markAllAsUnread,
    } = useConversationUtility();
    const localUserId = useAppSelector((state) => state.localUser.id);
    const [isHovered, setIsHovered] = React.useState(false);

    const showActions = isHovered || showSelectForActions;

    const handleMenuItemClick = React.useCallback(
        (event: React.MouseEvent<HTMLDivElement>, handler?: (conversation: Conversation) => void) => {
            event.stopPropagation();
            setIsHovered(false);
            handler?.(conversation);
        },
        [conversation],
    );

    const onPinned = React.useCallback(async () => {
        await setPinned(conversation, !isPinned(conversation));
    }, [conversation, isPinned, setPinned]);

    const action = React.useMemo(
        () => (
            <div className={classes.action}>
                <Checkbox
                    className={classes.selectCheckbox}
                    checked={selectedForActions}
                    onChange={() => onSelectForActions?.(conversation, !selectedForActions)}
                />
                <Menu key={conversation.id} positioning="below-end">
                    <MenuTrigger disableButtonEnhancement>
                        <Button
                            appearance="transparent"
                            className={classes.moreButton}
                            icon={<MoreHorizontalRegular />}
                        />
                    </MenuTrigger>
                    <MenuPopover>
                        <MenuList>
                            <MenuItem
                                icon={isPinned(conversation) ? <PinOffRegular /> : <PinRegular />}
                                onClick={(event) => handleMenuItemClick(event, onPinned)}
                            >
                                {isPinned(conversation) ? 'Unpin' : 'Pin'}
                            </MenuItem>
                            <MenuItem
                                icon={hasUnreadMessages(conversation) ? <GlassesRegular /> : <GlassesOffRegular />}
                                onClick={(event) => {
                                    const hasUnread = hasUnreadMessages(conversation);
                                    handleMenuItemClick(event, hasUnread ? markAllAsRead : markAllAsUnread);
                                }}
                            >
                                {hasUnreadMessages(conversation) ? 'Mark read' : 'Mark unread'}
                            </MenuItem>
                            {onRename && (
                                <MenuItem
                                    icon={<EditRegular />}
                                    onClick={(event) => handleMenuItemClick(event, onRename)}
                                    disabled={!owned}
                                >
                                    Rename
                                </MenuItem>
                            )}
                            <MenuItem
                                icon={<ArrowDownloadRegular />}
                                onClick={async (event) => handleMenuItemClick(event, onExport)}
                            >
                                Export
                            </MenuItem>
                            {onDuplicate && (
                                <MenuItem
                                    icon={<SaveCopyRegular />}
                                    onClick={(event) => handleMenuItemClick(event, onDuplicate)}
                                >
                                    Duplicate
                                </MenuItem>
                            )}
                            {onShare && (
                                <MenuItem
                                    icon={<ShareRegular />}
                                    onClick={(event) => handleMenuItemClick(event, onShare)}
                                >
                                    Share
                                </MenuItem>
                            )}
                            {onRemove && (
                                <MenuItem
                                    icon={<PlugDisconnectedRegular />}
                                    onClick={(event) => handleMenuItemClick(event, onRemove)}
                                    disabled={selected}
                                >
                                    {selected ? (
                                        <Tooltip
                                            content="Cannot remove currently active conversation"
                                            relationship="label"
                                        >
                                            <Text>Remove</Text>
                                        </Tooltip>
                                    ) : (
                                        'Remove'
                                    )}
                                </MenuItem>
                            )}
                        </MenuList>
                    </MenuPopover>
                </Menu>
            </div>
        ),
        [
            classes.action,
            classes.moreButton,
            classes.selectCheckbox,
            conversation,
            handleMenuItemClick,
            hasUnreadMessages,
            isPinned,
            markAllAsRead,
            markAllAsUnread,
            onDuplicate,
            onExport,
            onPinned,
            onRemove,
            onRename,
            onSelectForActions,
            onShare,
            owned,
            selected,
            selectedForActions,
        ],
    );

    const unread = hasUnreadMessages(conversation);

    const header = React.useMemo(() => {
        const formattedDate = Utility.toSimpleDateString(
            conversation.latest_message?.timestamp ?? conversation.created,
        );

        return (
            <div className={classes.header}>
                {isPinned(conversation) && (
                    <div className={classes.pin}>
                        <Pin12Regular />
                    </div>
                )}
                <Text className={classes.title} weight={unread ? 'bold' : 'regular'}>
                    {conversation.title}
                </Text>
                {!showActions && (
                    <Caption1 className={mergeClasses(classes.date, unread ? classes.unread : undefined)}>
                        {formattedDate}
                    </Caption1>
                )}
            </div>
        );
    }, [
        conversation,
        classes.header,
        classes.pin,
        classes.title,
        classes.date,
        classes.unread,
        showActions,
        isPinned,
        unread,
    ]);

    const description = React.useMemo(() => {
        if (!conversation.latest_message) {
            return undefined;
        }

        const participantId = conversation.latest_message.sender.participantId;
        const sender = conversation.participants.find((p) => p.id === participantId);
        const content = conversation.latest_message.content;

        return <Caption1 className={classes.description}>{sender ? `${sender.name}: ${content}` : content}</Caption1>;
    }, [conversation.latest_message, conversation.participants, classes.description]);

    const sortedParticipantsByOwnerMeOthers = React.useMemo(() => {
        const participants: ConversationParticipant[] = [];
        const owner = getOwnerParticipant(conversation);
        if (owner) {
            participants.push(owner);
        }
        if (wasSharedWithMe(conversation)) {
            const me = conversation.participants.find((participant) => participant.id === localUserId);
            if (me) {
                participants.push(me);
            }
        }
        const others = conversation.participants
            .filter((participant) => !participants.includes(participant))
            .filter((participant) => participant.active);
        participants.push(...others);
        return participants;
    }, [getOwnerParticipant, conversation, wasSharedWithMe, localUserId]);

    return (
        <Card
            size="small"
            appearance="subtle"
            selected={selected}
            onSelectionChange={() => onSelect?.(conversation)}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            floatingAction={showActions ? action : undefined}
        >
            <CardHeader
                className={mergeClasses(classes.cardHeader, showActions ? classes.showingActions : undefined)}
                image={<MemoizedParticipantAvatarGroup participants={sortedParticipantsByOwnerMeOthers} />}
                header={header}
                description={description}
            />
        </Card>
    );
};

export const MemoizedConversationItem = React.memo(ConversationItem, (prevProps, nextProps) =>
    Utility.deepEqual(prevProps, nextProps),
);


=== File: workbench-app/src/components/FrontDoor/Controls/ConversationList.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, shorthands, Text, tokens } from '@fluentui/react-components';

import { EventSourceMessage } from '@microsoft/fetch-event-source';
import React from 'react';
import { useConversationUtility } from '../../../libs/useConversationUtility';
import { useEnvironment } from '../../../libs/useEnvironment';
import { Conversation } from '../../../models/Conversation';
import { useAppSelector } from '../../../redux/app/hooks';
import { workbenchUserEvents } from '../../../routes/FrontDoor';
import { useGetConversationsQuery } from '../../../services/workbench';
import { Loading } from '../../App/Loading';
import { PresenceMotionList } from '../../App/PresenceMotionList';
import { ConversationDuplicateDialog } from '../../Conversations/ConversationDuplicate';
import { ConversationExportWithStatusDialog } from '../../Conversations/ConversationExport';
import { ConversationRemoveDialog } from '../../Conversations/ConversationRemove';
import { ConversationRenameDialog } from '../../Conversations/ConversationRename';
import { ConversationShareDialog } from '../../Conversations/ConversationShare';
import { MemoizedConversationItem } from './ConversationItem';
import { ConversationListOptions } from './ConversationListOptions';

const useClasses = makeStyles({
    list: {
        gap: 0,
        ...shorthands.padding(0, tokens.spacingHorizontalM, tokens.spacingVerticalM, tokens.spacingHorizontalM),
    },
    content: {
        ...shorthands.padding(0, tokens.spacingHorizontalM),
    },
});

interface ConversationListProps {
    parentConversationId?: string;
    hideChildConversations?: boolean;
}

export const ConversationList: React.FC<ConversationListProps> = (props) => {
    const { parentConversationId, hideChildConversations } = props;
    const classes = useClasses();
    const environment = useEnvironment();
    const activeConversationId = useAppSelector((state) => state.app.activeConversationId);
    const localUserId = useAppSelector((state) => state.localUser.id);
    const { navigateToConversation } = useConversationUtility();
    const {
        data: conversations,
        error: conversationsError,
        isLoading: conversationsLoading,
        isUninitialized: conversationsUninitialized,
        refetch: refetchConversations,
    } = useGetConversationsQuery();
    const [filteredConversations, setFilteredConversations] = React.useState<Conversation[]>();
    const [displayedConversations, setDisplayedConversations] = React.useState<Conversation[]>([]);

    const [renameConversation, setRenameConversation] = React.useState<Conversation>();
    const [duplicateConversation, setDuplicateConversation] = React.useState<Conversation>();
    const [exportConversation, setExportConversation] = React.useState<Conversation>();
    const [shareConversation, setShareConversation] = React.useState<Conversation>();
    const [removeConversation, setRemoveConversation] = React.useState<Conversation>();
    const [selectedForActions, setSelectedForActions] = React.useState(new Set<string>());

    if (conversationsError) {
        const errorMessage = JSON.stringify(conversationsError);
        throw new Error(`Error loading conversations: ${errorMessage}`);
    }

    React.useEffect(() => {
        if (conversationsLoading) {
            return;
        }

        // handle new message events
        const conversationHandler = async (_event: EventSourceMessage) => {
            if (conversationsUninitialized) {
                // do not refetch conversations if it's the first time loading
                return;
            }

            // refetch conversations to update the latest message
            await refetchConversations();
        };

        workbenchUserEvents.addEventListener('message.created', conversationHandler);
        workbenchUserEvents.addEventListener('message.deleted', conversationHandler);
        workbenchUserEvents.addEventListener('conversation.updated', conversationHandler);
        workbenchUserEvents.addEventListener('participant.created', conversationHandler);
        workbenchUserEvents.addEventListener('participant.updated', conversationHandler);

        return () => {
            // remove event listeners
            workbenchUserEvents.removeEventListener('message.created', conversationHandler);
            workbenchUserEvents.removeEventListener('message.deleted', conversationHandler);
            workbenchUserEvents.removeEventListener('conversation.updated', conversationHandler);
            workbenchUserEvents.removeEventListener('participant.created', conversationHandler);
            workbenchUserEvents.removeEventListener('participant.updated', conversationHandler);
        };
    }, [conversationsLoading, conversationsUninitialized, environment.url, refetchConversations]);

    React.useEffect(() => {
        if (conversationsLoading) {
            return;
        }

        setFilteredConversations(
            conversations?.filter((conversation) => {
                if (parentConversationId) {
                    if (hideChildConversations) {
                        return (
                            conversation.metadata?.['parent_conversation_id'] === undefined ||
                            conversation.metadata?.['parent_conversation_id'] !== parentConversationId
                        );
                    }
                    return conversation.metadata?.['parent_conversation_id'] === parentConversationId;
                }
                if (hideChildConversations) {
                    return conversation.metadata?.['parent_conversation_id'] === undefined;
                }
                return true;
            }),
        );
    }, [conversations, conversationsLoading, hideChildConversations, parentConversationId]);

    const handleUpdateSelectedForActions = React.useCallback((conversationId: string, selected: boolean) => {
        if (selected) {
            setSelectedForActions((prev) => new Set(prev).add(conversationId));
        } else {
            setSelectedForActions((prev) => {
                const newSet = new Set(prev);
                newSet.delete(conversationId);
                return newSet;
            });
        }
    }, []);

    const handleItemSelect = React.useCallback(
        (conversation: Conversation) => {
            navigateToConversation(conversation.id);
        },
        [navigateToConversation],
    );

    const handleItemSelectForActions = React.useCallback(
        (conversation: Conversation, selected: boolean) => {
            handleUpdateSelectedForActions(conversation.id, selected);
        },
        [handleUpdateSelectedForActions],
    );

    const handleDuplicateConversationComplete = React.useCallback(
        async (id: string) => {
            navigateToConversation(id);
            setDuplicateConversation(undefined);
        },
        [navigateToConversation],
    );

    const actionHelpers = React.useMemo(
        () => (
            <>
                <ConversationRenameDialog
                    conversationId={renameConversation?.id ?? ''}
                    value={renameConversation?.title ?? ''}
                    open={renameConversation !== undefined}
                    onOpenChange={() => setRenameConversation(undefined)}
                    onRename={async () => setRenameConversation(undefined)}
                />
                <ConversationDuplicateDialog
                    conversationId={duplicateConversation?.id ?? ''}
                    open={duplicateConversation !== undefined}
                    onOpenChange={() => setDuplicateConversation(undefined)}
                    onDuplicate={handleDuplicateConversationComplete}
                />
                <ConversationExportWithStatusDialog
                    conversationId={exportConversation?.id}
                    onExport={async () => setExportConversation(undefined)}
                />
                {shareConversation && (
                    <ConversationShareDialog
                        conversation={shareConversation}
                        onClose={() => setShareConversation(undefined)}
                    />
                )}
                {removeConversation && localUserId && (
                    <ConversationRemoveDialog
                        conversations={removeConversation}
                        participantId={localUserId}
                        onRemove={() => {
                            if (activeConversationId === removeConversation.id) {
                                navigateToConversation(undefined);
                            }
                            setRemoveConversation(undefined);
                        }}
                        onCancel={() => setRemoveConversation(undefined)}
                    />
                )}
            </>
        ),
        [
            renameConversation,
            duplicateConversation,
            handleDuplicateConversationComplete,
            exportConversation,
            shareConversation,
            removeConversation,
            localUserId,
            activeConversationId,
            navigateToConversation,
        ],
    );

    if (conversationsLoading) {
        return <Loading />;
    }

    return (
        <>
            {actionHelpers}
            <ConversationListOptions
                conversations={filteredConversations}
                selectedForActions={selectedForActions}
                onSelectedForActionsChanged={setSelectedForActions}
                onDisplayedConversationsChanged={setDisplayedConversations}
            />
            {!filteredConversations || filteredConversations.length === 0 ? (
                <div className={classes.content}>
                    <Text weight="semibold">No conversations found</Text>
                </div>
            ) : (
                <PresenceMotionList
                    className={classes.list}
                    items={displayedConversations.map((conversation) => (
                        // Use the individual memoized conversation item instead of the list
                        // to prevent re-rendering all items when one item changes
                        <MemoizedConversationItem
                            key={conversation.id}
                            conversation={conversation}
                            owned={conversation.ownerId === localUserId}
                            selected={activeConversationId === conversation.id}
                            selectedForActions={selectedForActions?.has(conversation.id)}
                            onSelect={handleItemSelect}
                            showSelectForActions={selectedForActions.size > 0}
                            onSelectForActions={handleItemSelectForActions}
                            onRename={setRenameConversation}
                            onDuplicate={setDuplicateConversation}
                            onExport={setExportConversation}
                            onShare={setShareConversation}
                            onRemove={setRemoveConversation}
                        />
                    ))}
                />
            )}
        </>
    );
};


=== File: workbench-app/src/components/FrontDoor/Controls/ConversationListOptions.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Input,
    Label,
    makeStyles,
    Menu,
    MenuButtonProps,
    MenuItem,
    MenuList,
    MenuPopover,
    MenuTrigger,
    Overflow,
    Select,
    shorthands,
    SplitButton,
    Text,
    tokens,
    Toolbar,
} from '@fluentui/react-components';
import {
    CheckboxCheckedFilled,
    CheckboxIndeterminateRegular,
    CheckboxUncheckedRegular,
    DismissRegular,
    FilterRegular,
    GlassesOffRegular,
    GlassesRegular,
    PinOffRegular,
    PinRegular,
    PlugDisconnectedRegular,
} from '@fluentui/react-icons';

import React from 'react';
import { useConversationUtility } from '../../../libs/useConversationUtility';
import { Utility } from '../../../libs/Utility';
import { Conversation } from '../../../models/Conversation';
import { useAppSelector } from '../../../redux/app/hooks';
import { TooltipWrapper } from '../../App/TooltipWrapper';
import { ConversationRemoveDialog } from '../../Conversations/ConversationRemove';

const useClasses = makeStyles({
    root: {
        position: 'sticky',
        top: 0,
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalS,
        zIndex: tokens.zIndexPriority,
        backgroundColor: tokens.colorNeutralBackground2,
        ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
    },
    header: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    displayOptions: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'space-between',
        gap: tokens.spacingHorizontalS,
    },
    displayOption: {
        display: 'flex',
        flexDirection: 'row',
        gap: tokens.spacingHorizontalXS,
        alignItems: 'center',
    },
    bulkActions: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
    },
    bulkActionsLabel: {
        marginLeft: tokens.spacingHorizontalM,
        color: tokens.colorNeutralForeground2,
    },
    toolbarTextButton: {
        minWidth: 'auto',
        paddingLeft: tokens.spacingHorizontalXS,
        paddingRight: tokens.spacingHorizontalXS,
    },
});

interface ConversationListOptionsProps {
    conversations?: Conversation[];
    selectedForActions: Set<string>;
    onSelectedForActionsChanged: (selected: Set<string>) => void;
    onDisplayedConversationsChanged: (conversations: Conversation[]) => void;
}

export const ConversationListOptions: React.FC<ConversationListOptionsProps> = (props) => {
    const { conversations, selectedForActions, onSelectedForActionsChanged, onDisplayedConversationsChanged } = props;
    const classes = useClasses();
    const localUserId = useAppSelector((state) => state.localUser.id);
    const { hasUnreadMessages, markAllAsRead, markAllAsUnread, isPinned, setPinned } = useConversationUtility();
    const [filterString, setFilterString] = React.useState<string>('');
    const [displayFilter, setDisplayFilter] = React.useState<string>('');
    const [sortByName, setSortByName] = React.useState<boolean>(false);
    const [removeConversations, setRemoveConversations] = React.useState<Conversation[]>();
    const [displayedConversations, setDisplayedConversations] = React.useState<Conversation[]>(conversations || []);

    const sortByNameHelper = React.useCallback(
        (a: Conversation, b: Conversation) => a.title.localeCompare(b.title),
        [],
    );

    const sortByDateHelper = React.useCallback((a: Conversation, b: Conversation) => {
        const dateA = a.latest_message ? Utility.toDate(a.latest_message.timestamp) : Utility.toDate(a.created);
        const dateB = b.latest_message ? Utility.toDate(b.latest_message.timestamp) : Utility.toDate(b.created);
        return dateB.getTime() - dateA.getTime();
    }, []);

    // update displayed conversations when conversations or options change
    React.useEffect(() => {
        // filter conversations based on display filter and filter string
        const filteredConversations =
            conversations?.filter((conversation) => {
                switch (displayFilter) {
                    case 'Unread':
                        if (!hasUnreadMessages(conversation)) {
                            return false;
                        }
                        break;
                    case 'Pinned':
                        if (!isPinned(conversation)) {
                            return false;
                        }
                        break;
                    case 'Mine':
                        if (conversation.ownerId !== localUserId) {
                            return false;
                        }
                        break;
                    case 'Shared with me':
                        if (conversation.ownerId === localUserId) {
                            return false;
                        }
                        break;
                    default:
                        break;
                }

                return (
                    !filterString ||
                    (filterString && conversation.title.toLowerCase().includes(filterString.toLowerCase()))
                );
            }) || [];

        // split conversations into pinned and unpinned
        const splitByPinned: Record<string, Conversation[]> = { pinned: [], unpinned: [] };
        filteredConversations.forEach((conversation) => {
            if (isPinned(conversation)) {
                splitByPinned.pinned.push(conversation);
            } else {
                splitByPinned.unpinned.push(conversation);
            }
        });

        const sortedConversations: Conversation[] = [];
        const sortHelperForSortType = sortByName ? sortByNameHelper : sortByDateHelper;

        // sort pinned conversations
        sortedConversations.push(...splitByPinned.pinned.sort(sortHelperForSortType));
        // sort unpinned conversations
        sortedConversations.push(...splitByPinned.unpinned.sort(sortHelperForSortType));

        setDisplayedConversations(sortedConversations);
        onDisplayedConversationsChanged(sortedConversations);
    }, [
        conversations,
        displayFilter,
        filterString,
        hasUnreadMessages,
        isPinned,
        onDisplayedConversationsChanged,
        sortByName,
        sortByNameHelper,
        sortByDateHelper,
        localUserId,
    ]);

    const bulkSelectForActionsIcon = React.useMemo(() => {
        const icons = {
            all: <CheckboxCheckedFilled color={tokens.colorCompoundBrandBackground} />,
            some: <CheckboxIndeterminateRegular color={tokens.colorCompoundBrandBackground} />,
            none: <CheckboxUncheckedRegular />,
        };

        if (selectedForActions.size === 0) {
            return icons.none;
        } else if (selectedForActions.size === displayedConversations.length) {
            return icons.all;
        } else {
            return icons.some;
        }
    }, [displayedConversations, selectedForActions]);

    const handleBulkSelectForActions = React.useCallback(
        (selectionType?: 'all' | 'none' | 'read' | 'unread' | 'pinned' | 'unpinned' | 'mine' | 'sharedWithMe') => {
            switch (selectionType) {
                case 'all':
                    onSelectedForActionsChanged(new Set(displayedConversations.map((conversation) => conversation.id)));
                    break;
                case 'none':
                    onSelectedForActionsChanged(new Set<string>());
                    break;
                case 'read':
                    onSelectedForActionsChanged(
                        new Set(
                            displayedConversations
                                .filter((conversation) => !hasUnreadMessages(conversation))
                                .map((conversation) => conversation.id),
                        ),
                    );
                    break;
                case 'unread':
                    onSelectedForActionsChanged(
                        new Set(
                            displayedConversations
                                .filter((conversation) => hasUnreadMessages(conversation))
                                .map((conversation) => conversation.id),
                        ),
                    );
                    break;
                case 'pinned':
                    onSelectedForActionsChanged(
                        new Set(
                            displayedConversations
                                .filter((conversation) => isPinned(conversation))
                                .map((conversation) => conversation.id),
                        ),
                    );
                    break;
                case 'unpinned':
                    onSelectedForActionsChanged(
                        new Set(
                            displayedConversations
                                .filter((conversation) => !isPinned(conversation))
                                .map((conversation) => conversation.id),
                        ),
                    );
                    break;
                case 'mine':
                    onSelectedForActionsChanged(
                        new Set(
                            displayedConversations
                                .filter((conversation) => conversation.ownerId === localUserId)
                                .map((conversation) => conversation.id),
                        ),
                    );
                    break;
                case 'sharedWithMe':
                    onSelectedForActionsChanged(
                        new Set(
                            displayedConversations
                                .filter((conversation) => conversation.ownerId !== localUserId)
                                .map((conversation) => conversation.id),
                        ),
                    );
                    break;
                default:
                    // handle toggle all
                    if (selectedForActions.size > 0) {
                        // deselect all
                        onSelectedForActionsChanged(new Set<string>());
                    } else {
                        // select all
                        onSelectedForActionsChanged(
                            new Set(displayedConversations.map((conversation) => conversation.id)),
                        );
                    }
                    break;
            }
        },
        [
            localUserId,
            onSelectedForActionsChanged,
            displayedConversations,
            selectedForActions.size,
            hasUnreadMessages,
            isPinned,
        ],
    );

    const bulkSelectForActionsButton = React.useMemo(
        () => (
            <Menu positioning="below-end">
                <MenuTrigger disableButtonEnhancement>
                    {(triggerProps: MenuButtonProps) => (
                        <SplitButton
                            appearance="outline"
                            size="small"
                            menuButton={triggerProps}
                            primaryActionButton={{
                                onClick: () => handleBulkSelectForActions(),
                            }}
                            icon={bulkSelectForActionsIcon}
                        />
                    )}
                </MenuTrigger>
                <MenuPopover>
                    <MenuList>
                        <MenuItem
                            onClick={() => handleBulkSelectForActions('all')}
                            disabled={selectedForActions.size === displayedConversations.length}
                        >
                            All
                        </MenuItem>
                        <MenuItem
                            onClick={() => handleBulkSelectForActions('none')}
                            disabled={selectedForActions.size === 0}
                        >
                            None
                        </MenuItem>
                        <MenuItem
                            onClick={() => handleBulkSelectForActions('read')}
                            disabled={!displayedConversations.some((conversation) => !hasUnreadMessages(conversation))}
                        >
                            Read
                        </MenuItem>
                        <MenuItem
                            onClick={() => handleBulkSelectForActions('unread')}
                            disabled={!displayedConversations.some(hasUnreadMessages)}
                        >
                            Unread
                        </MenuItem>
                        <MenuItem
                            onClick={() => handleBulkSelectForActions('pinned')}
                            disabled={!displayedConversations.some(isPinned)}
                        >
                            Pinned
                        </MenuItem>
                        <MenuItem
                            onClick={() => handleBulkSelectForActions('unpinned')}
                            disabled={!displayedConversations.some((conversation) => !isPinned(conversation))}
                        >
                            Unpinned
                        </MenuItem>
                        <MenuItem
                            onClick={() => handleBulkSelectForActions('mine')}
                            disabled={
                                !displayedConversations.some((conversation) => conversation.ownerId === localUserId)
                            }
                        >
                            Mine
                        </MenuItem>
                        <MenuItem
                            onClick={() => handleBulkSelectForActions('sharedWithMe')}
                            disabled={
                                !displayedConversations.some((conversation) => conversation.ownerId !== localUserId)
                            }
                        >
                            Shared with me
                        </MenuItem>
                    </MenuList>
                </MenuPopover>
            </Menu>
        ),
        [
            localUserId,
            bulkSelectForActionsIcon,
            displayedConversations,
            handleBulkSelectForActions,
            hasUnreadMessages,
            isPinned,
            selectedForActions.size,
        ],
    );

    const enableBulkActions = React.useMemo(
        () =>
            selectedForActions.size > 0
                ? {
                      read: conversations?.some(
                          (conversation) => selectedForActions.has(conversation.id) && hasUnreadMessages(conversation),
                      ),
                      unread: conversations?.some(
                          (conversation) => selectedForActions.has(conversation.id) && !hasUnreadMessages(conversation),
                      ),
                      pin: conversations?.some(
                          (conversation) => selectedForActions.has(conversation.id) && !isPinned(conversation),
                      ),
                      unpin: conversations?.some(
                          (conversation) => selectedForActions.has(conversation.id) && isPinned(conversation),
                      ),
                      remove: true,
                  }
                : {
                      read: false,
                      unread: false,
                      pin: false,
                      unpin: false,
                      remove: false,
                  },
        [conversations, hasUnreadMessages, isPinned, selectedForActions],
    );

    const getSelectedConversations = React.useCallback(() => {
        return conversations?.filter((conversation) => selectedForActions.has(conversation.id)) ?? [];
    }, [conversations, selectedForActions]);

    const handleMarkAllAsReadForSelected = React.useCallback(async () => {
        await markAllAsRead(getSelectedConversations());
        onSelectedForActionsChanged(new Set<string>());
    }, [getSelectedConversations, markAllAsRead, onSelectedForActionsChanged]);

    const handleMarkAsUnreadForSelected = React.useCallback(async () => {
        await markAllAsUnread(getSelectedConversations());
        onSelectedForActionsChanged(new Set<string>());
    }, [getSelectedConversations, markAllAsUnread, onSelectedForActionsChanged]);

    const handleRemoveForSelected = React.useCallback(async () => {
        // set removeConversations to show remove dialog
        setRemoveConversations(getSelectedConversations());
        // don't clear selected conversations until after the user confirms the removal
    }, [getSelectedConversations]);

    const handlePinForSelected = React.useCallback(async () => {
        await setPinned(getSelectedConversations(), true);
        onSelectedForActionsChanged(new Set<string>());
    }, [getSelectedConversations, setPinned, onSelectedForActionsChanged]);

    const handleUnpinForSelected = React.useCallback(async () => {
        await setPinned(getSelectedConversations(), false);
        onSelectedForActionsChanged(new Set<string>());
    }, [getSelectedConversations, setPinned, onSelectedForActionsChanged]);

    const handleRemoveConversations = React.useCallback(() => {
        // reset removeConversations and clear selected conversations
        setRemoveConversations(undefined);
        onSelectedForActionsChanged(new Set<string>());
    }, [onSelectedForActionsChanged]);

    const bulkSelectForActionsToolbar = React.useMemo(
        () => (
            <Overflow padding={90}>
                <Toolbar size="small">
                    <TooltipWrapper
                        content={
                            !enableBulkActions.read
                                ? 'Select conversation(s) to enable'
                                : 'Mark selected conversations as read'
                        }
                    >
                        <Button
                            className={classes.toolbarTextButton}
                            appearance="transparent"
                            icon={<GlassesRegular />}
                            disabled={!enableBulkActions.read}
                            onClick={handleMarkAllAsReadForSelected}
                        />
                    </TooltipWrapper>
                    <TooltipWrapper
                        content={
                            !enableBulkActions.unread
                                ? 'Select conversation(s) to enable'
                                : 'Mark selected conversations as unread'
                        }
                    >
                        <Button
                            appearance="transparent"
                            icon={<GlassesOffRegular />}
                            disabled={!enableBulkActions.unread}
                            onClick={handleMarkAsUnreadForSelected}
                        />
                    </TooltipWrapper>
                    <TooltipWrapper
                        content={
                            !enableBulkActions.remove
                                ? 'Select conversation(s) to enable'
                                : 'Remove selected conversations'
                        }
                    >
                        <Button
                            // hide this until implemented
                            style={{ display: 'none' }}
                            appearance="subtle"
                            icon={<PlugDisconnectedRegular />}
                            disabled={!enableBulkActions.remove}
                            onClick={handleRemoveForSelected}
                        />
                    </TooltipWrapper>
                    <TooltipWrapper
                        content={
                            !enableBulkActions.pin ? 'Select conversation(s) to enable' : 'Pin selected conversations'
                        }
                    >
                        <Button
                            appearance="subtle"
                            icon={<PinRegular />}
                            disabled={!enableBulkActions.pin}
                            onClick={handlePinForSelected}
                        />
                    </TooltipWrapper>
                    <TooltipWrapper
                        content={
                            !enableBulkActions.unpin
                                ? 'Select conversation(s) to enable'
                                : 'Unpin selected conversations'
                        }
                    >
                        <Button
                            appearance="subtle"
                            icon={<PinOffRegular />}
                            disabled={!enableBulkActions.unpin}
                            onClick={handleUnpinForSelected}
                        />
                    </TooltipWrapper>
                    <TooltipWrapper
                        content={
                            !enableBulkActions.remove
                                ? 'Select conversation(s) to enable'
                                : 'Remove selected conversations'
                        }
                    >
                        <Button
                            appearance="subtle"
                            icon={<PlugDisconnectedRegular />}
                            disabled={!enableBulkActions.remove}
                            onClick={handleRemoveForSelected}
                        />
                    </TooltipWrapper>
                </Toolbar>
            </Overflow>
        ),
        [
            classes.toolbarTextButton,
            enableBulkActions.pin,
            enableBulkActions.read,
            enableBulkActions.remove,
            enableBulkActions.unpin,
            enableBulkActions.unread,
            handleMarkAllAsReadForSelected,
            handleMarkAsUnreadForSelected,
            handlePinForSelected,
            handleRemoveForSelected,
            handleUnpinForSelected,
        ],
    );

    return (
        <div className={classes.root}>
            {removeConversations && localUserId && (
                <ConversationRemoveDialog
                    conversations={removeConversations}
                    participantId={localUserId}
                    onRemove={handleRemoveConversations}
                    onCancel={() => setRemoveConversations(undefined)}
                />
            )}
            <div className={classes.header}>
                <Text weight="semibold">Conversations</Text>
            </div>
            <Input
                contentBefore={<FilterRegular />}
                contentAfter={
                    filterString && (
                        <Button
                            icon={<DismissRegular />}
                            appearance="transparent"
                            onClick={() => setFilterString('')}
                        />
                    )
                }
                placeholder="Filter"
                value={filterString}
                onChange={(_event, data) => setFilterString(data.value)}
            />
            <div className={classes.displayOptions}>
                <Select
                    size="small"
                    defaultValue={sortByName ? 'Sort by name' : 'Sort by date'}
                    onChange={(_event, data) => setSortByName(data.value === 'Sort by name')}
                >
                    <option>Sort by name</option>
                    <option>Sort by date</option>
                </Select>
                <div className={classes.displayOption}>
                    <Label size="small">Show</Label>
                    <Select size="small" defaultValue="All" onChange={(_event, data) => setDisplayFilter(data.value)}>
                        <option>All</option>
                        <option disabled={conversations?.every((conversation) => !hasUnreadMessages(conversation))}>
                            Unread
                        </option>
                        <option disabled={conversations?.every((conversation) => !isPinned(conversation))}>
                            Pinned
                        </option>
                        <option disabled={conversations?.every((conversation) => conversation.ownerId !== localUserId)}>
                            Mine
                        </option>
                        <option disabled={conversations?.every((conversation) => conversation.ownerId === localUserId)}>
                            Shared with me
                        </option>
                    </Select>
                </div>
            </div>
            <div className={classes.bulkActions}>
                {bulkSelectForActionsButton}
                <Label className={classes.bulkActionsLabel} size="small">
                    Actions
                </Label>
                {bulkSelectForActionsToolbar}
            </div>
        </div>
    );
};


=== File: workbench-app/src/components/FrontDoor/Controls/NewConversationButton.tsx ===
import { Button, DialogTrigger } from '@fluentui/react-components';
import { ChatAddRegular, NavigationRegular } from '@fluentui/react-icons';
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useConversationUtility } from '../../../libs/useConversationUtility';
import { useCreateConversation } from '../../../libs/useCreateConversation';
import { useNotify } from '../../../libs/useNotify';
import { DialogControl } from '../../App/DialogControl';
import { ConversationsImport } from '../../Conversations/ConversationsImport';
import { NewConversationForm } from './NewConversationForm';

export const NewConversationButton: React.FC = () => {
    const [open, setOpen] = React.useState(false);
    const { createConversation } = useCreateConversation();
    const [isValid, setIsValid] = React.useState(false);
    const [assistantId, setAssistantId] = React.useState<string>();
    const [name, setName] = React.useState<string>();
    const [assistantServiceId, setAssistantServiceId] = React.useState<string>();
    const [templateId, setTemplateId] = React.useState<string>();
    const [submitted, setSubmitted] = React.useState(false);
    const { navigateToConversation } = useConversationUtility();
    const { notifyError } = useNotify();
    const navigate = useNavigate();

    const handleCreate = React.useCallback(async () => {
        if (submitted || !isValid || !assistantId) {
            return;
        }

        // ensure we have a valid assistant info
        let assistantInfo:
            | { assistantId: string }
            | { name: string; assistantServiceId: string; templateId: string }
            | undefined;
        if (assistantId === 'new' && name && assistantServiceId && templateId) {
            assistantInfo = { name, assistantServiceId, templateId };
        } else {
            assistantInfo = { assistantId };
        }

        if (!assistantInfo) {
            return;
        }
        setSubmitted(true);

        try {
            const { conversation } = await createConversation(assistantInfo);
            navigateToConversation(conversation.id);
        } finally {
            // In case of error, allow user to retry
            setSubmitted(false);
        }

        setOpen(false);
    }, [
        assistantId,
        assistantServiceId,
        createConversation,
        isValid,
        name,
        navigateToConversation,
        submitted,
        templateId,
    ]);

    const handleImport = React.useCallback(
        (conversationIds: string[]) => {
            if (conversationIds.length > 0) {
                navigateToConversation(conversationIds[0]);
            }
            setOpen(false);
        },
        [navigateToConversation],
    );

    const handleError = React.useCallback(
        (error: Error) =>
            notifyError({
                id: 'new-conversation-error',
                title: 'Error creating conversation',
                message: error.message,
            }),
        [notifyError],
    );

    return (
        <DialogControl
            open={open}
            onOpenChange={() => setOpen(!open)}
            trigger={<Button icon={<ChatAddRegular />} />}
            title="New Conversation with Assistant"
            content={
                <NewConversationForm
                    onSubmit={handleCreate}
                    onChange={(isValid, data) => {
                        setIsValid(isValid);
                        setAssistantId(data.assistantId);
                        setAssistantServiceId(data.assistantServiceId);
                        setTemplateId(data.templateId);
                        setName(data.name);
                    }}
                    disabled={submitted}
                />
            }
            hideDismissButton
            additionalActions={[
                <Button
                    key="home"
                    icon={<NavigationRegular />}
                    onClick={() => {
                        setOpen(false);
                        navigate('/');
                    }}
                    appearance="subtle"
                    autoFocus={false}
                >
                    View assistant descriptions
                </Button>,
                <ConversationsImport
                    key="import"
                    appearance="outline"
                    onImport={handleImport}
                    onError={handleError}
                    disabled={submitted}
                />,
                <DialogTrigger key="cancel" disableButtonEnhancement>
                    <Button appearance="secondary" disabled={submitted}>
                        Cancel
                    </Button>
                </DialogTrigger>,
                <Button
                    key="create"
                    appearance="primary"
                    onClick={handleCreate}
                    disabled={!isValid || submitted}
                    autoFocus
                >
                    {submitted ? 'Creating...' : 'Create'}
                </Button>,
            ]}
        />
    );
};


=== File: workbench-app/src/components/FrontDoor/Controls/NewConversationForm.tsx ===
import { Checkbox, Field, Input, makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { AssistantServiceTemplate, useCreateConversation } from '../../../libs/useCreateConversation';
import { AssistantSelector } from './AssistantSelector';
import { AssistantServiceSelector } from './AssistantServiceSelector';

const useClasses = makeStyles({
    content: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
    serviceOptions: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'space-between',
    },
    actions: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'end',
        alignItems: 'center',
        gap: tokens.spacingHorizontalM,
    },
});

export interface NewConversationData {
    assistantId?: string;
    assistantServiceId?: string;
    templateId?: string;
    name?: string;
}

interface NewConversationFormProps {
    onSubmit?: () => void;
    onChange?: (isValid: boolean, data: NewConversationData) => void;
    disabled?: boolean;
    assistantFieldLabel?: string;
}

export const NewConversationForm: React.FC<NewConversationFormProps> = (props) => {
    const { onSubmit, onChange, disabled, assistantFieldLabel = 'Assistant' } = props;
    const classes = useClasses();
    const {
        isFetching: createConversationIsFetching,
        assistants,
        assistantServicesByCategories,
    } = useCreateConversation();

    const [config, setConfig] = React.useState<NewConversationData>({
        assistantId: '',
        assistantServiceId: '',
        name: '',
    });
    const [manualEntry, setManualEntry] = React.useState(false);

    const checkIsValid = React.useCallback((data: NewConversationData) => {
        if (!data.assistantId) {
            return false;
        }

        if (data.assistantId === 'new') {
            if (!data.assistantServiceId || !data.name || !data.templateId) {
                return false;
            }
        }

        return true;
    }, []);

    const isValid = React.useMemo(() => checkIsValid(config), [checkIsValid, config]);

    const updateAndNotifyChange = React.useCallback(
        (data: NewConversationData) => {
            const updatedConfig = { ...config, ...data };
            if (data.assistantId === 'new') {
                updatedConfig.assistantServiceId = data.assistantServiceId ?? '';
                updatedConfig.name = data.name ?? '';
                updatedConfig.templateId = data.templateId ?? '';
            }

            setConfig(updatedConfig);
            onChange?.(checkIsValid(updatedConfig), updatedConfig);
        },
        [checkIsValid, config, onChange],
    );

    return (
        <form
            onSubmit={(event) => {
                event.preventDefault();
                if (isValid) {
                    onSubmit?.();
                }
            }}
        >
            <div className={classes.content}>
                <Field label={assistantFieldLabel}>
                    {createConversationIsFetching ? (
                        <Input disabled={true} value="Loading..." />
                    ) : (
                        <AssistantSelector
                            assistants={assistants}
                            defaultAssistant={assistants?.[0]}
                            onChange={(assistantId) =>
                                updateAndNotifyChange({
                                    assistantId,
                                    assistantServiceId: assistantId === 'new' ? '' : undefined,
                                    name: assistantId === 'new' ? '' : undefined,
                                })
                            }
                            disabled={disabled}
                        />
                    )}
                </Field>
                {config.assistantId === 'new' && (
                    <>
                        {!manualEntry && (
                            <Field label="Assistant Service">
                                <AssistantServiceSelector
                                    disabled={disabled}
                                    assistantServicesByCategory={assistantServicesByCategories}
                                    onChange={(assistantService: AssistantServiceTemplate) =>
                                        updateAndNotifyChange({
                                            assistantServiceId: assistantService.service.assistantServiceId,
                                            name: assistantService.template.name,
                                            templateId: assistantService.template.id,
                                        })
                                    }
                                />
                            </Field>
                        )}
                        {manualEntry && (
                            <Field label="Assistant Service ID">
                                <Input
                                    disabled={disabled}
                                    value={config.assistantServiceId}
                                    onChange={(_event, data) =>
                                        updateAndNotifyChange({ assistantServiceId: data?.value })
                                    }
                                    aria-autocomplete="none"
                                />
                            </Field>
                        )}
                        <Field label="Name">
                            <Input
                                disabled={disabled}
                                value={config.name}
                                onChange={(_event, data) => updateAndNotifyChange({ name: data?.value })}
                                aria-autocomplete="none"
                            />
                        </Field>
                        <div className={classes.serviceOptions}>
                            <Checkbox
                                disabled={disabled}
                                style={{ whiteSpace: 'nowrap' }}
                                label="Enter Assistant Service ID"
                                checked={manualEntry}
                                onChange={(_event, data) => {
                                    setManualEntry(data.checked === true);
                                }}
                            />
                        </div>
                    </>
                )}
                <button disabled={disabled} type="submit" hidden />
            </div>
        </form>
    );
};


=== File: workbench-app/src/components/FrontDoor/Controls/SiteMenuButton.tsx ===
import { useAccount, useIsAuthenticated, useMsal } from '@azure/msal-react';
import {
    Caption1,
    Label,
    Menu,
    MenuDivider,
    MenuItem,
    MenuList,
    MenuPopover,
    MenuTrigger,
    Persona,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import {
    ArrowEnterRegular,
    ArrowExitRegular,
    NavigationRegular,
    OpenRegular,
    SettingsRegular,
    ShareRegular,
} from '@fluentui/react-icons';
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthHelper } from '../../../libs/AuthHelper';
import { useMicrosoftGraph } from '../../../libs/useMicrosoftGraph';
import { useAppDispatch, useAppSelector } from '../../../redux/app/hooks';
import { setLocalUser } from '../../../redux/features/localUser/localUserSlice';

const useClasses = makeStyles({
    accountInfo: {
        display: 'flex',
        flexDirection: 'column',
        ...shorthands.padding(tokens.spacingHorizontalS),
    },
});

export const SiteMenuButton: React.FC = () => {
    const classes = useClasses();
    const navigate = useNavigate();
    const { instance } = useMsal();
    const isAuthenticated = useIsAuthenticated();
    const account = useAccount();
    const microsoftGraph = useMicrosoftGraph();
    const localUserState = useAppSelector((state) => state.localUser);
    const dispatch = useAppDispatch();

    React.useEffect(() => {
        (async () => {
            if (!isAuthenticated || !account?.name || localUserState.id) {
                return;
            }

            const photo = await microsoftGraph.getMyPhotoAsync();

            dispatch(
                setLocalUser({
                    id: (account.homeAccountId || '').split('.').reverse().join('.'),
                    name: account.name,
                    email: account.username,
                    avatar: {
                        name: account.name,
                        image: photo ? { src: photo } : undefined,
                    },
                }),
            );
        })();
    }, [account, dispatch, isAuthenticated, localUserState.id, microsoftGraph]);

    const handleSignOut = () => {
        void AuthHelper.logoutAsync(instance);
    };

    const handleSignIn = () => {
        void AuthHelper.loginAsync(instance);
    };

    return (
        <Menu>
            <MenuTrigger disableButtonEnhancement>
                <Persona className="user-avatar" avatar={localUserState.avatar} presence={{ status: 'available' }} />
            </MenuTrigger>
            <MenuPopover>
                <MenuList>
                    {isAuthenticated && (
                        <>
                            <div className={classes.accountInfo}>
                                <Label>{localUserState.name}</Label>
                                <Label size="small">{localUserState.email ?? ''}</Label>
                            </div>
                            <MenuDivider />
                        </>
                    )}
                    <MenuItem
                        icon={<NavigationRegular />}
                        onClick={() => {
                            navigate('/dashboard');
                        }}
                    >
                        Dashboard
                    </MenuItem>
                    <MenuItem
                        icon={<ShareRegular />}
                        onClick={() => {
                            navigate('/shares');
                        }}
                    >
                        Shares
                    </MenuItem>
                    <MenuItem
                        icon={<SettingsRegular />}
                        onClick={() => {
                            navigate('/settings');
                        }}
                    >
                        Settings
                    </MenuItem>
                    <MenuDivider />
                    <MenuItem
                        icon={<OpenRegular />}
                        onClick={() => window.open('https://go.microsoft.com/fwlink/?LinkId=521839')}
                    >
                        {' '}
                        Privacy &amp; Cookies
                    </MenuItem>
                    <MenuItem
                        icon={<OpenRegular />}
                        onClick={() => window.open('https://go.microsoft.com/fwlink/?linkid=2259814')}
                    >
                        {' '}
                        Consumer Health Privacy
                    </MenuItem>
                    <MenuItem
                        icon={<OpenRegular />}
                        onClick={() => window.open('https://go.microsoft.com/fwlink/?LinkID=246338')}
                    >
                        {' '}
                        Terms of Use
                    </MenuItem>
                    <MenuItem
                        icon={<OpenRegular />}
                        onClick={() =>
                            window.open(
                                'https://www.microsoft.com/en-us/legal/intellectualproperty/Trademarks/EN-US.aspx',
                            )
                        }
                    >
                        {' '}
                        Trademarks
                    </MenuItem>
                    <MenuItem
                        icon={<OpenRegular />}
                        onClick={() => window.open('http://github.com/microsoft/semanticworkbench')}
                    >
                        {' '}
                        @GitHub
                    </MenuItem>
                    <MenuDivider />
                    {isAuthenticated ? (
                        <MenuItem icon={<ArrowExitRegular />} onClick={handleSignOut}>
                            Sign Out
                        </MenuItem>
                    ) : (
                        <MenuItem icon={<ArrowEnterRegular />} onClick={handleSignIn}>
                            Sign In
                        </MenuItem>
                    )}
                    <MenuDivider />
                    <div className={classes.accountInfo}>
                        <Caption1>© Microsoft {new Date().getFullYear()}</Caption1>
                    </div>
                </MenuList>
            </MenuPopover>
        </Menu>
    );
};


=== File: workbench-app/src/components/FrontDoor/GlobalContent.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { ConversationList } from './Controls/ConversationList';

const useClasses = makeStyles({
    root: {
        flex: '1 1 auto',
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
    },
    header: {
        flex: '0 0 auto',
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
    },
    content: {
        flex: '1 1 auto',
        overflow: 'auto',
    },
});

interface GlobalContentProps {
    headerBefore?: React.ReactNode;
    headerAfter?: React.ReactNode;
}

export const GlobalContent: React.FC<GlobalContentProps> = (props) => {
    const { headerBefore, headerAfter } = props;
    const classes = useClasses();

    const conversationList = React.useMemo(() => <ConversationList hideChildConversations />, []);

    return (
        <div className={classes.root}>
            <div className={classes.header}>
                {headerBefore}
                {headerAfter}
            </div>
            <div className={classes.content}>{conversationList}</div>
        </div>
    );
};


=== File: workbench-app/src/components/FrontDoor/MainContent.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button, makeStyles, shorthands, Subtitle2, Title3, tokens } from '@fluentui/react-components';
import React from 'react';
import { Constants } from '../../Constants';
import { useConversationUtility } from '../../libs/useConversationUtility';
import { useCreateConversation } from '../../libs/useCreateConversation';
import { useSiteUtility } from '../../libs/useSiteUtility';
import { useAppSelector } from '../../redux/app/hooks';
import { useGetAssistantServiceInfosQuery } from '../../services/workbench';
import { ExperimentalNotice } from '../App/ExperimentalNotice';
import { Loading } from '../App/Loading';
import { ConversationsImport } from '../Conversations/ConversationsImport';
import { Chat } from './Chat/Chat';
import { AssistantCard } from './Controls/AssistantCard';
import { NewConversationForm } from './Controls/NewConversationForm';

const useClasses = makeStyles({
    root: {
        flex: '1 1 auto',
        display: 'flex',
        flexDirection: 'column',
    },
    header: {
        flex: '0 0 auto',
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
    },
    body: {
        flex: '1 1 auto',
        display: 'flex',
        justifyContent: 'center',
        height: '90vh',
        marginBottom: tokens.spacingVerticalL,
        overflowY: 'auto',
    },
    content: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
        width: '100%',
        maxWidth: '900px',
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
        height: '100%',
    },
    assistantHeader: {
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        alignItems: 'center',
        width: '100%',
        gap: tokens.spacingHorizontalM,
        marginTop: tokens.spacingVerticalL,
    },
    form: {
        marginTop: tokens.spacingVerticalL,
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
    actions: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: tokens.spacingHorizontalM,
    },
    cards: {
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'center',
        gap: tokens.spacingVerticalL,
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
    },
    card: {
        padding: 0,
        width: '420px',
    },
    cardHeader: {
        padding: tokens.spacingHorizontalM,
        borderRadius: tokens.borderRadiusMedium,
        borderBottomRightRadius: 0,
        borderBottomLeftRadius: 0,
    },
    cardHeaderBody: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxSizing: 'border-box',
        width: '100%',
    },
    cardPreview: {
        padding: tokens.spacingHorizontalM,
        paddingBottom: tokens.spacingVerticalL,
        margin: '0 !important',
        width: '100%',
        boxSizing: 'border-box',
        wordWrap: 'break-word',
        overflowWrap: 'break-word',
        '& ul': {
            boxSizing: 'border-box',
        },
    },
});

interface MainContentProps {
    headerBefore?: React.ReactNode;
    headerAfter?: React.ReactNode;
}

export const MainContent: React.FC<MainContentProps> = (props) => {
    const { headerBefore, headerAfter } = props;
    const activeConversationId = useAppSelector((state) => state.app.activeConversationId);
    const { createConversation } = useCreateConversation();
    const [isValid, setIsValid] = React.useState(false);
    const [assistantId, setAssistantId] = React.useState<string>();
    const [name, setName] = React.useState<string>();
    const [assistantServiceId, setAssistantServiceId] = React.useState<string>();
    const [templateId, setTemplateId] = React.useState<string>();
    const [submitted, setSubmitted] = React.useState(false);
    const { navigateToConversation } = useConversationUtility();
    const siteUtility = useSiteUtility();
    const { isFetching: createConversationIsFetching } = useCreateConversation();
    const { data: assistantServices } = useGetAssistantServiceInfosQuery({ userIds: ['me'] });

    const classes = useClasses();

    React.useEffect(() => {
        if (!activeConversationId && document.title !== Constants.app.name) {
            siteUtility.setDocumentTitle();
        }
    }, [activeConversationId, siteUtility]);

    const createConversationWithAssistant = React.useCallback(
        async (
            assistantInfo:
                | { assistantId: string }
                | { name: string; assistantServiceId: string; templateId: string; image?: string },
        ) => {
            setSubmitted(true);
            try {
                const { conversation } = await createConversation(assistantInfo);
                navigateToConversation(conversation.id);
            } finally {
                setSubmitted(false);
            }
        },
        [createConversation, navigateToConversation],
    );

    const handleCreate = React.useCallback(async () => {
        if (submitted || !isValid || !assistantId) {
            return;
        }

        // ensure we have a valid assistant info
        let assistantInfo:
            | { assistantId: string }
            | { name: string; assistantServiceId: string; templateId: string }
            | undefined;
        if (assistantId === 'new' && name && assistantServiceId && templateId) {
            assistantInfo = { name, assistantServiceId, templateId };
        } else {
            assistantInfo = { assistantId };
        }

        if (!assistantInfo) {
            return;
        }

        await createConversationWithAssistant(assistantInfo);
    }, [assistantId, assistantServiceId, createConversationWithAssistant, isValid, name, submitted, templateId]);

    const handleImport = React.useCallback(
        (conversationIds: string[]) => {
            if (conversationIds.length > 0) {
                navigateToConversation(conversationIds[0]);
            }
        },
        [navigateToConversation],
    );

    const uniqueAssistantTemplates = React.useMemo(
        () =>
            assistantServices
                ?.flatMap((assistantService) => {
                    return assistantService.templates.map((template) => ({
                        assistantServiceId: assistantService.assistantServiceId,
                        templateId: template.id,
                        name: template.name,
                    }));
                })
                .toSorted((a, b) => a.name.localeCompare(b.name)) ?? [],
        [assistantServices],
    );

    if (activeConversationId) {
        return <Chat conversationId={activeConversationId} headerBefore={headerBefore} headerAfter={headerAfter} />;
    }

    if (createConversationIsFetching) {
        return <Loading />;
    }

    return (
        <div className={classes.root}>
            <>
                <div className={classes.header}>
                    {headerBefore}
                    <ExperimentalNotice />
                    {headerAfter}
                </div>
                <div className={classes.body}>
                    <div className={classes.content}>
                        <div className={classes.assistantHeader}>
                            <Title3>Choose an assistant</Title3>
                        </div>
                        <div className={classes.cards}>
                            {uniqueAssistantTemplates?.map((ids) => (
                                <AssistantCard
                                    key={ids.assistantServiceId + '/' + ids.templateId}
                                    assistantServiceId={ids.assistantServiceId}
                                    templateId={ids.templateId}
                                    requireEnabled={true}
                                />
                            ))}
                        </div>
                        <div className={classes.form}>
                            <Subtitle2>Or pick from your list of assistants:</Subtitle2>
                            <NewConversationForm
                                assistantFieldLabel=""
                                onSubmit={handleCreate}
                                onChange={(isValid, data) => {
                                    setIsValid(isValid);
                                    setAssistantId(data.assistantId);
                                    setAssistantServiceId(data.assistantServiceId);
                                    setTemplateId(data.templateId);
                                    setName(data.name);
                                }}
                                disabled={submitted}
                            />
                            <div className={classes.actions}>
                                <ConversationsImport
                                    appearance="outline"
                                    onImport={handleImport}
                                    disabled={submitted}
                                />
                                <Button appearance="primary" onClick={handleCreate} disabled={!isValid || submitted}>
                                    Create
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>
            </>
        </div>
    );
};


=== File: workbench-app/src/global.d.ts ===
export {};

// Allow static build of React code to access env vars
// SEE https://create-react-app.dev/docs/title-and-meta-tags/#injecting-data-from-the-server-into-the-page
declare global {
    interface Window {
        VITE_SEMANTIC_WORKBENCH_SERVICE_URL?: string;
    }
}


=== File: workbench-app/src/index.css ===
:root {
    text-rendering: optimizeLegibility;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    -webkit-text-size-adjust: 100%;
}

body {
    margin: 0;
    overscroll-behavior: none;
    background-size: cover;
    background-repeat: no-repeat;
    background-position: center;
}

html,
body,
#root,
#root > .app-container {
    height: 100%;
    background-color: rgba(255, 255, 255, 0.3);
}

::-webkit-scrollbar {
    width: 1em;
}
::-webkit-scrollbar-track {
    -webkit-box-shadow: inset 0 0 6px rgba(0, 0, 0, 0.2);
}
::-webkit-scrollbar-thumb {
    background-color: rgba(0, 0, 0, 0.1);
    outline: 1px solid rgba(0, 0, 0, 0.1);
    border-radius: 2px;
}

/* Themed scroll bars - make sure to update the colors to match your theme brands */
.brand-scrollbar-light::-webkit-scrollbar-thumb {
    background-color: '#1D6BB9';
}

.brand-scrollbar-orange::-webkit-scrollbar-thumb {
    background-color: '#C02D09';
}

.brand-scrollbar-purple::-webkit-scrollbar-thumb {
    background-color: '#AB12D9';
}

.user-avatar .fui-Avatar {
    margin-right: unset;
}

#root .fui-Card {
    overflow: visible;
    margin: 2px 0;
}


=== File: workbench-app/src/libs/AppStorage.ts ===
// Copyright (c) Microsoft. All rights reserved.

import debug from 'debug';
import { Constants } from '../Constants';

const log = debug(Constants.debug.root).extend('app-storage');

export class AppStorage {
    public static instance: AppStorage | undefined;

    public static getInstance = () => {
        if (!this.instance) {
            this.instance = new AppStorage();
        }
        return this.instance;
    };

    public getValueOrDefault = <T>(storageKey: string, defaultValue: T) => {
        const value = window.localStorage.getItem(storageKey);
        if (value) {
            return value as T;
        }
        return defaultValue;
    };

    public saveValue = (storageKey: string, value?: unknown) => {
        if (!value) {
            window.localStorage.removeItem(storageKey);
            return;
        }

        window.localStorage.setItem(storageKey, value as string);
    };

    public loadObject = <T>(storageKey: string) => {
        return this.deserializeData<T>(window.localStorage.getItem(storageKey));
    };

    public saveObject = (storageKey: string, object?: unknown) => {
        if (!object) {
            window.localStorage.removeItem(storageKey);
            return;
        }

        window.localStorage.setItem(storageKey, JSON.stringify(object));
    };

    private readonly deserializeData = <T>(data: string | null) => {
        if (!data) {
            return undefined;
        }
        try {
            return JSON.parse(data) as T;
        } catch (error) {
            log(error);
            return undefined;
        }
    };
}


=== File: workbench-app/src/libs/AuthHelper.ts ===
// Copyright (c) Microsoft. All rights reserved.

import { EndSessionRequest, IPublicClientApplication, LogLevel, RedirectRequest } from '@azure/msal-browser';
import debug from 'debug';
import { Constants } from '../Constants';

const log = debug(Constants.debug.root).extend('auth-helper');

const getMsalConfig = () => ({
    auth: {
        ...Constants.msal.auth,
        redirectUri: window.origin,
    },
    cache: Constants.msal.cache,
    system: {
        loggerOptions: {
            loggerCallback: (level: any, message: any, containsPii: any) => {
                if (containsPii) {
                    return;
                }
                switch (level) {
                    case LogLevel.Error:
                        log('error:', message);
                        return;
                    // case LogLevel.Info:
                    //     log('info:', message);
                    //     return;
                    // case LogLevel.Verbose:
                    //     log('verbose:', message);
                    //     return;
                    case LogLevel.Warning:
                        log('warn:', message);
                }
            },
        },
    },
});

const loginRequest: RedirectRequest = {
    scopes: Constants.msal.msGraphScopes,
    // extraScopesToConsent: Constants.msal.skScopes,
};

const logoutRequest: EndSessionRequest = {
    postLogoutRedirectUri: window.origin,
};

const loginAsync = async (instance: IPublicClientApplication) => {
    if (Constants.msal.method === 'redirect') {
        await instance.loginRedirect(loginRequest);
        return undefined;
    } else {
        return await instance.loginPopup(loginRequest);
    }
};

const logoutAsync = async (instance: IPublicClientApplication) => {
    if (Constants.msal.method === 'popup') {
        void instance.logoutPopup(logoutRequest);
    }
    if (Constants.msal.method === 'redirect') {
        void instance.logoutRedirect(logoutRequest);
    }
};

export const AuthHelper = {
    getMsalConfig,
    loginRequest,
    logoutRequest,
    loginAsync,
    logoutAsync,
};


=== File: workbench-app/src/libs/EventSubscriptionManager.ts ===
type Listener = (event: any) => void;

export class EventSubscriptionManager {
    private listeners: Map<string, Set<Listener>>;

    constructor() {
        this.listeners = new Map();
    }

    addEventListener(eventName: string, listener: Listener) {
        if (!this.listeners.has(eventName)) {
            this.listeners.set(eventName, new Set());
        }
        this.listeners.get(eventName)!.add(listener);
    }

    removeEventListener(eventName: string, listener: Listener) {
        if (!this.listeners.has(eventName)) return;

        const listeners = this.listeners.get(eventName)!;
        listeners.delete(listener);

        if (listeners.size === 0) {
            this.listeners.delete(eventName);
        }
    }

    emit(eventName: string, event: any) {
        if (!this.listeners.has(eventName)) return;

        this.listeners.get(eventName)!.forEach((listener) => listener(event));
    }
}


=== File: workbench-app/src/libs/Theme.ts ===
// Copyright (c) Microsoft. All rights reserved.

import { BrandVariants, createDarkTheme, createLightTheme } from '@fluentui/react-components';

const getCustomTheme = (theme: string, brand?: string) => {
    let customBrandRamp: BrandVariants;
    switch (brand) {
        case 'orange':
            customBrandRamp = ramp2;
            break;
        case 'purple':
            customBrandRamp = ramp3;
            break;
        default:
            customBrandRamp = ramp1;
            break;
    }

    return theme === 'light' ? createLightTheme(customBrandRamp) : createDarkTheme(customBrandRamp);
};

export const Theme = {
    getCustomTheme,
};

// Generate at: https://fluentuipr.z22.web.core.windows.net/pull/24507/theme-designer/storybook/index.html?path=/story/themedesigner--page

const ramp1: BrandVariants = {
    10: '#000000',
    20: '#0F141D',
    30: '#152133',
    40: '#1A2E4C',
    50: '#1E3D65',
    60: '#1F4B80',
    70: '#1F5B9C',
    80: '#1D6BB9',
    90: '#177BD6',
    100: '#098BF5',
    110: '#469BFF',
    120: '#73ABFF',
    130: '#94BBFF',
    140: '#B1CCFF',
    150: '#CDDDFF',
    160: '#E6EEFF',
};

const ramp2: BrandVariants = {
    10: '#000000',
    20: '#210F04',
    30: '#381608',
    40: '#511C0B',
    50: '#6B210C',
    60: '#86260C',
    70: '#A32A0B',
    80: '#C02D09',
    90: '#DE3005',
    100: '#FD3300',
    110: '#FF6134',
    120: '#FF825B',
    130: '#FF9F7E',
    140: '#FFB9A0',
    150: '#FFD1C1',
    160: '#FFE9E1',
};

const ramp3: BrandVariants = {
    10: '#000000',
    20: '#1D0E20',
    30: '#32143B',
    40: '#481858',
    50: '#5F1A76',
    60: '#781A96',
    70: '#9118B7',
    80: '#AB12D9',
    90: '#C602FC',
    100: '#D142FF',
    110: '#DA65FF',
    120: '#E382FF',
    130: '#EA9DFF',
    140: '#F0B6FF',
    150: '#F6CFFF',
    160: '#FBE7FF',
};


=== File: workbench-app/src/libs/Utility.ts ===
// Copyright (c) Microsoft. All rights reserved.

import dayjs from 'dayjs';
import tz from 'dayjs/plugin/timezone';
import utc from 'dayjs/plugin/utc';
import { diff } from 'deep-object-diff';
import merge from 'deepmerge';

dayjs.extend(utc);
dayjs.extend(tz);

const deepEqual = (object1: object, object2: object) => {
    const differences = diff(object1, object2);
    return Object.keys(differences).length === 0;
};

const deepCopy = (object: object): object => {
    return JSON.parse(JSON.stringify(object));
};

const deepMerge = (target: object, source: object): object => {
    return merge(target, source, {
        arrayMerge: (_destinationArray: any[], sourceArray: any[]) => sourceArray,
    });
};

// Check if two values are equal, including handling undefined, null, and empty string
const isEqual = (value1: any, value2: any): boolean => {
    if (value1 === value2) return true;
    if (
        (value1 === undefined || value1 === null || value1 === '') &&
        (value2 === undefined || value2 === null || value2 === '')
    ) {
        return true;
    }
    return false;
};

// Deep diff between two objects, using dot-notation for nested keys
// Returns an object with the differences
const deepDiff = (obj1: ObjectLiteral, obj2: ObjectLiteral, parentKey = ''): ObjectLiteral => {
    const diff: ObjectLiteral = {};
    const allKeys = new Set([...Object.keys(obj1), ...Object.keys(obj2)]);

    allKeys.forEach((key) => {
        const value1 = obj1[key];
        const value2 = obj2[key];
        const currentKey = parentKey ? `${parentKey}.${key}` : key;

        if (!isEqual(value1, value2)) {
            if (typeof value1 === 'object' && typeof value2 === 'object') {
                const nestedDiff = deepDiff(value1, value2, currentKey);
                if (Object.keys(nestedDiff).length > 0) {
                    diff[currentKey] = nestedDiff;
                }
            } else {
                diff[currentKey] = { oldValue: value1, newValue: value2 };
            }
        }
    });

    return diff;
};

type ObjectLiteral = { [key: string]: any };

const toDayJs = (value: string | Date, timezone: string = dayjs.tz.guess()) => {
    return dayjs.utc(value).tz(timezone);
};

const toDate = (value: string, timezone: string = dayjs.tz.guess()): Date => {
    return toDayJs(value, timezone).toDate();
};

const toSimpleDateString = (value: string | Date, timezone: string = dayjs.tz.guess()): string => {
    const now = dayjs.utc();
    const date = toDayJs(value, timezone);

    // If the date is today, return the time
    if (date.isSame(now, 'day')) {
        return date.format('h:mm A');
    }

    // If the date is within the last week, return the day of the week
    if (date.isAfter(now.subtract(7, 'days'))) {
        return date.format('ddd');
    }

    // Otherwise, return the month and day if it's within the current year
    if (date.isSame(now, 'year')) {
        return date.format('MMM D');
    }

    // Otherwise, return the month, day, and year
    return date.format('MMM D, YYYY');
};

const toFormattedDateString = (value: string | Date, format: string, timezone: string = dayjs.tz.guess()): string => {
    return toDayJs(value, timezone).format(format);
};

const getTimestampForFilename = (timezone: string = dayjs.tz.guess()) => {
    // return in format YYYYMMDDHHmm
    return toDayJs(new Date(), timezone).format('YYYYMMDDHHmm');
};

const sortKeys = (obj: any): any => {
    if (Array.isArray(obj)) {
        return obj.map(sortKeys);
    } else if (obj !== null && typeof obj === 'object') {
        return Object.keys(obj)
            .sort()
            .reduce((result: any, key: string) => {
                result[key] = sortKeys(obj[key]);
                return result;
            }, {});
    }
    return obj;
};

const errorToMessageString = (error?: Record<string, any> | string) => {
    // Check if the error is undefined
    if (error === undefined) {
        // Return an empty string
        return undefined;
    }

    // Check if the error is a string
    if (typeof error === 'string') {
        // Return the error as is
        return error;
    }

    // Set the message for the error message, displayed as the error details
    let message = '';

    // Check if the action payload contains a 'data.detail' property
    if ('data' in error && 'detail' in error.data) {
        // Check if the 'detail' property is a string
        if (typeof error.data.detail === 'string') {
            // Set the message to the 'detail' property
            message = (error.data as { detail: string }).detail;
        } else {
            // Set the message to the 'detail' property as a stringified JSON object
            message = JSON.stringify(error.data.detail);
        }
    } else if ('message' in error) {
        message = error.message;
    } else if ('error' in error && 'status' in error) {
        message = error.status;

        // Additional error handling for specific error types
        if (error.status === 'FETCH_ERROR') {
            message = `Error connecting to Semantic Workbench service, ensure service is running`;
            // Check if the url contains a GitHub Codespaces hostname
            if (error.meta.baseQueryMeta.request.url.includes('app.github.dev')) {
                // Append a message to the error message to indicate it may be due
                // to the port not being forwarded correctly
                message = `${message} and port is visible`;
            }
        }
    }

    return message;
};

const withStatus = async <T>(setStatus: (status: boolean) => void, callback: () => Promise<T>): Promise<T> => {
    setStatus(true);
    try {
        return await callback();
    } finally {
        setStatus(false);
    }
};

export const Utility = {
    deepEqual,
    deepCopy,
    deepMerge,
    deepDiff,
    toDate,
    toSimpleDateString,
    toFormattedDateString,
    getTimestampForFilename,
    sortKeys,
    errorToMessageString,
    withStatus,
};


=== File: workbench-app/src/libs/useAssistantCapabilities.ts ===
import React from 'react';
import { Assistant } from '../models/Assistant';
import { AssistantCapability } from '../models/AssistantCapability';
import { useWorkbenchService } from './useWorkbenchService';

export function useGetAssistantCapabilities(assistants: Assistant[], skipToken: { skip: boolean } = { skip: false }) {
    const [isFetching, setIsFetching] = React.useState<boolean>(true);

    // Build a memoized set of all capabilities to be used as a default for assistants that do not
    // specify capabilities
    const allCapabilities = React.useMemo(
        () =>
            Object.entries(AssistantCapability).reduce((acc, [_, capability]) => {
                acc.add(capability);
                return acc;
            }, new Set<AssistantCapability>()),
        [],
    );

    const [assistantCapabilities, setAssistantCapabilities] = React.useState<Set<AssistantCapability>>(allCapabilities);
    const workbenchService = useWorkbenchService();

    // Load the capabilities for all assistants and update the state with the result
    React.useEffect(() => {
        if (skipToken.skip) {
            return;
        }

        let active = true;

        if (assistants.length === 0) {
            if (assistantCapabilities.symmetricDifference(allCapabilities).size > 0) {
                setAssistantCapabilities(allCapabilities);
            }
            setIsFetching(false);
            return;
        }

        (async () => {
            if (active) {
                setIsFetching(true);
            }

            // Get the service info for each assistant
            const infosResponse = await workbenchService.getAssistantServiceInfosAsync(
                assistants.map((assistant) => assistant.assistantServiceId),
            );
            const serviceInfos = infosResponse.filter((info) => info !== undefined);

            // Combine all capabilities from all assistants into a single set
            const capabilities = serviceInfos.reduce<Set<AssistantCapability>>((acc, info) => {
                const metadataCapabilities = info.metadata?.capabilities;

                // If there are no capabilities specified at all, default to all capabilities
                if (metadataCapabilities === undefined) {
                    acc.union(allCapabilities);
                    return acc;
                }

                const capabilitiesSet = new Set(
                    Object.keys(metadataCapabilities)
                        .filter((key) => metadataCapabilities[key])
                        .map((key) => key as AssistantCapability),
                );
                acc = acc.union(capabilitiesSet);
                return acc;
            }, new Set<AssistantCapability>());

            if (active) {
                if (assistantCapabilities.symmetricDifference(capabilities).size > 0) {
                    setAssistantCapabilities(capabilities);
                }
                setIsFetching(false);
            }
        })();

        return () => {
            active = false;
        };
    }, [allCapabilities, assistants, assistantCapabilities, skipToken.skip, workbenchService]);

    return {
        data: assistantCapabilities,
        isFetching,
    };
}


=== File: workbench-app/src/libs/useChatCanvasController.ts ===
import debug from 'debug';
import React from 'react';
import { Constants } from '../Constants';
import { useAppDispatch, useAppSelector } from '../redux/app/hooks';
import { setChatCanvasOpen, setChatCanvasState } from '../redux/features/chatCanvas/chatCanvasSlice';
import { ChatCanvasState } from '../redux/features/chatCanvas/ChatCanvasState';

const log = debug(Constants.debug.root).extend('useCanvasController');

export const useChatCanvasController = () => {
    const chatCanvasState = useAppSelector((state) => state.chatCanvas);
    const [isTransitioning, setIsTransitioning] = React.useState(false);
    const dispatch = useAppDispatch();

    const closingTransitionDelayMs = 400;
    const openingTransitionDelayMs = 200;

    const chooseTransitionType = React.useCallback(
        (currentCanvasState: ChatCanvasState, fullTargetCanvasState: ChatCanvasState) => {
            if (!currentCanvasState.open && fullTargetCanvasState.open) {
                return 'open';
            }
            if (currentCanvasState.open && !fullTargetCanvasState.open) {
                return 'close';
            }
            if (currentCanvasState.mode !== fullTargetCanvasState.mode) {
                return 'mode';
            }
            return 'none';
        },
        [],
    );

    const transitionOpenToClose = React.useCallback(async () => {
        log(`canvas closing with transition of ${closingTransitionDelayMs}ms`);

        // close the canvas
        dispatch(setChatCanvasOpen(false));

        // wait for the canvas to close before indicating that we are no longer transitioning
        await new Promise((resolve) => setTimeout(resolve, closingTransitionDelayMs));
        log('canvas closed');
    }, [dispatch]);

    const transitionCloseToOpen = React.useCallback(
        async (fullTargetCanvasState: ChatCanvasState) => {
            log(`canvas opening with transition of ${openingTransitionDelayMs}ms`);

            // open the canvas with the new mode
            dispatch(setChatCanvasState(fullTargetCanvasState));

            // wait for the canvas to open before indicating that we are no longer transitioning
            await new Promise((resolve) => setTimeout(resolve, openingTransitionDelayMs));

            log(`canvas opened with mode ${fullTargetCanvasState.mode}`);

            if (fullTargetCanvasState.mode === 'assistant') {
                log(
                    `assistant state: ${fullTargetCanvasState.selectedAssistantStateId} [assistant: ${fullTargetCanvasState.selectedAssistantId}]`,
                );
            }
        },
        [dispatch],
    );

    const transitionOpenToNewMode = React.useCallback(
        async (fullTargetCanvasState: ChatCanvasState) => {
            log('canvas changing mode while open');
            await transitionOpenToClose();
            await transitionCloseToOpen(fullTargetCanvasState);
        },
        [transitionCloseToOpen, transitionOpenToClose],
    );

    const setState = React.useCallback(
        (targetCanvasState: Partial<ChatCanvasState>) => {
            dispatch(setChatCanvasState({ ...chatCanvasState, ...targetCanvasState }));
        },
        [dispatch, chatCanvasState],
    );

    const transitionToState = React.useCallback(
        async (targetCanvasState: Partial<ChatCanvasState>) => {
            //
            // we should always set the isTransitioning state to true before we start any transitions
            // so that we can disable various UX elements that should not be interacted with
            // while the canvas is transitioning
            //
            // possible transitions:
            //
            // 1. open -> close:
            //   - update state to close the canvas
            //   - wait for the close delay
            //   - set isTransitioning to false
            //
            // 2. close -> open with mode selection
            //   - update state to open directly to the desired mode
            //   - wait for the open delay
            //   - set isTransitioning to false
            //
            // 3. mode change while open
            //   - close the canvas without any other state changes first
            //   - wait for the close delay
            //   - update state to open directly to the desired mode
            //   - wait for the open delay
            //   - set isTransitioning to false
            //

            // indicate that we are transitioning so that we can disable the canvas
            setIsTransitioning(true);

            // determine the type of transition that we need to perform
            const transitionType = chooseTransitionType(chatCanvasState, {
                ...chatCanvasState,
                ...targetCanvasState,
            });

            // perform the transition
            switch (transitionType) {
                case 'open':
                    await transitionOpenToClose();
                    await transitionCloseToOpen({ ...chatCanvasState, ...targetCanvasState });
                    break;
                case 'close':
                    await transitionOpenToClose();
                    break;
                case 'mode':
                    await transitionOpenToNewMode({ ...chatCanvasState, ...targetCanvasState });
                    break;
                case 'none':
                    // no transition needed, just update the state
                    dispatch(setChatCanvasState({ ...chatCanvasState, ...targetCanvasState }));
                    setIsTransitioning(false);
                    break;
            }

            // ensure that we are not claiming to be transitioning anymore
            setIsTransitioning(false);
        },
        [
            chooseTransitionType,
            dispatch,
            chatCanvasState,
            transitionCloseToOpen,
            transitionOpenToClose,
            transitionOpenToNewMode,
        ],
    );

    return { chatCanvasState, isTransitioning, setState, transitionToState };
};


=== File: workbench-app/src/libs/useConversationEvents.ts ===
// Copyright (c) Microsoft. All rights reserved.
import { EventSourceMessage } from '@microsoft/fetch-event-source';
import React from 'react';
import { conversationMessageFromJSON } from '../models/ConversationMessage';
import { ConversationParticipant } from '../models/ConversationParticipant';
import { useAppDispatch } from '../redux/app/hooks';
import { workbenchConversationEvents } from '../routes/FrontDoor';
import { useEnvironment } from './useEnvironment';

export const useConversationEvents = (
    conversationId: string,
    handlers: {
        onMessageCreated?: () => void;
        onMessageDeleted?: (messageId: string) => void;
        onParticipantCreated?: (participant: ConversationParticipant) => void;
        onParticipantUpdated?: (participant: ConversationParticipant) => void;
    },
) => {
    const { onMessageCreated, onMessageDeleted, onParticipantCreated, onParticipantUpdated } = handlers;
    const environment = useEnvironment();
    const dispatch = useAppDispatch();

    // handle new message events
    const handleMessageEvent = React.useCallback(
        async (event: EventSourceMessage) => {
            const { data } = JSON.parse(event.data);
            const parsedEventData = {
                timestamp: data.timestamp,
                data: {
                    message: conversationMessageFromJSON(data.message),
                },
            };

            if (event.event === 'message.created') {
                onMessageCreated?.();
            }

            if (event.event === 'message.deleted') {
                onMessageDeleted?.(parsedEventData.data.message.id);
            }
        },
        [onMessageCreated, onMessageDeleted],
    );

    // handle participant events
    const handleParticipantEvent = React.useCallback(
        (event: EventSourceMessage) => {
            const parsedEventData = JSON.parse(event.data) as {
                timestamp: string;
                data: {
                    participant: ConversationParticipant;
                    participants: ConversationParticipant[];
                };
            };

            if (event.event === 'participant.created') {
                onParticipantCreated?.(parsedEventData.data.participant);
            }

            if (event.event === 'participant.updated') {
                onParticipantUpdated?.(parsedEventData.data.participant);
            }
        },
        [onParticipantCreated, onParticipantUpdated],
    );

    React.useEffect(() => {
        workbenchConversationEvents.addEventListener('message.created', handleMessageEvent);
        workbenchConversationEvents.addEventListener('message.deleted', handleMessageEvent);
        workbenchConversationEvents.addEventListener('participant.created', handleParticipantEvent);
        workbenchConversationEvents.addEventListener('participant.updated', handleParticipantEvent);

        return () => {
            workbenchConversationEvents.removeEventListener('message.created', handleMessageEvent);
            workbenchConversationEvents.removeEventListener('message.deleted', handleMessageEvent);
            workbenchConversationEvents.removeEventListener('participant.created', handleParticipantEvent);
            workbenchConversationEvents.removeEventListener('participant.updated', handleParticipantEvent);
        };
    }, [conversationId, dispatch, environment.url, handleMessageEvent, handleParticipantEvent]);
};


=== File: workbench-app/src/libs/useConversationUtility.ts ===
import dayjs from 'dayjs';
import debug from 'debug';
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Constants } from '../Constants';
import { Conversation } from '../models/Conversation';
import { ConversationShare } from '../models/ConversationShare';
import { useAppSelector } from '../redux/app/hooks';
import { useUpdateConversationMutation } from '../services/workbench';

const log = debug(Constants.debug.root).extend('useConversationUtility');

// Share types to be used in the app.
export const enum ConversationShareType {
    NotRedeemable = 'Not redeemable',
    InvitedToParticipate = 'Invited to participate',
    InvitedToObserve = 'Invited to observe',
    InvitedToDuplicate = 'Invited to copy',
}

interface ParticipantAppMetadata {
    lastReadTimestamp?: string;
    pinned?: boolean;
}

export const useConversationUtility = () => {
    const [isMessageVisible, setIsMessageVisible] = React.useState(false);
    const isMessageVisibleRef = React.useRef(null);
    const [updateConversation] = useUpdateConversationMutation();
    const localUserId = useAppSelector((state) => state.localUser.id);
    const navigate = useNavigate();

    // region Navigation

    const navigateToConversation = React.useCallback(
        (conversationId?: string, hash?: string) => {
            let path = conversationId ? '/' + conversationId : '';
            if (hash) {
                path += `#${hash}`;
            }
            navigate(path);
        },
        [navigate],
    );

    // endregion

    // region Shares
    //
    // This region contains logic for handling conversation shares, including determining the share type
    // based on the conversation permission and metadata. It also contains logic for handling the combinations
    // of metadata, permissions, and share types in shared location for consistency across the app.
    //

    const getOwnerParticipant = React.useCallback((conversation: Conversation) => {
        return conversation.participants.find((participant) => participant.id === conversation.ownerId);
    }, []);

    const wasSharedWithMe = React.useCallback(
        (conversation: Conversation): boolean => {
            return conversation.ownerId !== localUserId;
        },
        [localUserId],
    );

    const getShareTypeMetadata = React.useCallback(
        (
            shareType: ConversationShareType,
            linkToMessageId?: string,
        ): {
            permission: 'read' | 'read_write';
            metadata: { showDuplicateAction?: boolean; linkToMessageId?: string };
        } => {
            // Default to read_write for invited to participate, read for observe or duplicate.
            const permission = shareType === ConversationShareType.InvitedToParticipate ? 'read_write' : 'read';
            const showDuplicateAction = shareType === ConversationShareType.InvitedToDuplicate;
            return {
                permission,
                metadata: { showDuplicateAction, linkToMessageId },
            };
        },
        [],
    );

    const getShareType = React.useCallback(
        (
            conversationShare: ConversationShare,
        ): {
            shareType: ConversationShareType;
            linkToMessageId?: string;
        } => {
            const { isRedeemable, conversationPermission, metadata } = conversationShare;

            if (!isRedeemable) {
                return { shareType: ConversationShareType.NotRedeemable };
            }

            // If the showDuplicateAction metadata is set, use that to determine the share type.
            if (metadata.showDuplicateAction) {
                return { shareType: ConversationShareType.InvitedToDuplicate };
            }

            // Otherwise, use the conversation permission to determine the share type.
            const shareType =
                conversationPermission !== 'read'
                    ? ConversationShareType.InvitedToParticipate
                    : ConversationShareType.InvitedToObserve;
            return {
                shareType,
                linkToMessageId: metadata.linkToMessageId,
            };
        },
        [],
    );

    const getShareLink = React.useCallback((share: ConversationShare): string => {
        return `${window.location.origin}/conversation-share/${encodeURIComponent(share.id)}/redeem`;
    }, []);
    // endregion

    // region App Metadata

    const setAppMetadata = React.useCallback(
        async (conversation: Conversation, appMetadata: Partial<ParticipantAppMetadata>) => {
            if (!localUserId) {
                log(
                    'Local user ID not set while setting conversation metadata for user, skipping',
                    `[Conversation ID: ${conversation.id}]`,
                    appMetadata,
                );
                return;
            }

            const participantAppMetadata: Record<string, ParticipantAppMetadata> =
                conversation.metadata?.participantAppMetadata ?? {};
            const userAppMetadata = participantAppMetadata[localUserId] ?? {};

            // Save the conversation
            await updateConversation({
                id: conversation.id,
                metadata: {
                    participantAppMetadata: {
                        ...participantAppMetadata,
                        [localUserId]: { ...userAppMetadata, ...appMetadata },
                    },
                },
            });
        },
        [updateConversation, localUserId],
    );

    // endregion

    // region Unread

    React.useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                setIsMessageVisible(entry.isIntersecting);
            },
            { threshold: 0.1 },
        );

        const currentRef = isMessageVisibleRef.current;
        if (currentRef) {
            observer.observe(currentRef);
        }

        return () => {
            if (currentRef) {
                observer.unobserve(currentRef);
            }
        };
    }, []);

    const getLastReadTimestamp = React.useCallback(
        (conversation: Conversation) => {
            if (!localUserId) {
                return;
            }
            const participantAppMetadata: Record<string, ParticipantAppMetadata> =
                conversation.metadata?.participantAppMetadata ?? {};
            return participantAppMetadata[localUserId]?.lastReadTimestamp;
        },
        [localUserId],
    );

    const getLastMessageTimestamp = React.useCallback((conversation: Conversation) => {
        return conversation.latest_message?.timestamp ?? conversation.created;
    }, []);

    const hasUnreadMessages = React.useCallback(
        (conversation: Conversation) => {
            const lastReadTimestamp = getLastReadTimestamp(conversation);
            if (!lastReadTimestamp) {
                return true;
            }
            const lastMessageTimestamp = getLastMessageTimestamp(conversation);
            return dayjs(lastMessageTimestamp).isAfter(lastReadTimestamp);
        },
        [getLastReadTimestamp, getLastMessageTimestamp],
    );

    const isUnread = React.useCallback(
        (conversation: Conversation, messageTimestamp: string) => {
            const lastReadTimestamp = getLastReadTimestamp(conversation);
            if (!lastReadTimestamp) {
                return true;
            }
            return dayjs(messageTimestamp).isAfter(lastReadTimestamp);
        },
        [getLastReadTimestamp],
    );

    const markAllAsRead = React.useCallback(
        async (conversation: Conversation | Conversation[]) => {
            const markSingleConversation = async (c: Conversation) => {
                if (!hasUnreadMessages(c)) {
                    return;
                }
                await setAppMetadata(c, { lastReadTimestamp: getLastMessageTimestamp(c) });
            };

            if (Array.isArray(conversation)) {
                await Promise.all(conversation.map(markSingleConversation));
                return;
            }
            await markSingleConversation(conversation);
        },
        [hasUnreadMessages, setAppMetadata, getLastMessageTimestamp],
    );

    const markAllAsUnread = React.useCallback(
        async (conversation: Conversation | Conversation[]) => {
            const markSingleConversation = async (c: Conversation) => {
                if (hasUnreadMessages(c)) {
                    return;
                }
                await setAppMetadata(c, { lastReadTimestamp: undefined });
            };

            if (Array.isArray(conversation)) {
                await Promise.all(conversation.map(markSingleConversation));
                return;
            }

            await markSingleConversation(conversation);
        },
        [hasUnreadMessages, setAppMetadata],
    );

    const setLastRead = React.useCallback(
        async (conversation: Conversation | Conversation[], messageTimestamp: string) => {
            if (Array.isArray(conversation)) {
                await Promise.all(conversation.map((c) => setAppMetadata(c, { lastReadTimestamp: messageTimestamp })));
                return;
            }
            await setAppMetadata(conversation, { lastReadTimestamp: messageTimestamp });
        },
        [setAppMetadata],
    );

    // Create a debounced version of setLastRead
    const timeoutRef = React.useRef<NodeJS.Timeout | null>(null);
    const debouncedSetLastRead = React.useCallback(
        (conversation: Conversation | Conversation[], messageTimestamp: string) => {
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
            }
            timeoutRef.current = setTimeout(() => setLastRead(conversation, messageTimestamp), 300);
        },
        [setLastRead],
    );

    // endregion

    // region Pinning

    const isPinned = React.useCallback(
        (conversation: Conversation) => {
            if (!localUserId) return;
            const participantAppMetadata: Record<string, ParticipantAppMetadata> =
                conversation.metadata?.participantAppMetadata ?? {};
            return participantAppMetadata[localUserId]?.pinned;
        },
        [localUserId],
    );

    const setPinned = React.useCallback(
        async (conversation: Conversation | Conversation[], pinned: boolean) => {
            if (Array.isArray(conversation)) {
                await Promise.all(conversation.map((c) => setAppMetadata(c, { pinned })));
                return;
            }
            await setAppMetadata(conversation, { pinned });
        },
        [setAppMetadata],
    );

    // endregion

    // add more conversation related utility functions here, separated by region if applicable

    return {
        navigateToConversation,
        getOwnerParticipant,
        wasSharedWithMe,
        getShareTypeMetadata,
        getShareType,
        getShareLink,
        isMessageVisibleRef,
        isMessageVisible,
        hasUnreadMessages,
        isUnread,
        markAllAsRead,
        markAllAsUnread,
        setLastRead,
        debouncedSetLastRead,
        isPinned,
        setPinned,
    };
};


=== File: workbench-app/src/libs/useCreateConversation.ts ===
import React from 'react';
import { Constants } from '../Constants';
import { Assistant } from '../models/Assistant';
import { AssistantServiceInfo, AssistantTemplate } from '../models/AssistantServiceInfo';
import { useAppSelector } from '../redux/app/hooks';
import {
    useAddConversationParticipantMutation,
    useCreateAssistantMutation,
    useCreateConversationMessageMutation,
    useCreateConversationMutation,
    useGetAssistantServiceInfosQuery,
    useGetAssistantsQuery,
    useLazyGetConversationQuery,
} from '../services/workbench';

export interface AssistantServiceTemplate {
    service: AssistantServiceInfo;
    template: AssistantTemplate;
}

export const useCreateConversation = () => {
    const {
        data: assistants,
        error: assistantsError,
        isLoading: assistantsLoading,
        refetch: refetchAssistants,
    } = useGetAssistantsQuery();
    const {
        data: assistantServices,
        error: assistantServicesError,
        isLoading: assistantServicesLoading,
    } = useGetAssistantServiceInfosQuery({});
    const {
        data: myAssistantServices,
        error: myAssistantServicesError,
        isLoading: myAssistantServicesLoading,
    } = useGetAssistantServiceInfosQuery({ userIds: ['me'] });

    const [createAssistant] = useCreateAssistantMutation();
    const [createConversation] = useCreateConversationMutation();
    const [addConversationParticipant] = useAddConversationParticipantMutation();
    const [createConversationMessage] = useCreateConversationMessageMutation();
    const [getConversation] = useLazyGetConversationQuery();

    const [isFetching, setIsFetching] = React.useState(true);
    const localUserName = useAppSelector((state) => state.localUser.name);

    if (assistantsError) {
        const errorMessage = JSON.stringify(assistantsError);
        throw new Error(`Error loading assistants: ${errorMessage}`);
    }

    if (assistantServicesError) {
        const errorMessage = JSON.stringify(assistantServicesError);
        throw new Error(`Error loading assistant services: ${errorMessage}`);
    }

    if (myAssistantServicesError) {
        const errorMessage = JSON.stringify(myAssistantServicesError);
        throw new Error(`Error loading my assistant services: ${errorMessage}`);
    }

    React.useEffect(() => {
        if (isFetching && !assistantsLoading && !assistantServicesLoading && !myAssistantServicesLoading) {
            setIsFetching(false);
        }

        if (!isFetching && (assistantsLoading || assistantServicesLoading || myAssistantServicesLoading)) {
            setIsFetching(true);
        }
    }, [assistantsLoading, assistantServicesLoading, myAssistantServicesLoading, isFetching]);

    const create = React.useCallback(
        async (
            conversationInfo:
                | {
                      assistantId: string;
                      conversationMetadata?: { [key: string]: any };
                      participantMetadata?: { [key: string]: any };
                      additionalAssistantIds?: string[];
                      existingConversationId?: string;
                  }
                | {
                      name: string;
                      assistantServiceId: string;
                      templateId: string;
                      conversationMetadata?: { [key: string]: any };
                      participantMetadata?: { [key: string]: any };
                      additionalAssistantIds?: string[];
                      existingConversationId?: string;
                  },
        ) => {
            if (assistantsLoading || assistantServicesLoading || myAssistantServicesLoading) {
                throw new Error('Cannot create conversation while loading assistants or assistant services');
            }

            let assistant: Assistant | undefined = undefined;

            const conversation = conversationInfo.existingConversationId
                ? await getConversation(conversationInfo.existingConversationId).unwrap()
                : await createConversation({ metadata: conversationInfo.conversationMetadata }).unwrap();

            if ('assistantId' in conversationInfo) {
                assistant = assistants?.find((a) => a.id === conversationInfo.assistantId);
                if (!assistant) {
                    throw new Error('Assistant not found');
                }
            } else {
                const { name, assistantServiceId, templateId } = conversationInfo;

                assistant = await createAssistant({
                    name,
                    assistantServiceId,
                    templateId,
                }).unwrap();
                await refetchAssistants();
            }

            const additionalAssistants =
                conversationInfo.additionalAssistantIds
                    ?.map((assistantId) => assistants?.find((a) => a.id === assistantId))
                    .filter((a) => a !== undefined) || [];

            if (conversationInfo.existingConversationId === undefined) {
                // send event to notify the conversation that the user has joined
                await createConversationMessage({
                    conversationId: conversation.id,
                    content: `${localUserName ?? 'Unknown user'} created the conversation`,
                    messageType: 'notice',
                });
            }

            for (const assistantAndMetadata of [
                { assistant, metadata: conversationInfo.participantMetadata },
                ...additionalAssistants.map((a) => ({ assistant: a, metadata: undefined })),
            ]) {
                // send notice message first, to announce before assistant reacts to create event
                await createConversationMessage({
                    conversationId: conversation.id,
                    content: `${assistantAndMetadata.assistant.name} added to conversation`,
                    messageType: 'notice',
                });

                await addConversationParticipant({
                    conversationId: conversation.id,
                    participantId: assistantAndMetadata.assistant.id,
                    metadata: assistantAndMetadata.metadata,
                });
            }

            return {
                assistant,
                conversation,
            };
        },
        [
            assistantsLoading,
            assistantServicesLoading,
            myAssistantServicesLoading,
            getConversation,
            createConversation,
            assistants,
            createAssistant,
            refetchAssistants,
            createConversationMessage,
            localUserName,
            addConversationParticipant,
        ],
    );

    const categorizedAssistantServices: Record<string, AssistantServiceTemplate[]> = React.useMemo(
        () => ({
            ...(assistantServices ?? [])
                .filter(
                    (service) =>
                        !myAssistantServices?.find(
                            (myService) => myService.assistantServiceId === service.assistantServiceId,
                        ),
                )
                .flatMap(
                    (service) =>
                        (service.templates ?? []).map((template) => ({
                            service,
                            template,
                        })) as AssistantServiceTemplate[],
                )
                .reduce((accumulated, assistantService) => {
                    const entry = Object.entries(Constants.assistantCategories).find(([_, serviceIds]) =>
                        serviceIds.includes(assistantService.service.assistantServiceId),
                    );
                    const assignedCategory = entry ? entry[0] : 'Other';
                    if (!accumulated[assignedCategory]) {
                        accumulated[assignedCategory] = [];
                    }
                    accumulated[assignedCategory].push(assistantService);
                    return accumulated;
                }, {} as Record<string, AssistantServiceTemplate[]>),
            'My Services': (myAssistantServices ?? []).flatMap(
                (service) =>
                    (service.templates ?? []).map((template) => ({
                        service,
                        template,
                    })) as AssistantServiceTemplate[],
            ),
        }),
        [assistantServices, myAssistantServices],
    );

    const orderedAssistantServicesCategories = React.useMemo(
        () =>
            [...Object.keys(Constants.assistantCategories), 'Other', 'My Services'].filter(
                (category) => categorizedAssistantServices[category]?.length,
            ),
        [categorizedAssistantServices],
    );

    const assistantServicesByCategories: { category: string; assistantServices: AssistantServiceTemplate[] }[] =
        React.useMemo(
            () =>
                orderedAssistantServicesCategories.map((category) => ({
                    category,
                    assistantServices:
                        categorizedAssistantServices[category]?.sort((a, b) =>
                            a.template.name.localeCompare(b.template.name),
                        ) ?? [],
                })),
            [categorizedAssistantServices, orderedAssistantServicesCategories],
        );

    return {
        isFetching,
        createConversation: create,
        assistantServicesByCategories,
        assistants,
    };
};


=== File: workbench-app/src/libs/useDebugComponentLifecycle.ts ===
import debug from 'debug';
import React from 'react';
import { Constants } from '../Constants';

const log = debug(Constants.debug.root).extend('useDebugComponentUpdate');

export const useDebugComponentLifecycle = (name: string, props: Record<string, any>, other?: Record<string, any>) => {
    const previousProps = React.useRef(props);
    const previousOther = React.useRef(other);

    log(`[${name}] rendered`);

    React.useEffect(() => {
        log(`[${name}] mounted`);
        return () => {
            log(`[${name}] unmounted`);
        };
    }, [name]);

    React.useEffect(() => {
        if (previousProps.current !== props) {
            const changedProps = Object.keys(props).reduce((acc, key) => {
                if (props[key] !== previousProps.current[key]) {
                    acc[key] = { from: previousProps.current[key], to: props[key] };
                }
                return acc;
            }, {} as Record<string, any>);

            if (Object.keys(changedProps).length > 0) {
                log(`[${name}] props changes:`, changedProps);
            }
        }

        previousProps.current = props;
    }, [name, props]);

    React.useEffect(() => {
        if (other && previousOther.current !== other) {
            const changedOther = Object.keys(other).reduce((acc, key) => {
                if (other[key] !== previousOther.current?.[key]) {
                    acc[key] = { from: previousOther.current?.[key], to: other[key] };
                }
                return acc;
            }, {} as Record<string, any>);

            if (Object.keys(changedOther).length > 0) {
                log(`[${name}] other changes:`, changedOther);
            }
        }

        previousOther.current = other;
    }, [name, other]);
};


=== File: workbench-app/src/libs/useDragAndDrop.ts ===
import debug from 'debug';
import React from 'react';

const useDragAndDrop = (domElement?: HTMLElement | null, log?: debug.Debugger, ignoreFileDrop: boolean = false) => {
    const [isDraggingOver, setIsDraggingOver] = React.useState(false);

    React.useEffect(() => {
        if (!domElement) {
            // no-op if the dom element is not provided
            // allowed so that the hook can be used with
            // React.useRef()
            return;
        }

        log?.('adding event listeners for drag and drop');

        const handleDragEnter = (event: DragEvent) => {
            event.preventDefault();
            setIsDraggingOver(true);
        };

        const handleDragLeave = (event: DragEvent) => {
            const relatedTarget = event.relatedTarget as HTMLElement;
            const currentTarget = event.currentTarget as HTMLElement;

            if (currentTarget.contains(relatedTarget)) {
                // ignore the event if the drag is still within the target element
                return;
            }
            setIsDraggingOver(false);
        };

        const handleDragOver = (event: DragEvent) => {
            // needed to allow drop event to fire
            event.preventDefault();
        };

        const handleDrop = (event: DragEvent) => {
            // ignore file drop events at the document level, but only file types this
            // prevents the undesirable behavior of the browser opening the file in the
            // window if the drop event is not handled or the user misses the drop target
            if (ignoreFileDrop && event.dataTransfer?.files.length) {
                log?.('ignoring file drop event');
                event.preventDefault();
            }

            setIsDraggingOver(false);
        };

        domElement.addEventListener('dragenter', handleDragEnter);
        domElement.addEventListener('dragleave', handleDragLeave);
        domElement.addEventListener('dragover', handleDragOver);
        domElement.addEventListener('drop', handleDrop);

        return () => {
            log?.('removing event listeners for drag and drop');
            domElement.removeEventListener('dragenter', handleDragEnter);
            domElement.removeEventListener('dragleave', handleDragLeave);
            domElement.removeEventListener('dragover', handleDragOver);
            domElement.removeEventListener('drop', handleDrop);
        };
    }, [log, domElement, ignoreFileDrop]);

    return isDraggingOver;
};

export default useDragAndDrop;


=== File: workbench-app/src/libs/useEnvironment.ts ===
// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { Constants } from '../Constants';
import { ServiceEnvironment } from '../models/ServiceEnvironment';
import { useAppSelector } from '../redux/app/hooks';
import { RootState } from '../redux/app/store';
import { Utility } from './Utility';

import debug from 'debug';

const log = debug(Constants.debug.root).extend('useEnvironment');

export const useEnvironment = () => {
    const environmentId = useAppSelector((state: RootState) => state.settings.environmentId);
    const [environment, setEnvironment] = React.useState<ServiceEnvironment>(getEnvironment(environmentId));

    React.useEffect(() => {
        const updatedEnvironment = getEnvironment(environmentId);
        if (!Utility.deepEqual(environment, updatedEnvironment)) {
            log('Environment changed', environment, updatedEnvironment);
            setEnvironment(updatedEnvironment);
        }
    }, [environment, environmentId]);

    return environment;
};

export const getEnvironment = (environmentId?: string): ServiceEnvironment => {
    if (environmentId) {
        const environment = Constants.service.environments.find((environment) => environment.id === environmentId);
        if (environment) {
            return transformEnvironment(environment);
        }
    }

    const defaultEnvironment = Constants.service.environments.find(
        (environment) => environment.id === Constants.service.defaultEnvironmentId,
    );
    if (defaultEnvironment) {
        return transformEnvironment(defaultEnvironment);
    }

    throw new Error('No default environment found. Check Constants.ts file.');
};

const transformEnvironment = (environment: ServiceEnvironment) => {
    if (window.location.hostname.includes('-4000.app.github.dev') && environment.id === 'local') {
        return {
            ...environment,
            url: window.location.origin.replace('-4000.app.github.dev', '-3000.app.github.dev'),
        };
    }

    return environment;
};


=== File: workbench-app/src/libs/useExportUtility.ts ===
import React from 'react';
import { useWorkbenchService } from './useWorkbenchService';

export const useExportUtility = () => {
    const workbenchService = useWorkbenchService();

    const exportContent = React.useCallback(
        async (id: string, exportFunction: (id: string) => Promise<{ blob: Blob; filename: string }>) => {
            const { blob, filename } = await exportFunction(id);
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            URL.revokeObjectURL(url);
        },
        [],
    );

    const exportConversationFunction = React.useCallback(
        async (conversationId: string) => {
            return await workbenchService.exportConversationsAsync([conversationId]);
        },
        [workbenchService],
    );

    const exportConversation = React.useCallback(
        async (conversationId: string) => {
            return await exportContent(conversationId, exportConversationFunction);
        },
        [exportContent, exportConversationFunction],
    );

    const exportAssistantFunction = React.useCallback(
        async (assistantId: string) => {
            return await workbenchService.exportAssistantAsync(assistantId);
        },
        [workbenchService],
    );

    const exportAssistant = React.useCallback(
        async (assistantId: string) => {
            return await exportContent(assistantId, exportAssistantFunction);
        },
        [exportContent, exportAssistantFunction],
    );

    return {
        exportContent,
        exportConversationFunction,
        exportConversation,
        exportAssistantFunction,
        exportAssistant,
    };
};


=== File: workbench-app/src/libs/useHistoryUtility.ts ===
import React from 'react';
import { ConversationMessage } from '../models/ConversationMessage';
import { useAppDispatch } from '../redux/app/hooks';
import {
    conversationApi,
    updateGetConversationMessagesQueryData,
    useGetConversationMessagesQuery,
    useGetAssistantsInConversationQuery,
    useGetConversationFilesQuery,
    useGetConversationParticipantsQuery,
    useGetConversationQuery,
    workbenchApi,
} from '../services/workbench';
import { useGetAssistantCapabilities } from './useAssistantCapabilities';
import { useConversationEvents } from './useConversationEvents';

export const useHistoryUtility = (conversationId: string) => {
    const dispatch = useAppDispatch();

    const {
        data: conversation,
        error: conversationError,
        isLoading: conversationIsLoading,
        refetch: refetchConversation,
    } = useGetConversationQuery(conversationId, { refetchOnMountOrArgChange: true });
    const {
        data: allConversationMessages,
        error: allConversationMessagesError,
        isLoading: allConversationMessagesIsLoading,
    } = useGetConversationMessagesQuery({
        conversationId,
    });
    const {
        data: conversationParticipants,
        error: conversationParticipantsError,
        isLoading: conversationParticipantsIsLoading,
        refetch: conversationParticipantsRefetch,
    } = useGetConversationParticipantsQuery(conversationId);
    const {
        data: assistants,
        error: assistantsError,
        isLoading: assistantsIsLoading,
        refetch: assistantsRefetch,
    } = useGetAssistantsInConversationQuery(conversationId);
    const {
        data: conversationFiles,
        error: conversationFilesError,
        isLoading: conversationFilesIsLoading,
    } = useGetConversationFilesQuery(conversationId);

    const { data: assistantCapabilities, isFetching: assistantCapabilitiesIsFetching } = useGetAssistantCapabilities(
        assistants ?? [],
        { skip: assistantsIsLoading || assistantsError !== undefined },
    );

    const error =
        conversationError ||
        allConversationMessagesError ||
        conversationParticipantsError ||
        assistantsError ||
        conversationFilesError;

    const isLoading =
        conversationIsLoading ||
        allConversationMessagesIsLoading ||
        conversationParticipantsIsLoading ||
        assistantsIsLoading ||
        conversationFilesIsLoading;

    // region Events

    // handler for when a new message is created
    const onMessageCreated = React.useCallback(async () => {
        dispatch(workbenchApi.util.invalidateTags(['ConversationMessage']));
    }, [dispatch]);

    // handler for when a message is deleted
    const onMessageDeleted = React.useCallback(
        (messageId: string) => {
            if (!allConversationMessages) {
                return;
            }

            const updatedMessages = allConversationMessages.filter((message) => message.id !== messageId);

            // remove the message from the messages state
            dispatch(updateGetConversationMessagesQueryData({ conversationId }, updatedMessages));
        },
        [allConversationMessages, conversationId, dispatch],
    );

    // handler for when a new participant is created
    const onParticipantCreated = React.useCallback(async () => {
        await conversationParticipantsRefetch();
    }, [conversationParticipantsRefetch]);

    // handler for when a participant is updated
    const onParticipantUpdated = React.useCallback(async () => {
        await conversationParticipantsRefetch();
    }, [conversationParticipantsRefetch]);

    // subscribe to conversation events
    useConversationEvents(conversationId, {
        onMessageCreated,
        onMessageDeleted,
        onParticipantCreated,
        onParticipantUpdated,
    });

    // endregion

    // region Rewind

    const rewindToBefore = React.useCallback(
        async (message: ConversationMessage, redo: boolean) => {
            if (!allConversationMessages) {
                return;
            }

            // find the index of the message to rewind to
            const messageIndex = allConversationMessages.findIndex(
                (possibleMessage) => possibleMessage.id === message.id,
            );

            // if the message is not found, do nothing
            if (messageIndex === -1) {
                return;
            }

            // delete all messages from the message to the end of the conversation
            for (let i = messageIndex; i < allConversationMessages.length; i++) {
                await dispatch(
                    conversationApi.endpoints.deleteConversationMessage.initiate({
                        conversationId,
                        messageId: allConversationMessages[i].id,
                    }),
                );
            }

            // if redo is true, create a new message with the same content as the message to redo
            if (redo) {
                await dispatch(
                    conversationApi.endpoints.createConversationMessage.initiate({
                        conversationId,
                        ...message,
                    }),
                );
            }
        },
        [allConversationMessages, conversationId, dispatch],
    );

    // endregion

    // add more messages related utility functions here, separated by region if applicable

    return {
        conversation,
        allConversationMessages,
        conversationParticipants,
        assistants,
        conversationFiles,
        assistantCapabilities,
        error,
        isLoading,
        assistantsRefetch,
        assistantCapabilitiesIsFetching,
        rewindToBefore,
        refetchConversation,
    };
};


=== File: workbench-app/src/libs/useKeySequence.ts ===
// Copyright (c) Microsoft. All rights reserved.
import React from 'react';

export const useKeySequence = (sequence: string[], onKeySequenceComplete: () => void) => {
    const buffer = React.useRef<string[]>([]);

    const keySequence = React.useCallback(
        (event: KeyboardEvent) => {
            if (event.defaultPrevented) return;

            if (event.key === sequence[buffer.current.length]) {
                buffer.current = [...buffer.current, event.key];
            } else {
                buffer.current = [];
            }

            if (buffer.current.length === sequence.length) {
                const bufferString = buffer.current.toString();
                const sequenceString = sequence.toString();

                if (sequenceString === bufferString) {
                    buffer.current = [];
                    onKeySequenceComplete();
                }
            }
        },
        [onKeySequenceComplete, sequence],
    );

    React.useEffect(() => {
        document.addEventListener('keydown', keySequence);
        return () => document.removeEventListener('keydown', keySequence);
    }, [keySequence]);
};


=== File: workbench-app/src/libs/useMediaQuery.ts ===
import React from 'react';

export const useMediaQuery = (config: MediaQueryConfig): boolean => {
    const query = buildMediaQuery(config);
    const [matches, setMatches] = React.useState<boolean>(false);

    React.useEffect(() => {
        const mediaQueryList = window.matchMedia(query);
        const documentChangeHandler = () => setMatches(mediaQueryList.matches);

        // Set the initial state
        documentChangeHandler();

        // Listen for changes
        mediaQueryList.addEventListener('change', documentChangeHandler);

        return () => {
            mediaQueryList.removeEventListener('change', documentChangeHandler);
        };
    }, [query]);

    return matches;
};

type MediaQueryConfig =
    | { minWidth: string | number }
    | { maxWidth: string | number }
    | { minHeight: string | number }
    | { maxHeight: string | number }
    | { query: string }
    | { orientation: 'portrait' | 'landscape' }
    | { resolution: 'high' }
    | { aspectRatio: 'wide' | 'tall' }
    | { device: 'screen' | 'print' };

export const buildMediaQuery = (config: MediaQueryConfig): string => {
    if ('minWidth' in config) {
        return `(min-width: ${typeof config.minWidth === 'number' ? `${config.minWidth}px` : config.minWidth})`;
    }
    if ('maxWidth' in config) {
        return `(max-width: ${typeof config.maxWidth === 'number' ? `${config.maxWidth}px` : config.maxWidth})`;
    }
    if ('minHeight' in config) {
        return `(min-height: ${typeof config.minHeight === 'number' ? `${config.minHeight}px` : config.minHeight})`;
    }
    if ('maxHeight' in config) {
        return `(max-height: ${typeof config.maxHeight === 'number' ? `${config.maxHeight}px` : config.maxHeight})`;
    }
    if ('query' in config) {
        return config.query;
    }
    if ('orientation' in config) {
        return `(orientation: ${config.orientation})`;
    }
    if ('resolution' in config) {
        return `(min-resolution: 2dppx)`;
    }
    if ('aspectRatio' in config) {
        return config.aspectRatio === 'wide' ? `(min-aspect-ratio: 16/9)` : `(max-aspect-ratio: 1/1)`;
    }
    if ('device' in config) {
        return config.device;
    }
    return '';
};


=== File: workbench-app/src/libs/useMicrosoftGraph.ts ===
// Copyright (c) Microsoft. All rights reserved.

import { InteractionRequiredAuthError } from '@azure/msal-browser';
import { useMsal } from '@azure/msal-react';
import { Client, ResponseType } from '@microsoft/microsoft-graph-client';
import React from 'react';
import { AuthHelper } from './AuthHelper';

export const useMicrosoftGraph = () => {
    const msal = useMsal();

    const getClientAsync = React.useCallback(async (): Promise<Client> => {
        const account = msal.instance.getActiveAccount();
        if (!account) {
            throw new Error('No active account');
        }

        const response = await msal.instance
            .acquireTokenSilent({
                ...AuthHelper.loginRequest,
                account,
            })
            .catch(async (error) => {
                if (error instanceof InteractionRequiredAuthError) {
                    return await AuthHelper.loginAsync(msal.instance);
                }
                throw error;
            });

        if (!response) {
            throw new Error('error acquiring access token');
        }

        return Client.init({
            authProvider: (done) => {
                done(null, response.accessToken);
            },
        });
    }, [msal]);

    const getAsync = React.useCallback(
        async <T>(url: string): Promise<T> => {
            const client = await getClientAsync();
            return (await client.api(url).get()) as T;
        },
        [getClientAsync],
    );

    const blobToBase64Async = React.useCallback(async (blob: Blob): Promise<string> => {
        return await new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onerror = reject;
            reader.onload = () => {
                resolve(reader.result as string);
            };
            reader.readAsDataURL(blob);
        });
    }, []);

    const getPhotoAsync = React.useCallback(
        async (url: string): Promise<string> => {
            const client = await getClientAsync();
            const response = (await client.api(url).responseType(ResponseType.RAW).get()) as Response;
            const blob = await response.blob();
            return await blobToBase64Async(blob);
        },
        [blobToBase64Async, getClientAsync],
    );

    const getMyPhotoAsync = React.useCallback(async (): Promise<string> => {
        return await getPhotoAsync('/me/photo/$value');
    }, [getPhotoAsync]);

    return {
        getAsync,
        getMyPhotoAsync,
    };
};


=== File: workbench-app/src/libs/useNotify.tsx ===
import {
    Slot,
    Toast,
    ToastBody,
    ToastFooter,
    ToastIntent,
    ToastTitle,
    ToastTrigger,
    useToastController,
} from '@fluentui/react-components';
import React from 'react';
import { Constants } from '../Constants';

interface NotifyOptions {
    id: string;
    title?: string;
    message: string;
    subtitle?: string;
    action?: Slot<'div'> | string;
    additionalActions?: React.ReactElement[];
    timeout?: number;
    intent: ToastIntent;
}

export const useNotify = (toasterId: string = Constants.app.globalToasterId) => {
    const { dispatchToast } = useToastController(toasterId);

    const notify = React.useCallback(
        (options: NotifyOptions) => {
            const { id, title, message, subtitle, action, additionalActions, timeout, intent } = options;

            const getAction = () => {
                if (typeof action === 'string') {
                    return (
                        <ToastTrigger>
                            <span>{action}</span>
                        </ToastTrigger>
                    );
                }
                return action;
            };

            dispatchToast(
                <Toast>
                    <ToastTitle action={getAction()}>{title}</ToastTitle>
                    <ToastBody subtitle={subtitle}>{message}</ToastBody>
                    {additionalActions && <ToastFooter>{additionalActions}</ToastFooter>}
                </Toast>,
                {
                    toastId: id,
                    timeout,
                    intent,
                },
            );
        },
        [dispatchToast],
    );

    const notifySuccess = React.useCallback(
        (options: Omit<NotifyOptions, 'intent'>) =>
            notify({
                ...options,
                intent: 'success',
            }),
        [notify],
    );

    const notifyInfo = React.useCallback(
        (options: Omit<NotifyOptions, 'intent'>) =>
            notify({
                ...options,
                intent: 'info',
            }),
        [notify],
    );

    const notifyWarning = React.useCallback(
        (options: Omit<NotifyOptions, 'intent'>) =>
            notify({
                ...options,
                intent: 'warning',
            }),
        [notify],
    );

    const notifyError = React.useCallback(
        (options: Omit<NotifyOptions, 'intent'>) =>
            notify({
                action: 'Dismiss',
                timeout: -1,
                ...options,
                intent: 'error',
            }),
        [notify],
    );

    return { notify, notifySuccess, notifyInfo, notifyError, notifyWarning };
};


=== File: workbench-app/src/libs/useParticipantUtility.tsx ===
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


=== File: workbench-app/src/libs/useSiteUtility.ts ===
// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { Constants } from '../Constants';

export const useSiteUtility = () => {
    const setDocumentTitle = React.useCallback((title?: string) => {
        document.title = title ? `${title} - ${Constants.app.name}` : Constants.app.name;
    }, []);

    const forceNavigateTo = React.useCallback((url: string | URL) => {
        window.history.pushState(null, '', url);
        window.location.reload();
    }, []);

    return {
        setDocumentTitle,
        forceNavigateTo,
    };
};


=== File: workbench-app/src/libs/useWorkbenchEventSource.ts ===
import { InteractionRequiredAuthError } from '@azure/msal-browser';
import { EventSourceMessage, EventStreamContentType, fetchEventSource } from '@microsoft/fetch-event-source';
import debug from 'debug';
import React from 'react';
import { Constants } from '../Constants';
import { getMsalInstance } from '../main';
import { AuthHelper } from './AuthHelper';
import { EventSubscriptionManager } from './EventSubscriptionManager';
import { useEnvironment } from './useEnvironment';

const log = debug(Constants.debug.root).extend('useWorkbenchEventSource');

class RetriableError extends Error {}
class FatalError extends Error {}

const useWorkbenchEventSource = (manager: EventSubscriptionManager, endpoint?: string) => {
    React.useEffect(() => {
        if (!endpoint) return;

        log(`Connecting event source: ${endpoint}`);

        const abortController = new AbortController();
        let isMounted = true;

        const startEventSource = async () => {
            if (!isMounted) return;

            const accessToken = await getAccessToken();
            const idToken = await getIdTokenAsync();

            // this promise is intentionally not awaited. it runs in the background and is cancelled when
            // the control is aborted or an error occurs.
            fetchEventSource(endpoint, {
                signal: abortController.signal,
                openWhenHidden: true,
                headers: {
                    Authorization: `Bearer ${accessToken}`,
                    'X-OpenIdToken': idToken,
                },
                async onopen(response) {
                    if (!isMounted) return;
                    if (response.ok && response.headers.get('content-type')?.includes(EventStreamContentType)) {
                        log(`Event source connected: ${response.status} ${response.statusText} [${response.url}]`);
                        return; // everything's good
                    } else if (response.status >= 400 && response.status < 500 && response.status !== 429) {
                        // client-side errors are usually non-retriable:
                        log(`Event source error: ${response.status} ${response.statusText} [${response.url}]`);
                        throw new FatalError();
                    } else {
                        log(`Event source error: ${response.status} ${response.statusText} [${response.url}]`);
                        throw new RetriableError();
                    }
                },
                onmessage(message: EventSourceMessage) {
                    if (!message.event) return;
                    if (message.event === 'FatalError') {
                        throw new FatalError();
                    }
                    manager.emit(message.event, message);
                },
                onclose() {
                    if (!isMounted) return;
                    log(`Event source closed unexpectedly: ${endpoint}`);
                    throw new RetriableError();
                },
                onerror(error) {
                    if (!isMounted) return;
                    log(`Event source error: ${error} [${endpoint}]`);
                    if (error instanceof FatalError) {
                        // fatal errors are not retried
                        throw error; // rethrow to stop the event source
                    }
                    // will retry
                },
            });
        };

        startEventSource();

        return () => {
            log(`Disconnecting event source: ${endpoint}`);
            isMounted = false;
            abortController.abort();
        };
    }, [endpoint, manager]);
};

const getAccessToken = async (forceRefresh?: boolean) => {
    const msalInstance = await getMsalInstance();

    const account = msalInstance.getActiveAccount();
    if (!account) {
        throw new Error('No active account');
    }

    const response = await msalInstance
        .acquireTokenSilent({
            ...AuthHelper.loginRequest,
            account,
            forceRefresh,
        })
        .catch(async (error) => {
            if (error instanceof InteractionRequiredAuthError) {
                return await AuthHelper.loginAsync(msalInstance);
            }
            throw error;
        });
    if (!response) {
        throw new Error('Could not acquire access token');
    }

    return response.accessToken;
};

const getIdTokenAsync = async (forceRefresh?: boolean) => {
    const msalInstance = await getMsalInstance();

    const account = msalInstance.getActiveAccount();
    if (!account) {
        throw new Error('No active account');
    }

    const response = await msalInstance
        .acquireTokenSilent({
            ...AuthHelper.loginRequest,
            account,
            forceRefresh,
        })
        .catch(async (error) => {
            if (error instanceof InteractionRequiredAuthError) {
                return await AuthHelper.loginAsync(msalInstance);
            }
            throw error;
        });
    if (!response) {
        throw new Error('Could not acquire ID token');
    }

    return response.idToken;
};

export const useWorkbenchUserEventSource = (manager: EventSubscriptionManager) => {
    const environment = useEnvironment();
    const [endpoint, setEndpoint] = React.useState<string>();

    React.useEffect(() => {
        setEndpoint(`${environment.url}/events`);
    }, [environment]);

    return useWorkbenchEventSource(manager, endpoint);
};

export const useWorkbenchConversationEventSource = (manager: EventSubscriptionManager, conversationId?: string) => {
    const environment = useEnvironment();
    const [endpoint, setEndpoint] = React.useState<string>();

    React.useEffect(() => {
        setEndpoint(conversationId ? `${environment.url}/conversations/${conversationId}/events` : undefined);
    }, [environment, conversationId]);

    useWorkbenchEventSource(manager, endpoint);
};


=== File: workbench-app/src/libs/useWorkbenchService.ts ===
// Copyright (c) Microsoft. All rights reserved.

import { InteractionRequiredAuthError } from '@azure/msal-browser';
import { useAccount, useMsal } from '@azure/msal-react';
import React from 'react';
import { AssistantServiceInfo } from '../models/AssistantServiceInfo';
import { AssistantServiceRegistration } from '../models/AssistantServiceRegistration';
import { Conversation } from '../models/Conversation';
import { ConversationFile } from '../models/ConversationFile';
import { ConversationParticipant } from '../models/ConversationParticipant';
import { useAppDispatch } from '../redux/app/hooks';
import { addError } from '../redux/features/app/appSlice';
import { assistantServiceApi, conversationApi, workbenchApi } from '../services/workbench';
import { AuthHelper } from './AuthHelper';
import { Utility } from './Utility';
import { useEnvironment } from './useEnvironment';

export const useWorkbenchService = () => {
    const environment = useEnvironment();
    const dispatch = useAppDispatch();
    const account = useAccount();
    const msal = useMsal();

    const getAccessTokenAsync = React.useCallback(async () => {
        if (!account) {
            throw new Error('No active account');
        }

        const response = await msal.instance
            .acquireTokenSilent({
                ...AuthHelper.loginRequest,
                account,
            })
            .catch(async (error) => {
                if (error instanceof InteractionRequiredAuthError) {
                    return await AuthHelper.loginAsync(msal.instance);
                }
                throw error;
            });
        if (!response) {
            dispatch(addError({ title: 'Failed to acquire token', message: 'Could not acquire access token' }));
            throw new Error('Could not acquire access token');
        }
        return response.accessToken;
    }, [account, dispatch, msal.instance]);

    const getIdTokenAsync = React.useCallback(async () => {
        if (!account) {
            throw new Error('No active account');
        }

        const response = await msal.instance
            .acquireTokenSilent({
                ...AuthHelper.loginRequest,
                account,
            })
            .catch(async (error) => {
                if (error instanceof InteractionRequiredAuthError) {
                    return await AuthHelper.loginAsync(msal.instance);
                }
                throw error;
            });
        if (!response) {
            dispatch(addError({ title: 'Failed to acquire ID token', message: 'Could not acquire token' }));
            throw new Error('Could not acquire ID token');
        }
        return response.idToken;
    }, [account, dispatch, msal.instance]);

    const tryFetchAsync = React.useCallback(
        async (operationTitle: string, url: string, options?: RequestInit): Promise<Response> => {
            const accessToken = await getAccessTokenAsync();
            const idToken = await getIdTokenAsync();
            const response = await fetch(url, {
                ...options,
                headers: {
                    ...options?.headers,
                    Authorization: `Bearer ${accessToken}`,
                    'X-OpenIdToken': idToken,
                },
            });

            if (!response.ok) {
                const json = await response.json();
                const message = json?.detail ?? json?.detail ?? response.statusText;
                dispatch(addError({ title: operationTitle, message }));
                throw new Error(`Failed to ${operationTitle}: ${message}`);
            }

            return response;
        },
        [dispatch, getAccessTokenAsync, getIdTokenAsync],
    );

    const tryFetchStreamAsync = React.useCallback(
        async (operationTitle: string, url: string, options?: RequestInit): Promise<Response> => {
            const accessToken = await getAccessTokenAsync();
            const idToken = await getIdTokenAsync();
            const response = await fetch(url, {
                ...options,
                headers: {
                    ...options?.headers,
                    Authorization: `Bearer ${accessToken}`,
                    'X-OpenIdToken': idToken,
                },
            });

            if (!response.ok) {
                const json = await response.json();
                const message = json?.detail ?? json?.detail ?? response.statusText;
                dispatch(addError({ title: operationTitle, message }));
                throw new Error(`Failed to ${operationTitle}: ${message}`);
            }

            return response;
        },
        [dispatch, getAccessTokenAsync, getIdTokenAsync],
    );

    const tryFetchFileAsync = React.useCallback(
        async (
            operationTitle: string,
            path: string,
            defaultFilename: string,
        ): Promise<{ blob: Blob; filename: string }> => {
            const response = await tryFetchAsync(operationTitle, `${environment.url}${path}`);
            const blob = await response.blob();
            return {
                blob,
                filename:
                    response.headers.get('Content-Disposition')?.split('filename=')[1].replaceAll('"', '') ??
                    defaultFilename,
            };
        },
        [environment.url, tryFetchAsync],
    );

    const getAzureSpeechTokenAsync = React.useCallback(async (): Promise<{ token: string; region: string }> => {
        const response = await tryFetchAsync('Get Azure Speech token', `${environment.url}/azure-speech/token`);
        const json = await response.json();
        return { token: json.token ?? '', region: json.region ?? '' };
    }, [environment.url, tryFetchAsync]);

    const downloadConversationFileAsync = React.useCallback(
        async (conversationId: string, conversationFile: ConversationFile): Promise<Response> => {
            const path = `/conversations/${conversationId}/files/${conversationFile.name}`;
            return await tryFetchStreamAsync('Download conversation file', `${environment.url}${path}`);
        },
        [environment.url, tryFetchStreamAsync],
    );

    const exportTranscriptAsync = React.useCallback(
        async (
            conversation: Conversation,
            participants: ConversationParticipant[],
        ): Promise<{ blob: Blob; filename: string }> => {
            const messages = await dispatch(
                conversationApi.endpoints.getConversationMessages.initiate({
                    conversationId: conversation.id,
                }),
            ).unwrap();

            const timestampForFilename = Utility.getTimestampForFilename();
            const filename = `transcript_${conversation.title.replaceAll(' ', '_')}_${timestampForFilename}.md`;

            const markdown = messages
                .filter((message) => message.messageType !== 'log')
                .map((message) => {
                    const date = Utility.toFormattedDateString(message.timestamp, 'dddd, MMMM D');
                    const time = Utility.toFormattedDateString(message.timestamp, 'h:mm A');
                    const participant = participants.find(
                        (possible_participant) => possible_participant.id === message.sender.participantId,
                    );
                    const sender = participant ? participant.name : 'Unknown';
                    const parts = [];
                    parts.push(`### [${date} ${time}] ${sender}:`);
                    if (message.messageType !== 'chat') {
                        // truncate long messages
                        const trimToLength = 1000;
                        const content =
                            message.content.length > trimToLength
                                ? `${message.content.slice(0, trimToLength)}... <truncated>`
                                : message.content;
                        parts.push(`${message.messageType}: ${content}`);
                    } else {
                        parts.push(message.content);
                    }
                    if (message.filenames && message.filenames.length > 0) {
                        parts.push(
                            message.filenames
                                .map((filename) => {
                                    return `attachment: ${filename}`;
                                })
                                .join('\n'),
                        );
                    }
                    parts.push('----------------------------------\n\n');

                    return parts.join('\n\n');
                })
                .join('\n');

            const blob = new Blob([markdown], { type: 'text/markdown' });

            return { blob, filename };
        },
        [dispatch],
    );

    const exportConversationsAsync = React.useCallback(
        async (conversationIds: string[]): Promise<{ blob: Blob; filename: string }> => {
            const response = await tryFetchAsync(
                'Export conversations',
                `${environment.url}/conversations/export?id=${conversationIds.join(',')}`,
            );

            // file comes back as an attachment with the name available in the content-disposition header
            const contentDisposition = response.headers.get('Content-Disposition');
            const filename = contentDisposition?.split('filename=')[1].replaceAll('"', '');
            const blob = await response.blob();
            return { blob, filename: filename || 'conversation-export.zip' };
        },
        [environment.url, tryFetchAsync],
    );

    const importConversationsAsync = React.useCallback(
        async (exportData: File): Promise<{ assistantIds: string[]; conversationIds: string[] }> => {
            const formData = new FormData();
            formData.append('from_export', exportData);

            const response = await tryFetchAsync(
                'Import assistants and conversations',
                `${environment.url}/conversations/import`,
                {
                    method: 'POST',
                    body: formData,
                },
            );

            try {
                const json = await response.json();
                return {
                    conversationIds: json.conversation_ids as string[],
                    assistantIds: json.assistant_ids as string[],
                };
            } catch (error) {
                dispatch(addError({ title: 'Import assistants and conversations', message: (error as Error).message }));
                throw error;
            } finally {
                // conversation imports can include assistants and conversations
                dispatch(workbenchApi.util.invalidateTags(['Assistant', 'Conversation']));
            }
        },
        [dispatch, environment.url, tryFetchAsync],
    );

    const exportThenImportConversationAsync = React.useCallback(
        async (conversationIds: string[]) => {
            const { blob, filename } = await exportConversationsAsync(conversationIds);
            const result = await importConversationsAsync(new File([blob], filename));
            return result.conversationIds;
        },
        [exportConversationsAsync, importConversationsAsync],
    );

    const exportAssistantAsync = React.useCallback(
        async (
            assistantId: string,
        ): Promise<{
            blob: Blob;
            filename: string;
        }> => {
            const path = `/assistants/${assistantId}/export`;
            return await tryFetchFileAsync('Export assistant', path, 'assistant-export.zip');
        },
        [tryFetchFileAsync],
    );

    const exportThenImportAssistantAsync = React.useCallback(
        async (assistantId: string) => {
            const { blob, filename } = await exportAssistantAsync(assistantId);
            const result = await importConversationsAsync(new File([blob], filename));
            return result.assistantIds[0];
        },
        [exportAssistantAsync, importConversationsAsync],
    );

    const getAssistantServiceInfoAsync = React.useCallback(
        async (assistantServiceId: string): Promise<AssistantServiceInfo | undefined> => {
            const results = await dispatch(
                assistantServiceApi.endpoints.getAssistantServiceInfo.initiate(assistantServiceId),
            );
            if (results.isError) {
                throw results.error;
            }
            return results.data;
        },
        [dispatch],
    );

    const getAssistantServiceRegistrationAsync = React.useCallback(
        async (assistantServiceId: string): Promise<AssistantServiceRegistration | undefined> => {
            const results = await dispatch(
                assistantServiceApi.endpoints.getAssistantServiceRegistration.initiate(assistantServiceId),
            );
            if (results.isError) {
                throw results.error;
            }
            return results.data;
        },
        [dispatch],
    );

    const getAssistantServiceInfosAsync = React.useCallback(
        async (assistantServiceIds: string[]): Promise<Array<AssistantServiceInfo | undefined>> => {
            return await Promise.all(
                assistantServiceIds.map(async (assistantServiceId) => {
                    try {
                        const registration = await getAssistantServiceRegistrationAsync(assistantServiceId);
                        if (!registration?.assistantServiceOnline) {
                            return undefined;
                        }
                    } catch (error) {
                        return undefined;
                    }
                    try {
                        return await getAssistantServiceInfoAsync(assistantServiceId);
                    } catch (error) {
                        return undefined;
                    }
                }),
            );
        },
        [getAssistantServiceInfoAsync, getAssistantServiceRegistrationAsync],
    );

    return {
        getAzureSpeechTokenAsync,
        downloadConversationFileAsync,
        exportTranscriptAsync,
        exportConversationsAsync,
        importConversationsAsync,
        exportThenImportConversationAsync,
        exportAssistantAsync,
        exportThenImportAssistantAsync,
        getAssistantServiceInfoAsync,
        getAssistantServiceInfosAsync,
    };
};


=== File: workbench-app/src/main.tsx ===
import { AuthenticationResult, EventType, PublicClientApplication } from '@azure/msal-browser';
import { AuthenticatedTemplate, MsalProvider, UnauthenticatedTemplate } from '@azure/msal-react';
import { CopilotProvider } from '@fluentui-copilot/react-copilot';
import { FluentProvider } from '@fluentui/react-components';
import { initializeFileTypeIcons } from '@fluentui/react-file-type-icons';
import debug from 'debug';
import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider as ReduxProvider } from 'react-redux';
import { RouterProvider, createBrowserRouter } from 'react-router-dom';
import { Constants } from './Constants';
import { Root } from './Root';
import './index.css';
import { AuthHelper } from './libs/AuthHelper';
import { Theme } from './libs/Theme';
import { getEnvironment } from './libs/useEnvironment';
import { store } from './redux/app/store';
import { AcceptTerms } from './routes/AcceptTerms';
import { AssistantEditor } from './routes/AssistantEditor';
import { AssistantServiceRegistrationEditor } from './routes/AssistantServiceRegistrationEditor';
import { Dashboard } from './routes/Dashboard';
import { ErrorPage } from './routes/ErrorPage';
import { FrontDoor } from './routes/FrontDoor';
import { Login } from './routes/Login';
import { Settings } from './routes/Settings';
import { ShareRedeem } from './routes/ShareRedeem';
import { Shares } from './routes/Shares';

// Enable debug logging for the app
localStorage.setItem('debug', `${Constants.debug.root}:*`);

const log = debug(Constants.debug.root).extend('main');

const unauthenticatedRouter = createBrowserRouter([
    {
        path: '/',
        element: <Root />,
        errorElement: <ErrorPage />,
        children: [
            {
                // This is the default route, it should not include a path
                index: true,
                element: <Login />,
            },
            {
                path: '/terms',
                element: <AcceptTerms />,
            },
            {
                // This is the catch-all route, it should be the last route
                path: '/*',
                element: <Login />,
            },
        ],
    },
]);

const authenticatedRouter = createBrowserRouter([
    {
        path: '/',
        element: <Root />,
        errorElement: <ErrorPage />,
        children: [
            {
                index: true,
                element: <FrontDoor />,
            },
            {
                path: '/:conversationId?',
                element: <FrontDoor />,
            },
            {
                path: '/dashboard',
                element: <Dashboard />,
            },
            {
                path: '/settings',
                element: <Settings />,
            },
            {
                path: '/shares',
                element: <Shares />,
            },
            {
                path: '/assistant/:assistantId/edit',
                element: <AssistantEditor />,
            },
            {
                path: '/assistant-service-registration/:assistantServiceRegistrationId/edit',
                element: <AssistantServiceRegistrationEditor />,
            },
            {
                path: '/conversation-share/:conversationShareId/redeem',
                element: <ShareRedeem />,
            },
            {
                path: '/terms',
                element: <AcceptTerms />,
            },
        ],
    },
]);

const msalInstance = new PublicClientApplication(AuthHelper.getMsalConfig());

const accounts = msalInstance.getAllAccounts();
if (accounts.length > 0) {
    msalInstance.setActiveAccount(accounts[0]);
}

msalInstance.addEventCallback((event) => {
    if (event.eventType === EventType.LOGIN_SUCCESS && event.payload) {
        const payload = event.payload as AuthenticationResult;
        msalInstance.setActiveAccount(payload.account);
    }
});

export const getMsalInstance = async () => {
    await msalInstance.initialize();
    return msalInstance;
};

const customTheme = Theme.getCustomTheme('light', getEnvironment(store.getState().settings.environmentId)?.brand);

initializeFileTypeIcons();

let container: HTMLElement | null = null;
document.addEventListener('DOMContentLoaded', () => {
    if (!container) {
        container = document.getElementById('root');
        if (!container) {
            throw new Error('Could not find root element');
        }
        const root = ReactDOM.createRoot(container);

        const app = (
            <ReduxProvider store={store}>
                <MsalProvider instance={msalInstance}>
                    <FluentProvider className="app-container" theme={customTheme}>
                        <CopilotProvider mode="canvas">
                            <UnauthenticatedTemplate>
                                <RouterProvider router={unauthenticatedRouter} />
                            </UnauthenticatedTemplate>
                            <AuthenticatedTemplate>
                                <RouterProvider router={authenticatedRouter} />
                            </AuthenticatedTemplate>
                        </CopilotProvider>
                    </FluentProvider>
                </MsalProvider>
            </ReduxProvider>
        );

        // NOTE: React.StrictMode is used to help catch common issues in the app but will also double-render
        // components.If you want to verify that any double rendering is coming from this, you can disable
        // React.StrictMode by setting the env var VITE_DISABLE_STRICT_MODE = true. Please note that this
        // will also disable the double-render check, so only use this for debugging purposes and make sure
        // to test with React.StrictMode enabled before committing any changes.

        // Can be overridden by env var VITE_DISABLE_STRICT_MODE
        const disableStrictMode = import.meta.env.VITE_DISABLE_STRICT_MODE === 'true';

        let startLogMessage = 'starting app';
        if (import.meta.env.DEV) {
            startLogMessage = `${startLogMessage} in development mode`;
            startLogMessage = `${startLogMessage} [strict mode: ${disableStrictMode ? 'disabled' : 'enabled'}]`;
        }

        log(startLogMessage);
        root.render(disableStrictMode ? app : <React.StrictMode>{app}</React.StrictMode>);
    }
});


=== File: workbench-app/src/models/Assistant.ts ===
// Copyright (c) Microsoft. All rights reserved.

export type Assistant = {
    id: string;
    name: string;
    image?: string;
    assistantServiceId: string;
    assistantServiceOnline: boolean;
    templateId: string;
    createdDatetime: string;
    conversations: {
        [additionalPropertyId: string]: {
            id: string;
        };
    };
    commands?: {
        [commandName: string]: {
            displayName: string;
            description: string;
        };
    };
    states?: {
        [stateKey: string]: {
            displayName: string;
            description: string;
        };
    };
    metadata?: {
        [key: string]: any;
    };
};


=== File: workbench-app/src/models/AssistantCapability.ts ===
export enum AssistantCapability {
    SupportsConversationFiles = 'supports_conversation_files',
}


=== File: workbench-app/src/models/AssistantServiceInfo.ts ===
// Copyright (c) Microsoft. All rights reserved.

import { Config } from './Config';

export interface AssistantTemplate {
    id: string;
    name: string;
    description: string;
    defaultConfig: Config;
}

export interface AssistantServiceInfo {
    assistantServiceId: string;
    templates: AssistantTemplate[];
    metadata: {
        [key: string]: any;
    };
}


=== File: workbench-app/src/models/AssistantServiceRegistration.ts ===
// Copyright (c) Microsoft. All rights reserved.

export interface NewAssistantServiceRegistration {
    assistantServiceId: string;
    name: string;
    description: string;
    includeInListing: boolean;
}

export interface AssistantServiceRegistration {
    assistantServiceId: string;
    assistantServiceOnline: boolean;
    assistantServiceUrl: string;
    name: string;
    description: string;
    includeInListing: boolean;
    createdDateTime: string;
    createdByUserId: string;
    createdByUserName: string;
    apiKeyName: string;
    apiKey?: string;
}


=== File: workbench-app/src/models/Config.ts ===
// Copyright (c) Microsoft. All rights reserved.

import { RJSFSchema, UiSchema } from '@rjsf/utils';

export type Config = {
    config: object;
    jsonSchema?: RJSFSchema;
    uiSchema?: UiSchema;
};


=== File: workbench-app/src/models/Conversation.ts ===
// Copyright (c) Microsoft. All rights reserved.

import { ConversationMessage } from './ConversationMessage';
import { ConversationParticipant } from './ConversationParticipant';

export interface Conversation {
    id: string;
    ownerId: string;
    title: string;
    created: string;
    latest_message?: ConversationMessage;
    participants: ConversationParticipant[];
    metadata: {
        [key: string]: any;
    };
    conversationPermission: 'read' | 'read_write';
    importedFromConversationId?: string;
}


=== File: workbench-app/src/models/ConversationFile.ts ===
// Copyright (c) Microsoft. All rights reserved.

export interface ConversationFile {
    name: string;
    created: string;
    updated: string;
    size: number;
    version: number;
    contentType: string;
    metadata: {
        [key: string]: any;
    };
}


=== File: workbench-app/src/models/ConversationMessage.ts ===
// Copyright (c) Microsoft. All rights reserved.

export interface ConversationMessage {
    id: string;
    sender: {
        participantId: string;
        participantRole: string;
    };
    timestamp: string;
    content: string;
    messageType: string;
    contentType: string;
    filenames?: string[];
    metadata?: {
        [key: string]: any;
    };
    hasDebugData: boolean;
}

export const conversationMessageFromJSON = (json: any): ConversationMessage => {
    return {
        id: json.id,
        sender: {
            participantId: json.sender.participant_id,
            participantRole: json.sender.participant_role,
        },
        timestamp: json.timestamp,
        content: json.content,
        messageType: json.message_type,
        contentType: json.content_type,
        filenames: json.filenames,
        metadata: json.metadata,
        hasDebugData: json.has_debug_data,
    };
};


=== File: workbench-app/src/models/ConversationMessageDebug.ts ===
// Copyright (c) Microsoft. All rights reserved.

export interface ConversationMessageDebug {
    id: string;
    debugData: {
        [key: string]: any;
    };
}

export const conversationMessageDebugFromJSON = (json: any): ConversationMessageDebug => {
    return {
        id: json.id,
        debugData: json.debug_data,
    };
};


=== File: workbench-app/src/models/ConversationParticipant.ts ===
// Copyright (c) Microsoft. All rights reserved.

export interface ConversationParticipant {
    role: 'user' | 'assistant' | 'service';
    id: string;
    conversationId: string;
    name: string;
    image?: string;
    online?: boolean;
    status: string | null;
    statusTimestamp: string | null;
    conversationPermission: 'read' | 'read_write';
    active: boolean;
    metadata: {
        [key: string]: any;
    };
}


=== File: workbench-app/src/models/ConversationShare.ts ===
// Copyright (c) Microsoft. All rights reserved.

import { User } from './User';

export interface ConversationShare {
    id: string;
    createdByUser: User;
    label: string;
    conversationId: string;
    conversationTitle: string;
    conversationPermission: 'read' | 'read_write';
    isRedeemable: boolean;
    createdDateTime: string;
    metadata: {
        [key: string]: any;
    };
}


=== File: workbench-app/src/models/ConversationShareRedemption.ts ===
// Copyright (c) Microsoft. All rights reserved.

import { User } from './User';

export interface ConversationShareRedemption {
    id: string;
    conversationShareId: string;
    conversationId: string;
    redeemedByUser: User;
    conversationPermission: 'read' | 'read_write';
    createdDateTime: string;
    isNewParticipant: boolean;
}


=== File: workbench-app/src/models/ConversationState.ts ===
// Copyright (c) Microsoft. All rights reserved.

import { RJSFSchema, UiSchema } from '@rjsf/utils';

export type ConversationState = {
    id: string;
    data: object;
    jsonSchema?: RJSFSchema;
    uiSchema?: UiSchema;
};


=== File: workbench-app/src/models/ConversationStateDescription.ts ===
// Copyright (c) Microsoft. All rights reserved.

export interface ConversationStateDescription {
    id: string;
    displayName: string;
    description: string;
    enabled: boolean;
}


=== File: workbench-app/src/models/ServiceEnvironment.ts ===
// Copyright (c) Microsoft. All rights reserved.

export interface ServiceEnvironment {
    id: string;
    name: string;
    url: string;
    brand?: string;
}


=== File: workbench-app/src/models/User.ts ===
// Copyright (c) Microsoft. All rights reserved.

export interface User {
    id: string;
    name: string;
    image?: string;
}


=== File: workbench-app/src/redux/app/hooks.ts ===
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from './store';

// Use throughout your app instead of plain `useDispatch` and `useSelector`
export const useAppDispatch: () => AppDispatch = useDispatch;
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;


=== File: workbench-app/src/redux/app/rtkQueryErrorLogger.ts ===
// Copyright (c) Microsoft. All rights reserved.
import type { Middleware, MiddlewareAPI } from '@reduxjs/toolkit';
import { isRejectedWithValue } from '@reduxjs/toolkit';
import { addError } from '../features/app/appSlice';

import debug from 'debug';
import { Constants } from '../../Constants';
import { Utility } from '../../libs/Utility';
import { store } from './store';

const log = debug(Constants.debug.root).extend('rtk-query-error-logger');

// Middleware for all RTK Query actions
export const rtkQueryErrorLogger: Middleware = (_api: MiddlewareAPI) => (next) => (action) => {
    // Check if the action is a rejected action with a value
    if (isRejectedWithValue(action.payload)) {
        // Set the title for the error message, displayed as a prefix to the error message
        const title = 'Service error';

        // Set the message for the error message, displayed as the error details
        const message = Utility.errorToMessageString(action);

        // Dispatch the error to the store to cause the error message to be displayed
        // in the header area of the Semantic Workbench UI
        store.dispatch(addError({ title, message }));

        // Additionally, log the error to the console for debugging purposes
        log(title, action.payload);
    }

    // Continue with the next action
    return next(action);
};


=== File: workbench-app/src/redux/app/store.ts ===
import { Action, ThunkAction, configureStore } from '@reduxjs/toolkit';
import { workbenchApi } from '../../services/workbench';
import appReducer from '../features/app/appSlice';
import chatCanvasReducer from '../features/chatCanvas/chatCanvasSlice';
import localUserReducer from '../features/localUser/localUserSlice';
import settingsReducer from '../features/settings/settingsSlice';
import { rtkQueryErrorLogger } from './rtkQueryErrorLogger';

export const store = configureStore({
    reducer: {
        app: appReducer,
        chatCanvas: chatCanvasReducer,
        localUser: localUserReducer,
        settings: settingsReducer,
        [workbenchApi.reducerPath]: workbenchApi.reducer,
    },
    middleware: (getDefaultMiddleware) => getDefaultMiddleware().concat(workbenchApi.middleware, rtkQueryErrorLogger),
});

export type AppDispatch = typeof store.dispatch;
export type RootState = ReturnType<typeof store.getState>;
export type AppThunk<ReturnType = void> = ThunkAction<ReturnType, RootState, unknown, Action<string>>;


=== File: workbench-app/src/redux/features/app/AppState.ts ===
// Copyright (c) Microsoft. All rights reserved.

export interface AppState {
    // persisted
    devMode: boolean;
    completedFirstRun: {
        app: boolean;
        experimental: boolean;
    };
    hideExperimentalNotice: boolean;
    chatWidthPercent: number;
    globalContentOpen: boolean;
    // transient
    isDraggingOverBody?: boolean;
    activeConversationId?: string;
    errors: {
        id: string;
        title?: string;
        message?: string;
    }[];
}


=== File: workbench-app/src/redux/features/app/appSlice.ts ===
// Copyright (c) Microsoft. All rights reserved.

import { generateUuid } from '@azure/ms-rest-js';
import { PayloadAction, createSlice } from '@reduxjs/toolkit';
import { Constants } from '../../../Constants';
import { AppStorage } from '../../../libs/AppStorage';
import { workbenchApi } from '../../../services/workbench';
import { AppState } from './AppState';

const localStorageKey = {
    devMode: 'app.dev-mode',
    completedFirstRunApp: 'app.completed-first-run.app',
    completedFirstRunExperimental: 'app.completed-first-run.experimental',
    hideExperimentalNotice: 'app.hide-experimental-notice',
    chatWidthPercent: 'app.chat-width-percent',
    globalContentOpen: 'app.global-content-open',
};

const initialState: AppState = {
    devMode: localStorage.getItem(localStorageKey.devMode) === 'true',
    errors: [],
    chatWidthPercent:
        AppStorage.getInstance().loadObject<number>(localStorageKey.chatWidthPercent) ??
        Constants.app.defaultChatWidthPercent,
    completedFirstRun: {
        app: AppStorage.getInstance().loadObject<boolean>(localStorageKey.completedFirstRunApp) ?? false,
        experimental:
            AppStorage.getInstance().loadObject<boolean>(localStorageKey.completedFirstRunExperimental) ?? false,
    },
    hideExperimentalNotice:
        AppStorage.getInstance().loadObject<boolean>(localStorageKey.hideExperimentalNotice) ?? false,
    globalContentOpen: AppStorage.getInstance().loadObject<boolean>(localStorageKey.globalContentOpen) ?? false,
};

export const appSlice = createSlice({
    name: 'app',
    initialState,
    reducers: {
        toggleDevMode: (state: AppState) => {
            state.devMode = !state.devMode;
            AppStorage.getInstance().saveObject(localStorageKey.devMode, state.devMode);
        },
        setIsDraggingOverBody: (state: AppState, action: PayloadAction<boolean>) => {
            state.isDraggingOverBody = action.payload;
        },
        addError: (state: AppState, action: PayloadAction<{ title?: string; message?: string }>) => {
            // exit if matching error already exists
            if (
                state.errors?.some(
                    (error) => error.title === action.payload.title && error.message === action.payload.message,
                )
            ) {
                return;
            }

            // add error
            state.errors?.push({
                id: generateUuid(),
                title: action.payload.title,
                message: action.payload.message,
            });
        },
        removeError: (state: AppState, action: PayloadAction<string>) => {
            state.errors = state.errors?.filter((error) => error.id !== action.payload);
        },
        clearErrors: (state: AppState) => {
            state.errors = [];
        },
        setChatWidthPercent: (state: AppState, action: PayloadAction<number>) => {
            AppStorage.getInstance().saveObject(localStorageKey.chatWidthPercent, action.payload);
            state.chatWidthPercent = action.payload;
        },
        setCompletedFirstRun: (state: AppState, action: PayloadAction<{ app?: boolean; experimental?: boolean }>) => {
            if (action.payload.app !== undefined) {
                AppStorage.getInstance().saveObject(localStorageKey.completedFirstRunApp, action.payload.app);
                state.completedFirstRun.app = action.payload.app;
            }
            if (action.payload.experimental !== undefined) {
                AppStorage.getInstance().saveObject(
                    localStorageKey.completedFirstRunExperimental,
                    action.payload.experimental,
                );
                state.completedFirstRun.experimental = action.payload.experimental;
            }
        },
        setHideExperimentalNotice: (state: AppState, action: PayloadAction<boolean>) => {
            AppStorage.getInstance().saveObject(localStorageKey.hideExperimentalNotice, action.payload);
            state.hideExperimentalNotice = action.payload;
        },
        setActiveConversationId: (state: AppState, action: PayloadAction<string | undefined>) => {
            if (action.payload === state.activeConversationId) {
                return;
            }
            state.activeConversationId = action.payload;

            // dispatch to invalidate messages cache
            if (action.payload) {
                workbenchApi.util.invalidateTags(['ConversationMessage']);
            }
        },
        setGlobalContentOpen: (state: AppState, action: PayloadAction<boolean>) => {
            AppStorage.getInstance().saveObject(localStorageKey.globalContentOpen, action.payload);
            state.globalContentOpen = action.payload;
        },
    },
});

export const {
    toggleDevMode,
    setIsDraggingOverBody,
    addError,
    removeError,
    clearErrors,
    setChatWidthPercent,
    setCompletedFirstRun,
    setHideExperimentalNotice,
    setActiveConversationId,
    setGlobalContentOpen,
} = appSlice.actions;

export default appSlice.reducer;


=== File: workbench-app/src/redux/features/chatCanvas/ChatCanvasState.ts ===
// Copyright (c) Microsoft. All rights reserved.

export interface ChatCanvasState {
    // persisted
    open: boolean;
    mode: 'conversation' | 'assistant';
    selectedAssistantId?: string;
    selectedAssistantStateId?: string;
}


=== File: workbench-app/src/redux/features/chatCanvas/chatCanvasSlice.ts ===
// Copyright (c) Microsoft. All rights reserved.

import { PayloadAction, createSlice } from '@reduxjs/toolkit';
import { AppStorage } from '../../../libs/AppStorage';
import { ChatCanvasState } from './ChatCanvasState';

const localStorageKey = {
    chatCanvasOpen: 'chat-canvas.open',
    chatCanvasMode: 'chat-canvas.mode',
    chatCanvasSelectedAssistantId: 'chat-canvas.selected-assistant-id',
    chatCanvasSelectedAssistantStateId: 'chat-canvas.selected-assistant-state-id',
};

const initialState: ChatCanvasState = {
    open: localStorage.getItem(localStorageKey.chatCanvasOpen) === 'true',
    mode: localStorage.getItem(localStorageKey.chatCanvasMode) === 'assistant' ? 'assistant' : 'conversation',
    selectedAssistantId: localStorage.getItem(localStorageKey.chatCanvasSelectedAssistantId) ?? undefined,
    selectedAssistantStateId: localStorage.getItem(localStorageKey.chatCanvasSelectedAssistantStateId) ?? undefined,
};

export const chatCanvasSlice = createSlice({
    name: 'chatCanvas',
    initialState,
    reducers: {
        setChatCanvasOpen: (state: ChatCanvasState, action: PayloadAction<boolean>) => {
            state.open = action.payload;
            persistState(state);
        },
        setChatCanvasMode: (state: ChatCanvasState, action: PayloadAction<ChatCanvasState['mode']>) => {
            state.mode = action.payload;
            persistState(state);
        },
        setChatCanvasAssistantId: (state: ChatCanvasState, action: PayloadAction<string | undefined>) => {
            state.selectedAssistantId = action.payload;
            persistState(state);
        },
        setChatCanvasAssistantStateId: (state: ChatCanvasState, action: PayloadAction<string | undefined>) => {
            state.selectedAssistantStateId = action.payload;
            persistState(state);
        },
        setChatCanvasState: (state: ChatCanvasState, action: PayloadAction<ChatCanvasState>) => {
            Object.assign(state, action.payload);
            persistState(state);
        },
    },
});

const persistState = (state: ChatCanvasState) => {
    AppStorage.getInstance().saveObject(localStorageKey.chatCanvasOpen, state.open);
    AppStorage.getInstance().saveObject(localStorageKey.chatCanvasMode, state.mode);
    AppStorage.getInstance().saveObject(localStorageKey.chatCanvasSelectedAssistantId, state.selectedAssistantId);
    AppStorage.getInstance().saveObject(
        localStorageKey.chatCanvasSelectedAssistantStateId,
        state.selectedAssistantStateId,
    );
};

export const {
    setChatCanvasOpen,
    setChatCanvasMode,
    setChatCanvasAssistantId,
    setChatCanvasAssistantStateId,
    setChatCanvasState,
} = chatCanvasSlice.actions;

export default chatCanvasSlice.reducer;


=== File: workbench-app/src/redux/features/localUser/LocalUserState.ts ===
export interface LocalUserState {
    id?: string;
    name?: string;
    email?: string;
    avatar: {
        name?: string;
        image?: {
            src: string;
        };
    };
}


=== File: workbench-app/src/redux/features/localUser/localUserSlice.ts ===
// Copyright (c) Microsoft. All rights reserved.

import { PayloadAction, createSlice } from '@reduxjs/toolkit';
import { AppStorage } from '../../../libs/AppStorage';
import { LocalUserState } from './LocalUserState';

const storageKeys = {
    id: 'local-user.id',
    name: 'local-user.name',
    email: 'local-user.email',
    avatarName: 'local-user.avatar.name',
    avatarImage: 'local-user.avatar.image',
};

const initialState: LocalUserState = {
    id: AppStorage.getInstance().loadObject<string>(storageKeys.id),
    name: AppStorage.getInstance().loadObject<string>(storageKeys.name),
    email: AppStorage.getInstance().loadObject<string>(storageKeys.email),
    avatar: {
        name: AppStorage.getInstance().loadObject<string>(storageKeys.avatarName),
        image: AppStorage.getInstance().loadObject<{
            src: string;
        }>(storageKeys.avatarImage),
    },
};

export const localUserSlice = createSlice({
    name: 'localUser',
    initialState,
    reducers: {
        setLocalUser: (state: LocalUserState, action: PayloadAction<LocalUserState>) => {
            Object.assign(state, action.payload);
            AppStorage.getInstance().saveObject(storageKeys.id, state.id);
            AppStorage.getInstance().saveObject(storageKeys.name, state.name);
            AppStorage.getInstance().saveObject(storageKeys.email, state.email);
            AppStorage.getInstance().saveObject(storageKeys.avatarName, state.avatar.name);
            AppStorage.getInstance().saveObject(storageKeys.avatarImage, state.avatar.image);
        },
    },
});

export const { setLocalUser } = localUserSlice.actions;

export default localUserSlice.reducer;


=== File: workbench-app/src/redux/features/settings/SettingsState.ts ===
// Copyright (c) Microsoft. All rights reserved.

export interface SettingsState {
    // persisted
    theme?: string;
    environmentId?: string;
}


=== File: workbench-app/src/redux/features/settings/settingsSlice.ts ===
// Copyright (c) Microsoft. All rights reserved.

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Constants } from '../../../Constants';
import { AppStorage } from '../../../libs/AppStorage';
import { SettingsState } from './SettingsState';

const storageKeys = {
    theme: 'settings.theme',
    environmentId: 'settings.environment-id',
};

const initialState: SettingsState = {
    theme: AppStorage.getInstance().loadObject<string>(storageKeys.theme) ?? Constants.app.defaultTheme,
    environmentId:
        AppStorage.getInstance().loadObject<string>(storageKeys.environmentId) ??
        Constants.service.defaultEnvironmentId,
};

export const settingsSlice = createSlice({
    name: 'settings',
    initialState,
    reducers: {
        setTheme: (state: SettingsState, action: PayloadAction<string>) => {
            AppStorage.getInstance().saveObject(storageKeys.theme, action.payload);
            state.theme = action.payload;
        },
        setEnvironmentId: (state: SettingsState, action: PayloadAction<string>) => {
            const needsReload = state.environmentId !== action.payload;
            if (action.payload === Constants.service.defaultEnvironmentId) {
                AppStorage.getInstance().saveObject(storageKeys.environmentId, undefined);
            } else {
                AppStorage.getInstance().saveObject(storageKeys.environmentId, action.payload);
            }
            state.environmentId = action.payload;
            if (needsReload) {
                window.location.reload();
            }
        },
    },
});

export const { setTheme, setEnvironmentId } = settingsSlice.actions;

export default settingsSlice.reducer;


=== File: workbench-app/src/routes/AcceptTerms.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button, Title2, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import debug from 'debug';
import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Constants } from '../Constants';
import { AppView } from '../components/App/AppView';
import { useAppDispatch, useAppSelector } from '../redux/app/hooks';
import { setCompletedFirstRun } from '../redux/features/app/appSlice';

const log = debug(Constants.debug.root).extend('accept-terms');

const useClasses = makeStyles({
    root: {
        height: '100%',
        backgroundColor: tokens.colorNeutralBackgroundAlpha,
        display: 'grid',
        gridTemplateRows: 'auto 1fr auto',
        gridTemplateColumns: '1fr',
        gridTemplateAreas: "'header' 'content' 'footer'",
        boxSizing: 'border-box',
        gap: tokens.spacingVerticalL,
        borderRadius: `${tokens.borderRadiusLarge} ${tokens.borderRadiusLarge} 0 0`,
        ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM, tokens.spacingVerticalXXXL),
    },
    header: {
        ...shorthands.gridArea('header'),
    },
    content: {
        backgroundColor: tokens.colorNeutralBackgroundAlpha2,
        overflow: 'auto',
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
        ...shorthands.gridArea('content'),
    },
    terms: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalS,
    },
    footer: {
        ...shorthands.gridArea('footer'),
        textAlign: 'right',
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalS,
    },
});

export const AcceptTerms: React.FC = () => {
    const classes = useClasses();
    const completedFirstRun = useAppSelector((state) => state.app.completedFirstRun);
    const dispatch = useAppDispatch();
    const navigate = useNavigate();
    const location = useLocation();

    React.useEffect(() => {
        if (completedFirstRun?.app) {
            const redirectTo = location.state?.redirectTo ?? '/';
            navigate(redirectTo);
        }
    }, [completedFirstRun, location.state?.redirectTo, navigate]);

    const handleAccept = () => {
        log('User accepted terms');
        dispatch(setCompletedFirstRun({ app: true }));
    };

    return (
        <AppView title="Terms" actions={{ items: [], replaceExisting: true, hideProfileSettings: true }}>
            <div className={classes.root}>
                <div className={classes.header}>
                    <Title2>MICROSOFT SEMANTIC WORKBENCH</Title2>
                </div>
                <div className={classes.content}>{terms}</div>
                <div className={classes.footer}>
                    <div>
                        <em>
                            You must accept the use terms before you can install or use the software. If you do not
                            accept the use terms, do not install or use the software.
                        </em>
                    </div>
                    <div>
                        <Button appearance="primary" onClick={handleAccept}>
                            I accept the terms
                        </Button>
                    </div>
                </div>
            </div>
        </AppView>
    );
};

const terms = (
    <div>
        <div>
            MIT License
            <br />
            <br />
        </div>
        <div>
            Copyright (c) Microsoft Corporation.
            <br />
            <br />
        </div>
        <div>
            Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
            documentation files (the &quot;Software&quot;), to deal in the Software without restriction, including
            without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
            copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the
            following conditions:
            <br />
            <br />
        </div>
        <div>
            The above copyright notice and this permission notice shall be included in all copies or substantial
            portions of the Software.
            <br />
            <br />
        </div>
        <div>
            THE SOFTWARE IS PROVIDED &quot;AS IS&quot;, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
            NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
            NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
            IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
            USE OR OTHER DEALINGS IN THE SOFTWARE
            <br />
            <br />
        </div>
    </div>
);


=== File: workbench-app/src/routes/AssistantEditor.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Card, Title3, Toolbar, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AppView } from '../components/App/AppView';
import { Loading } from '../components/App/Loading';
import { AssistantConfiguration } from '../components/Assistants/AssistantConfiguration';
import { AssistantDelete } from '../components/Assistants/AssistantDelete';
import { AssistantDuplicate } from '../components/Assistants/AssistantDuplicate';
import { AssistantExport } from '../components/Assistants/AssistantExport';
import { AssistantRename } from '../components/Assistants/AssistantRename';
import { AssistantServiceMetadata } from '../components/Assistants/AssistantServiceMetadata';
import { MyConversations } from '../components/Conversations/MyConversations';
import { useSiteUtility } from '../libs/useSiteUtility';
import { Conversation } from '../models/Conversation';
import { useAppSelector } from '../redux/app/hooks';
import {
    useAddConversationParticipantMutation,
    useCreateConversationMessageMutation,
    useGetAssistantConversationsQuery,
    useGetAssistantQuery,
} from '../services/workbench';

const useClasses = makeStyles({
    root: {
        display: 'grid',
        gridTemplateRows: '1fr auto',
        height: '100%',
        gap: tokens.spacingVerticalM,
    },
    title: {
        color: tokens.colorNeutralForegroundOnBrand,
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: tokens.spacingHorizontalM,
    },
    content: {
        overflowY: 'auto',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
        ...shorthands.padding(0, tokens.spacingHorizontalM),
    },
    toolbar: {
        backgroundColor: tokens.colorNeutralBackgroundAlpha,
        borderRadius: tokens.borderRadiusMedium,
    },
    card: {
        backgroundImage: `linear-gradient(to right, ${tokens.colorNeutralBackground1}, ${tokens.colorBrandBackground2})`,
    },
});

export const AssistantEditor: React.FC = () => {
    const { assistantId } = useParams();
    if (!assistantId) {
        throw new Error('Assistant ID is required');
    }

    const classes = useClasses();
    const {
        data: assistantConversations,
        error: assistantConversationsError,
        isLoading: isLoadingAssistantConversations,
    } = useGetAssistantConversationsQuery(assistantId);
    const { data: assistant, error: assistantError, isLoading: isLoadingAssistant } = useGetAssistantQuery(assistantId);
    const [addConversationParticipant] = useAddConversationParticipantMutation();
    const [createConversationMessage] = useCreateConversationMessageMutation();
    const localUserName = useAppSelector((state) => state.localUser.name);
    const siteUtility = useSiteUtility();
    const navigate = useNavigate();

    if (assistantConversationsError) {
        const errorMessage = JSON.stringify(assistantConversationsError);
        throw new Error(`Error loading assistant conversations: ${errorMessage}`);
    }

    if (assistantError) {
        const errorMessage = JSON.stringify(assistantError);
        throw new Error(`Error loading assistant: ${errorMessage}`);
    }

    React.useEffect(() => {
        if (isLoadingAssistant) return;
        if (!assistant) {
            throw new Error(`Assistant with ID ${assistantId} not found`);
        }
        siteUtility.setDocumentTitle(`Edit ${assistant.name}`);
    }, [assistantId, assistant, isLoadingAssistant, siteUtility]);

    const handleDelete = React.useCallback(() => {
        // navigate to site root
        siteUtility.forceNavigateTo('/');
    }, [siteUtility]);

    const handleDuplicate = (assistantId: string) => {
        siteUtility.forceNavigateTo(`/assistant/${assistantId}/edit`);
    };

    const handleConversationCreate = async (conversation: Conversation) => {
        // send event to notify the conversation that the user has joined
        await createConversationMessage({
            conversationId: conversation.id,
            content: `${localUserName ?? 'Unknown user'} created the conversation`,
            messageType: 'notice',
        });

        // send notice message first, to announce before assistant reacts to create event
        await createConversationMessage({
            conversationId: conversation.id,
            content: `${assistant?.name} added to conversation`,
            messageType: 'notice',
        });

        // add assistant to conversation
        await addConversationParticipant({ conversationId: conversation.id, participantId: assistantId });

        // navigate to conversation
        navigate(`/conversation/${conversation.id}`);
    };

    if (isLoadingAssistant || isLoadingAssistantConversations || !assistant) {
        return (
            <AppView title="Edit Assistant">
                <Loading />
            </AppView>
        );
    }

    return (
        <AppView
            title={
                <div className={classes.title}>
                    <AssistantRename iconOnly assistant={assistant} />
                    <Title3>{assistant.name}</Title3>
                </div>
            }
        >
            <div className={classes.root}>
                <div className={classes.content}>
                    <Card className={classes.card}>
                        <AssistantServiceMetadata assistantServiceId={assistant.assistantServiceId} />
                    </Card>
                    <MyConversations
                        title="Conversations"
                        conversations={assistantConversations}
                        participantId={assistantId}
                        hideInstruction
                        onCreate={handleConversationCreate}
                    />
                    <Card className={classes.card}>
                        <AssistantConfiguration assistant={assistant} />
                    </Card>
                </div>
                <Toolbar className={classes.toolbar}>
                    <AssistantDelete asToolbarButton assistant={assistant} onDelete={handleDelete} />
                    <AssistantExport asToolbarButton assistantId={assistant.id} />
                    <AssistantDuplicate asToolbarButton assistant={assistant} onDuplicate={handleDuplicate} />
                </Toolbar>
            </div>
        </AppView>
    );
};


=== File: workbench-app/src/routes/AssistantServiceRegistrationEditor.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button, Card, Checkbox, Field, Input, Textarea, makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { useParams } from 'react-router-dom';
import { AppView } from '../components/App/AppView';
import { CopyButton } from '../components/App/CopyButton';
import { Loading } from '../components/App/Loading';
import { AssistantServiceRegistrationApiKeyReset } from '../components/AssistantServiceRegistrations/AssistantServiceRegistrationApiKeyReset';
import {
    useGetAssistantServiceRegistrationQuery,
    useUpdateAssistantServiceRegistrationMutation,
} from '../services/workbench';

const useClasses = makeStyles({
    card: {
        backgroundImage: `linear-gradient(to right, ${tokens.colorNeutralBackground1}, ${tokens.colorBrandBackground2})`,
    },
    input: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'stretch',
        width: '100%',
        maxWidth: '300px',
    },
    row: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: tokens.spacingHorizontalM,
    },
});

export const AssistantServiceRegistrationEditor: React.FC = () => {
    const { assistantServiceRegistrationId } = useParams();
    if (!assistantServiceRegistrationId) {
        throw new Error('Assistant service registration ID is required');
    }
    const classes = useClasses();

    const {
        data: assistantServiceRegistration,
        error: assistantServiceRegistrationError,
        isLoading: isAssistantServiceRegistrationLoading,
    } = useGetAssistantServiceRegistrationQuery(assistantServiceRegistrationId);
    const [updateAssistantServiceRegistration] = useUpdateAssistantServiceRegistrationMutation();

    const [name, setName] = React.useState('');
    const [includeInListing, setIncludeInListing] = React.useState(false);
    const [description, setDescription] = React.useState('');
    const [submitted, setSubmitted] = React.useState(false);

    if (assistantServiceRegistrationError) {
        const errorMessage = JSON.stringify(assistantServiceRegistrationError);
        throw new Error(`Error loading assistant service registration: ${errorMessage}`);
    }

    React.useEffect(() => {
        if (assistantServiceRegistration) {
            setName(assistantServiceRegistration.name);
            setIncludeInListing(assistantServiceRegistration.includeInListing);
            setDescription(assistantServiceRegistration.description);
        }
    }, [assistantServiceRegistration]);

    const handleSave = React.useCallback(async () => {
        setSubmitted(true);
        try {
            await updateAssistantServiceRegistration({
                id: assistantServiceRegistrationId,
                assistantServiceRegistration: {
                    name,
                    description,
                    includeInListing,
                },
            }).unwrap();
        } finally {
            setSubmitted(false);
        }
    }, [assistantServiceRegistrationId, name, includeInListing, description, updateAssistantServiceRegistration]);

    if (isAssistantServiceRegistrationLoading || !assistantServiceRegistration) {
        return (
            <AppView title="Assistant Service Registration Editor">
                <Loading />
            </AppView>
        );
    }

    const disabled =
        submitted ||
        !name ||
        !description ||
        (name === assistantServiceRegistration.name &&
            description === assistantServiceRegistration.description &&
            includeInListing === assistantServiceRegistration.includeInListing);

    return (
        <AppView title="Assistant Service Registration Editor">
            <Card className={classes.card}>
                <Field label="Assistant Service ID (read-only)">
                    <Input className={classes.input} value={assistantServiceRegistration.assistantServiceId} readOnly />
                </Field>
                <Field label="Name">
                    <Input className={classes.input} value={name} onChange={(_event, data) => setName(data.value)} />
                </Field>
                {assistantServiceRegistration.apiKeyName && (
                    <>
                        <Field label="API Key (read-only)">
                            <div className={classes.row}>
                                <Input className={classes.input} value={assistantServiceRegistration.apiKey} readOnly />
                                <AssistantServiceRegistrationApiKeyReset
                                    assistantServiceRegistration={assistantServiceRegistration}
                                />
                            </div>
                        </Field>
                        <Field label="API Key secret name (read-only)">
                            <div className={classes.row}>
                                <Input
                                    className={classes.input}
                                    value={assistantServiceRegistration.apiKeyName}
                                    readOnly
                                />
                                <CopyButton data={assistantServiceRegistration.apiKeyName} />
                            </div>
                        </Field>
                    </>
                )}
                <Checkbox
                    label="Include this assistant service in everyone's create assistant list"
                    checked={includeInListing}
                    onChange={(_event, data) => setIncludeInListing(data.checked === true)}
                />
                <Field label="Description">
                    <Textarea rows={4} value={description} onChange={(_event, data) => setDescription(data.value)} />
                </Field>
                <div>
                    <Button appearance="primary" disabled={disabled} onClick={handleSave}>
                        Save
                    </Button>
                </div>
            </Card>
        </AppView>
    );
};


=== File: workbench-app/src/routes/Dashboard.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AppView } from '../components/App/AppView';
import { ExperimentalNotice } from '../components/App/ExperimentalNotice';
import { Loading } from '../components/App/Loading';
import { MyAssistants } from '../components/Assistants/MyAssistants';
import { MyConversations } from '../components/Conversations/MyConversations';
import { useSiteUtility } from '../libs/useSiteUtility';
import { Conversation } from '../models/Conversation';
import { useAppSelector } from '../redux/app/hooks';
import { useGetAssistantsQuery, useGetConversationsQuery } from '../services/workbench';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
    messageBars: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalS,
    },
    body: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalXXXL,
    },
});

export const Dashboard: React.FC = () => {
    const classes = useClasses();
    const { data: assistants, error: assistantsError, isLoading: isLoadingAssistants } = useGetAssistantsQuery();
    const {
        data: conversations,
        error: conversationsError,
        isLoading: isLoadingConversations,
    } = useGetConversationsQuery();

    const localUserStateId = useAppSelector((state) => state.localUser.id);
    const navigate = useNavigate();

    const siteUtility = useSiteUtility();
    siteUtility.setDocumentTitle('Dashboard');

    if (assistantsError) {
        const errorMessage = JSON.stringify(assistantsError);
        throw new Error(`Error loading assistants: ${errorMessage}`);
    }

    if (conversationsError) {
        const errorMessage = JSON.stringify(conversationsError);
        throw new Error(`Error loading conversations: ${errorMessage}`);
    }

    const handleConversationCreate = React.useCallback(
        (conversation: Conversation) => {
            navigate(`/conversation/${conversation.id}`);
        },
        [navigate],
    );

    if (isLoadingAssistants || isLoadingConversations) {
        return (
            <AppView title="Dashboard">
                <Loading />
            </AppView>
        );
    }

    const myConversations = conversations?.filter((conversation) => conversation.ownerId === localUserStateId) || [];
    const conversationsSharedWithMe =
        conversations?.filter((conversation) => conversation.ownerId !== localUserStateId) || [];

    return (
        <AppView title="Dashboard">
            <div className={classes.root}>
                <div className={classes.messageBars}>
                    <ExperimentalNotice />
                </div>
                <div className={classes.body}>
                    <MyAssistants assistants={assistants} />
                    <MyConversations
                        conversations={myConversations}
                        participantId="me"
                        onCreate={handleConversationCreate}
                    />
                    {conversationsSharedWithMe.length > 0 && (
                        <MyConversations
                            title="Conversations Shared with Me"
                            conversations={conversationsSharedWithMe}
                            participantId="me"
                            onCreate={handleConversationCreate}
                        />
                    )}
                </div>
            </div>
        </AppView>
    );
};


=== File: workbench-app/src/routes/ErrorPage.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { MessageBar, MessageBarBody } from '@fluentui/react-components';
import React from 'react';
import { isRouteErrorResponse, useRouteError } from 'react-router-dom';
import { AppView } from '../components/App/AppView';
import { useSiteUtility } from '../libs/useSiteUtility';

export const ErrorPage: React.FC = () => {
    const error = useRouteError();
    const siteUtility = useSiteUtility();

    siteUtility.setDocumentTitle('Error');

    let errorMessage: string;

    if (isRouteErrorResponse(error)) {
        // error is type `ErrorResponse`
        errorMessage = error.data || error.statusText;
    } else if (error instanceof Error) {
        // error is type `Error`
        errorMessage = error.message;
    } else if (typeof error === 'string') {
        // error is type `string`
        errorMessage = error;
    } else {
        // error is type `unknown`
        errorMessage = 'Unknown error';
    }

    return (
        <AppView title="Error">
            <MessageBar intent="error" layout="multiline">
                <MessageBarBody>{errorMessage}</MessageBarBody>
            </MessageBar>
        </AppView>
    );
};


=== File: workbench-app/src/routes/FrontDoor.tsx ===
import {
    Button,
    Drawer,
    DrawerBody,
    Link,
    makeStyles,
    mergeClasses,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import { ChatAddRegular, PanelLeftContractRegular, PanelLeftExpandRegular } from '@fluentui/react-icons';
import React from 'react';
import { useDispatch } from 'react-redux';
import { useNavigate, useParams } from 'react-router-dom';
import { Loading } from '../components/App/Loading';
import { SiteMenuButton } from '../components/FrontDoor/Controls/SiteMenuButton';
import { GlobalContent } from '../components/FrontDoor/GlobalContent';
import { MainContent } from '../components/FrontDoor/MainContent';
import { Constants } from '../Constants';
import { EventSubscriptionManager } from '../libs/EventSubscriptionManager';
import { useWorkbenchConversationEventSource, useWorkbenchUserEventSource } from '../libs/useWorkbenchEventSource';
import { useAppSelector } from '../redux/app/hooks';
import { setActiveConversationId, setGlobalContentOpen } from '../redux/features/app/appSlice';

const useClasses = makeStyles({
    documentBody: {
        backgroundColor: `rgba(0, 0, 0, 0.1)`,
    },
    root: {
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
    },
    body: {
        flex: '1 1 auto',
        display: 'flex',
        flexDirection: 'row',
        height: '100%',
    },
    sideRailLeft: {
        backgroundColor: tokens.colorNeutralBackground2,
        ...shorthands.borderRight(tokens.strokeWidthThick, 'solid', tokens.colorNeutralStroke3),
        boxSizing: 'border-box',
        minWidth: Constants.app.conversationListMinWidth,
    },
    sideRailLeftBody: {
        // override Fluent UI DrawerBody padding
        padding: 0,
        '&:first-child': {
            paddingTop: 0,
        },
        '&:last-child': {
            paddingBottom: 0,
        },
    },
    transitionFade: {
        opacity: 0,
        transitionProperty: 'opacity',
        transitionDuration: tokens.durationFast,
        transitionDelay: '0',
        transitionTimingFunction: tokens.curveEasyEase,

        '&.in': {
            opacity: 1,
            transitionProperty: 'opacity',
            transitionDuration: tokens.durationNormal,
            transitionDelay: tokens.durationNormal,
            transitionTimingFunction: tokens.curveEasyEase,
        },
    },
    mainContent: {
        flex: '1 1 auto',
        display: 'flex',
        flexDirection: 'column',
    },
    controls: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: tokens.spacingHorizontalS,
    },
});

export const workbenchUserEvents = new EventSubscriptionManager();
export const workbenchConversationEvents = new EventSubscriptionManager();

export const FrontDoor: React.FC = () => {
    const classes = useClasses();
    const { conversationId } = useParams();
    const activeConversationId = useAppSelector((state) => state.app.activeConversationId);
    const globalContentOpen = useAppSelector((state) => state.app.globalContentOpen);
    const dispatch = useDispatch();
    const [isInitialized, setIsInitialized] = React.useState(false);
    const navigate = useNavigate();

    // set up the workbench event sources and connect to the conversation and user event streams
    // any child components can subscribe to these events using the subscription managers
    // these should only reset when the conversation ID changes
    useWorkbenchUserEventSource(workbenchUserEvents);
    useWorkbenchConversationEventSource(workbenchConversationEvents, activeConversationId);

    React.useEffect(() => {
        document.body.className = classes.documentBody;
        return () => {
            document.body.className = '';
        };
    }, [classes.documentBody]);

    React.useEffect(() => {
        if (conversationId !== activeConversationId) {
            dispatch(setActiveConversationId(conversationId));
        }
        setIsInitialized(true);
    }, [conversationId, activeConversationId, dispatch]);

    const sideRailLeftButton = React.useMemo(
        () => (
            <Button
                icon={globalContentOpen ? <PanelLeftContractRegular /> : <PanelLeftExpandRegular />}
                onClick={(event) => {
                    event.stopPropagation();
                    dispatch(setGlobalContentOpen(!globalContentOpen));
                }}
            />
        ),
        [dispatch, globalContentOpen],
    );

    const handleNewConversation = React.useCallback(() => {
        navigate('/');
    }, [navigate]);

    const newConversationButton = React.useMemo(
        () => (
            <Link href="/" onClick={(event) => event.preventDefault()}>
                <Button title="New Conversation" icon={<ChatAddRegular />} onClick={handleNewConversation} />
            </Link>
        ),
        [handleNewConversation],
    );

    const globalContent = React.useMemo(
        () => <GlobalContent headerBefore={sideRailLeftButton} headerAfter={newConversationButton} />,
        [sideRailLeftButton, newConversationButton],
    );

    return (
        <div className={classes.root}>
            <div className={classes.body}>
                <Drawer
                    className={classes.sideRailLeft}
                    open={globalContentOpen}
                    modalType="non-modal"
                    type="inline"
                    size="small"
                >
                    <DrawerBody className={classes.sideRailLeftBody}>{globalContent}</DrawerBody>
                </Drawer>
                <div className={classes.mainContent}>
                    {!isInitialized ? (
                        <Loading />
                    ) : (
                        <MainContent
                            headerBefore={
                                <div
                                    className={mergeClasses(
                                        classes.controls,
                                        classes.transitionFade,
                                        !globalContentOpen ? 'in' : undefined,
                                    )}
                                >
                                    {sideRailLeftButton}
                                    {newConversationButton}
                                </div>
                            }
                            headerAfter={<SiteMenuButton />}
                        />
                    )}
                </div>
            </div>
        </div>
    );
};


=== File: workbench-app/src/routes/Login.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { useMsal } from '@azure/msal-react';
import { Button, Label, MessageBar } from '@fluentui/react-components';
import debug from 'debug';
import React from 'react';
import { Constants } from '../Constants';
import { AppView } from '../components/App/AppView';
import { AuthHelper } from '../libs/AuthHelper';
import { useSiteUtility } from '../libs/useSiteUtility';

const log = debug(Constants.debug.root).extend('login');

export const Login: React.FC = () => {
    const { instance } = useMsal();
    const siteUtility = useSiteUtility();
    const [errorMessage, setErrorMessage] = React.useState<string>();

    siteUtility.setDocumentTitle('Login');

    const handleSignIn = () => {
        void (async () => {
            try {
                await AuthHelper.loginAsync(instance);
            } catch (error) {
                log(error);
                setErrorMessage((error as Error).message);
            }
        })();
    };

    return (
        <AppView title="Login" actions={{ items: [], replaceExisting: true, hideProfileSettings: true }}>
            <div>
                <Button appearance="primary" onClick={handleSignIn}>
                    Sign In
                </Button>
            </div>
            <Label>
                Note: Semantic Workbench can be deployed as a multi-user application, requiring user sign-in even when
                running locally as a single-user instance. By default, it uses Microsoft accounts and a sample app
                registration for quick setup. You can modify the configuration in the code by editing `Constants.ts` and
                `AuthSettings` in `semantic_workbench_settings.config.py`.
            </Label>
            {errorMessage && (
                <MessageBar intent="error" layout="multiline">
                    {errorMessage}
                </MessageBar>
            )}
        </AppView>
    );
};


=== File: workbench-app/src/routes/Settings.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Card, Dropdown, Field, Label, Option, makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { Constants } from '../Constants';
import { AppView } from '../components/App/AppView';
import { MyAssistantServiceRegistrations } from '../components/App/MyAssistantServiceRegistrations';
import { useEnvironment } from '../libs/useEnvironment';
import { useSiteUtility } from '../libs/useSiteUtility';
import { useAppDispatch } from '../redux/app/hooks';
import { setEnvironmentId } from '../redux/features/settings/settingsSlice';
import { useGetAssistantServiceRegistrationsQuery } from '../services/workbench';

const useClasses = makeStyles({
    card: {
        backgroundImage: `linear-gradient(to right, ${tokens.colorNeutralBackground1}, ${tokens.colorBrandBackground2})`,
    },
    input: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'stretch',
        width: '100%',
        maxWidth: '300px',
    },
    row: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
    },
});

export const Settings: React.FC = () => {
    const classes = useClasses();
    const environment = useEnvironment();
    // const { devMode } = useAppSelector((state) => state.app);
    const { data: assistantServiceRegistrations, error: assistantServiceRegistrationsError } =
        useGetAssistantServiceRegistrationsQuery({ userIds: ['me'] });

    const dispatch = useAppDispatch();
    const siteUtility = useSiteUtility();

    siteUtility.setDocumentTitle('Settings');

    // Don't throw on assistant service registration error,
    // instead show the error message in the UI and allow the
    // rest of the settings page to render.

    const handleSettingChange = React.useCallback(
        (setting: string, value: string) => {
            switch (setting) {
                case 'environmentId':
                    dispatch(setEnvironmentId(value));
                    break;
                default:
                    throw new Error(`Unknown setting: ${setting}`);
            }
        },
        [dispatch],
    );

    // const handleDevModeChange = () => {
    //     dispatch(toggleDevMode());
    // };

    return (
        <AppView title="Settings">
            <Card className={classes.card}>
                <Field label="Service Environment">
                    <Dropdown
                        className={classes.input}
                        value={environment.name}
                        selectedOptions={[environment.id]}
                        onOptionSelect={(_event, data) =>
                            handleSettingChange('environmentId', data.optionValue as string)
                        }
                    >
                        {Constants.service.environments.map((environmentOption) => (
                            <Option
                                key={environmentOption.id}
                                text={environmentOption.name}
                                value={environmentOption.id}
                            >
                                <Label>{environmentOption.name}</Label>
                            </Option>
                        ))}
                    </Dropdown>
                </Field>

                {/* <Field label="Enable Developer Mode">
                    <div className={classes.row}>
                        <Switch checked={devMode} onChange={handleDevModeChange} />
                        <Tooltip
                            content={
                                'These settings are for early, in-development features that are enabled throughout the app.' +
                                ' These are features that are not yet ready for general availability and may not be fully' +
                                ' functional. Use at your own risk.'
                            }
                            relationship="description"
                        >
                            <QuestionCircle16Regular />
                        </Tooltip>
                    </div>
                </Field> */}
            </Card>
            {!assistantServiceRegistrationsError && (
                <Card className={classes.card}>
                    <Field label="Assistant Service Registrations">
                        <MyAssistantServiceRegistrations
                            assistantServiceRegistrations={assistantServiceRegistrations}
                        />
                    </Field>
                </Card>
            )}
        </AppView>
    );
};


=== File: workbench-app/src/routes/ShareRedeem.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogOpenChangeData, DialogOpenChangeEvent, DialogTrigger } from '@fluentui/react-components';
import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AppView } from '../components/App/AppView';
import { DialogControl } from '../components/App/DialogControl';
import { Loading } from '../components/App/Loading';
import { ConversationShareType, useConversationUtility } from '../libs/useConversationUtility';
import { useSiteUtility } from '../libs/useSiteUtility';
import { useWorkbenchService } from '../libs/useWorkbenchService';
import { Conversation } from '../models/Conversation';
import { useAppSelector } from '../redux/app/hooks';
import {
    useCreateConversationMessageMutation,
    useGetConversationsQuery,
    useRemoveConversationParticipantMutation,
} from '../services/workbench';
import { useGetShareQuery, useRedeemShareMutation } from '../services/workbench/share';

export const ShareRedeem: React.FC = () => {
    const { conversationShareId } = useParams();
    const navigate = useNavigate();
    const workbenchService = useWorkbenchService();
    const [redeemShare] = useRedeemShareMutation();
    const [createConversationMessage] = useCreateConversationMessageMutation();
    const [removeConversationParticipant] = useRemoveConversationParticipantMutation();
    const [submitted, setSubmitted] = React.useState(false);
    const [joinAttempted, setJoinAttempted] = React.useState(false);
    const conversationUtility = useConversationUtility();
    const localUserName = useAppSelector((state) => state.localUser.name);

    if (!conversationShareId) {
        throw new Error('Conversation Share ID is required');
    }

    const siteUtility = useSiteUtility();
    const {
        data: conversationShare,
        error: conversationShareError,
        isLoading: conversationShareIsLoading,
    } = useGetShareQuery(conversationShareId);
    const {
        data: conversations,
        error: conversationsError,
        isLoading: conversationsIsLoading,
    } = useGetConversationsQuery();
    const [existingDuplicateConversations, setExistingDuplicateConversations] = React.useState<Array<Conversation>>([]);

    const title = 'Open a shared conversation';
    siteUtility.setDocumentTitle(title);

    const handleClickJoin = React.useCallback(
        async (messageId?: string) => {
            if (!conversationShare) {
                return;
            }
            setSubmitted(true);
            try {
                await redeemShare(conversationShare.id);
                const hash = messageId ? `#${messageId}` : '';

                // send event to notify the conversation that the user has joined
                if (conversationShare.conversationPermission === 'read_write') {
                    await createConversationMessage({
                        conversationId: conversationShare.conversationId,
                        content: `${localUserName} joined the conversation`,
                        messageType: 'notice',
                    });
                }

                conversationUtility.navigateToConversation(conversationShare.conversationId, hash);
            } finally {
                setSubmitted(false);
            }
        },
        [conversationShare, redeemShare, conversationUtility, createConversationMessage, localUserName],
    );

    const handleClickDuplicate = React.useCallback(async () => {
        if (!conversationShare) {
            return;
        }
        setSubmitted(true);
        try {
            // join the conversation
            const redemption = await redeemShare(conversationShare.id).unwrap();

            // duplicate it
            const duplicatedConversationIds = await workbenchService.exportThenImportConversationAsync([
                redemption.conversationId,
            ]);

            if (redemption.isNewParticipant) {
                // leave the conversation
                await removeConversationParticipant({
                    conversationId: redemption.conversationId,
                    participantId: 'me',
                });
            }

            // navigate to the newly duplicated conversation
            const conversationId = duplicatedConversationIds[0];
            conversationUtility.navigateToConversation(conversationId);
        } finally {
            setSubmitted(false);
        }
    }, [conversationShare, redeemShare, workbenchService, conversationUtility, removeConversationParticipant]);

    const handleDismiss = React.useCallback(
        (_: DialogOpenChangeEvent, data: DialogOpenChangeData) => {
            if (data.open) {
                return;
            }
            navigate(`/`);
        },
        [navigate],
    );

    const readyToCheckForMessageLink = conversationShare && !joinAttempted && !conversationsIsLoading;

    React.useEffect(() => {
        if (!readyToCheckForMessageLink) {
            return;
        }

        const { linkToMessageId } = conversationUtility.getShareType(conversationShare);
        if (!linkToMessageId) {
            return;
        }

        setJoinAttempted(true);
        handleClickJoin(linkToMessageId);
    }, [conversationShare, conversationUtility, handleClickJoin, readyToCheckForMessageLink]);

    const renderAppView = React.useCallback(
        (options: {
            dialogTitle?: string;
            dialogContent?: React.ReactElement;
            dialogActions?: React.ReactElement[];
            dismissLabel?: string;
        }) => {
            const { dialogTitle, dialogContent, dialogActions, dismissLabel } = options;
            return (
                <AppView title={title}>
                    <DialogControl
                        open={true}
                        onOpenChange={handleDismiss}
                        title={dialogTitle}
                        content={dialogContent}
                        closeLabel={dismissLabel ?? 'Close'}
                        additionalActions={dialogActions}
                        dismissButtonDisabled={submitted}
                    />
                </AppView>
            );
        },
        [handleDismiss, submitted],
    );

    const renderTrigger = React.useCallback(
        (options: {
            label: string;
            appearance?: 'secondary' | 'primary' | 'outline' | 'subtle' | 'transparent';
            onClick: () => void;
        }) => {
            return (
                <DialogTrigger disableButtonEnhancement action="open" key={options.label}>
                    <Button
                        style={{ width: 'max-content' }}
                        appearance={options?.appearance ?? 'primary'}
                        onClick={options.onClick}
                        disabled={submitted}
                    >
                        {options.label}
                    </Button>
                </DialogTrigger>
            );
        },
        [submitted],
    );

    React.useEffect(() => {
        if (!conversations || !conversationShare) {
            return;
        }
        const existingDuplicates = conversations.filter(
            (conversation) => conversation.importedFromConversationId === conversationShare.conversationId,
        );
        if (existingDuplicates.length > 0) {
            setExistingDuplicateConversations(existingDuplicates);
        }
    }, [conversations, conversationShare]);

    if (conversationShareIsLoading || conversationsIsLoading) {
        return renderAppView({
            dialogContent: <Loading />,
        });
    }

    // Handle error states - either an explicit error or a missing conversation share after loading.
    if (conversationShareError || !conversationShare) {
        return renderAppView({
            dialogTitle: 'Share does not exist or has been deleted',
        });
    }

    if (conversationsError || !conversations) {
        return renderAppView({
            dialogTitle: 'Error loading conversations',
        });
    }

    // Determine the share type and render the appropriate view.
    const { shareType, linkToMessageId } = conversationUtility.getShareType(conversationShare);
    const { conversationTitle, createdByUser } = conversationShare;

    if (shareType !== ConversationShareType.NotRedeemable && linkToMessageId) {
        return renderAppView({
            dialogContent: <Loading />,
        });
    }

    // Many of the share types have common content, so we'll define them here.
    const shareDetails = (
        <ul>
            <li>
                Conversation title: <strong>{conversationTitle}</strong>
            </li>
            <li>
                Shared by: <strong>{createdByUser.name}</strong>
            </li>
        </ul>
    );
    const inviteTitle = 'A conversation has been shared with you';
    const copyNote = 'You may create a copy of the conversation to make changes without affecting the original.';
    const existingCopyNote = existingDuplicateConversations.length ? (
        <>
            You have copied this conversation before. Click on a link below to open an existing copy:
            <ul>
                {existingDuplicateConversations.map((conversation) => (
                    <li key={conversation.id}>
                        <a href={`${window.location.origin}/${conversation.id}`}>{conversation.title}</a>
                    </li>
                ))}
            </ul>
        </>
    ) : (
        <> </>
    );

    switch (shareType) {
        // Handle the case where the share is no longer redeemable.
        case ConversationShareType.NotRedeemable:
            return renderAppView({
                dialogTitle: 'Share is no longer redeemable',
                dialogContent: (
                    <div>
                        The share has already been redeemed or has expired.
                        {shareDetails}
                        If you believe this is an error, please contact the person who shared the conversation with you.
                    </div>
                ),
            });

        // Handle the case where the user has been invited to participate in the conversation.
        case ConversationShareType.InvitedToParticipate:
            return renderAppView({
                dialogTitle: inviteTitle,
                dialogContent: (
                    <>
                        <div>
                            You have been <em>invited to participate</em> in a conversation: By joining, you will be
                            able to view and participate in the conversation.
                            {shareDetails}
                        </div>
                        <div>{existingCopyNote}</div>
                        <div>{copyNote}</div>
                    </>
                ),
                dialogActions: [
                    renderTrigger({
                        label: 'Create copy',
                        onClick: handleClickDuplicate,
                        appearance: 'secondary',
                    }),
                    renderTrigger({
                        label: 'Join',
                        onClick: handleClickJoin,
                    }),
                ],
            });

        // Handle the case where the user has been invited to observe the conversation.
        case ConversationShareType.InvitedToObserve:
            return renderAppView({
                dialogTitle: inviteTitle,
                dialogContent: (
                    <>
                        <div>
                            You have been <em>invited to observe</em> a conversation: By observing, you will be able to
                            view the conversation without participating.
                            {shareDetails}
                        </div>
                        <div>{existingCopyNote}</div>
                        <div>{copyNote}</div>
                    </>
                ),
                dialogActions: [
                    renderTrigger({
                        label: 'Create copy',
                        onClick: handleClickDuplicate,
                        appearance: 'secondary',
                    }),
                    renderTrigger({
                        label: 'Observe',
                        onClick: handleClickJoin,
                    }),
                ],
            });

        // Handle the case where the user has been invited to duplicate the conversation.
        case ConversationShareType.InvitedToDuplicate:
            return renderAppView({
                dialogTitle: inviteTitle,
                dialogContent: (
                    <>
                        <div>
                            You have been <em>invited to copy</em> a conversation:
                            {shareDetails}
                        </div>
                        <div>{existingCopyNote}</div>
                        <div>{copyNote}</div>
                    </>
                ),
                dialogActions: [
                    renderTrigger({
                        label: 'Create copy',
                        onClick: handleClickDuplicate,
                    }),
                ],
            });
    }
};


=== File: workbench-app/src/routes/Shares.tsx ===
// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { AppView } from '../components/App/AppView';
import { Loading } from '../components/App/Loading';
import { MyShares } from '../components/Conversations/MyShares';
import { useSiteUtility } from '../libs/useSiteUtility';
import { useGetSharesQuery } from '../services/workbench/share';

export const Shares: React.FC = () => {
    const {
        data: conversationShares,
        error: conversationSharesError,
        isLoading: isLoadingConversationShares,
    } = useGetSharesQuery({
        conversationId: undefined,
        includeUnredeemable: false,
    });

    const siteUtility = useSiteUtility();
    siteUtility.setDocumentTitle('Shares');

    if (conversationSharesError) {
        throw new Error(`Error loading conversation shares: ${JSON.stringify(conversationSharesError)}`);
    }

    if (isLoadingConversationShares) {
        return (
            <AppView title="Shares">
                <Loading />
            </AppView>
        );
    }

    return (
        <AppView title="Shares">
            <MyShares hideInstruction={true} shares={conversationShares ?? []} />
        </AppView>
    );
};


=== File: workbench-app/src/services/workbench/assistant.ts ===
import { Assistant } from '../../models/Assistant';
import { workbenchApi } from './workbench';

export const assistantApi = workbenchApi.injectEndpoints({
    endpoints: (builder) => ({
        getAssistants: builder.query<Assistant[], void>({
            query: () => '/assistants',
            providesTags: ['Assistant'],
            transformResponse: (response: any) => response.assistants.map(transformResponseToAssistant),
        }),
        getAssistantsInConversation: builder.query<Assistant[], string>({
            query: (conversationId: string) => `/assistants?conversation_id=${conversationId}`,
            providesTags: ['Assistant', 'Conversation'],
            transformResponse: (response: any) => response.assistants.map(transformResponseToAssistant),
        }),
        getAssistant: builder.query<Assistant, string>({
            query: (id) => `/assistants/${id}`,
            providesTags: ['Assistant'],
            transformResponse: (response: any) => transformResponseToAssistant(response),
        }),
        createAssistant: builder.mutation<
            Assistant,
            Partial<Assistant> & Pick<Assistant, 'name' | 'assistantServiceId' | 'templateId'>
        >({
            query: (body) => ({
                url: '/assistants',
                method: 'POST',
                body: transformAssistantForRequest(body),
            }),
            invalidatesTags: ['Assistant'],
            transformResponse: (response: any) => transformResponseToAssistant(response),
        }),
        updateAssistant: builder.mutation<Assistant, Assistant>({
            query: (body) => ({
                url: `/assistants/${body.id}`,
                method: 'PATCH',
                body: transformAssistantForRequest(body),
            }),
            invalidatesTags: ['Assistant'],
            transformResponse: (response: any) => transformResponseToAssistant(response),
        }),
        deleteAssistant: builder.mutation<{ id: string }, string>({
            query: (id) => ({
                url: `/assistants/${id}`,
                method: 'DELETE',
            }),
            // deleting an assistant can remove it from 0 or more conversations
            invalidatesTags: ['Assistant', 'Conversation'],
        }),
    }),
    overrideExisting: false,
});

export const {
    useGetAssistantsQuery,
    useGetAssistantsInConversationQuery,
    useGetAssistantQuery,
    useCreateAssistantMutation,
    useUpdateAssistantMutation,
    useDeleteAssistantMutation,
} = assistantApi;

const transformAssistantForRequest = (assistant: Partial<Assistant>) => ({
    id: assistant.id,
    name: assistant.name,
    assistant_service_id: assistant.assistantServiceId,
    template_id: assistant.templateId,
    metadata: assistant.metadata,
});

export const transformResponseToAssistant = (response: any): Assistant => {
    try {
        return {
            id: response.id,
            name: response.name,
            image: response.image,
            assistantServiceId: response.assistant_service_id,
            assistantServiceOnline: response.assistant_service_online,
            createdDatetime: response.created_datetime,
            templateId: response.template_id,
            conversations: {
                ...Object.fromEntries(
                    Object.entries(response.conversations ?? {}).map(
                        ([conversationId, conversation]: [string, any]) => [
                            conversationId,
                            {
                                id: conversation.id,
                            },
                        ],
                    ),
                ),
            },
            metadata: response.metadata,
        };
    } catch (error) {
        throw new Error(`Failed to transform assistant response: ${error}`);
    }
};


=== File: workbench-app/src/services/workbench/assistantService.ts ===
import { AssistantServiceInfo } from '../../models/AssistantServiceInfo';
import {
    AssistantServiceRegistration,
    NewAssistantServiceRegistration,
} from '../../models/AssistantServiceRegistration';
import { workbenchApi } from './workbench';

export const assistantServiceApi = workbenchApi.injectEndpoints({
    endpoints: (builder) => ({
        getAssistantServiceInfo: builder.query<AssistantServiceInfo, string>({
            query: (assistantServiceId: string) => `/assistant-services/${encodeURIComponent(assistantServiceId)}`,
            providesTags: ['AssistantServiceInfo'],
            transformResponse: (response: any) => transformResponseToAssistantServiceInfo(response),
        }),
        getAssistantServiceInfos: builder.query<AssistantServiceInfo[], { userIds?: string[] }>({
            query: () => `/assistant-services`,
            providesTags: ['AssistantServiceInfo'],
            transformResponse: (response: any) => transformResponseToAssistantServiceInfos(response),
        }),
        getAssistantServiceRegistration: builder.query<AssistantServiceRegistration, string>({
            query: (id) => `/assistant-service-registrations/${encodeURIComponent(id)}`,
            providesTags: ['AssistantServiceRegistration'],
            transformResponse: (response: any) => transformResponseToAssistantServiceRegistration(response),
        }),
        getAssistantServiceRegistrations: builder.query<
            AssistantServiceRegistration[],
            {
                userIds?: string[];
                onlineOnly?: boolean;
            }
        >({
            query: ({ userIds, onlineOnly }) => {
                const params: Record<string, any> = {};
                if (userIds && userIds.length > 0) {
                    params.user_id = userIds;
                }
                if (onlineOnly) {
                    params.assistant_service_online = true;
                }
                return {
                    url: '/assistant-service-registrations',
                    params,
                };
            },
            providesTags: ['AssistantServiceRegistration'],
            transformResponse: (response: any) =>
                response.assistant_service_registrations.map(transformResponseToAssistantServiceRegistration),
        }),
        createAssistantServiceRegistration: builder.mutation<
            AssistantServiceRegistration,
            NewAssistantServiceRegistration
        >({
            query: (body) => ({
                url: '/assistant-service-registrations',
                method: 'POST',
                body: transformRequestToAssistantServiceRegistration(body),
            }),
            invalidatesTags: ['AssistantServiceRegistration'],
            transformResponse: (response: any) => transformResponseToAssistantServiceRegistration(response),
        }),
        removeAssistantServiceRegistration: builder.mutation<{ id: string }, string>({
            query: (id) => ({
                url: `/assistant-service-registrations/${encodeURIComponent(id)}`,
                method: 'DELETE',
            }),
            invalidatesTags: ['AssistantServiceRegistration'],
        }),
        updateAssistantServiceRegistration: builder.mutation<
            AssistantServiceRegistration,
            {
                id: string;
                assistantServiceRegistration: Partial<AssistantServiceRegistration> &
                    Pick<AssistantServiceRegistration, 'name' | 'description' | 'includeInListing'>;
            }
        >({
            query: ({ id, assistantServiceRegistration }) => ({
                url: `/assistant-service-registrations/${encodeURIComponent(id)}`,
                method: 'PATCH',
                body: {
                    name: assistantServiceRegistration.name,
                    description: assistantServiceRegistration.description,
                    include_in_listing: assistantServiceRegistration.includeInListing,
                },
            }),
            invalidatesTags: ['AssistantServiceRegistration'],
            transformResponse: (response: any) => transformResponseToAssistantServiceRegistration(response),
        }),
        resetAssistantServiceRegistrationApiKey: builder.mutation<AssistantServiceRegistration, string>({
            query: (id) => ({
                url: `/assistant-service-registrations/${encodeURIComponent(id)}/api-key`,
                method: 'POST',
            }),
            invalidatesTags: ['AssistantServiceRegistration'],
            transformResponse: (response: any) => transformResponseToAssistantServiceRegistration(response),
        }),
    }),
    overrideExisting: false,
});

export const {
    useGetAssistantServiceInfoQuery,
    useGetAssistantServiceInfosQuery,
    useGetAssistantServiceRegistrationQuery,
    useGetAssistantServiceRegistrationsQuery,
    useCreateAssistantServiceRegistrationMutation,
    useRemoveAssistantServiceRegistrationMutation,
    useUpdateAssistantServiceRegistrationMutation,
    useResetAssistantServiceRegistrationApiKeyMutation,
} = assistantServiceApi;

const transformResponseToAssistantServiceInfo = (response: any): AssistantServiceInfo => ({
    assistantServiceId: response.assistant_service_id,
    templates: response.templates.map((template: any) => ({
        id: template.id,
        name: template.name,
        description: template.description,
        config: {
            config: template.config.config,
            jsonSchema: template.config.json_schema,
            uiSchema: template.config.ui_schema,
        },
    })),
    metadata: response.metadata,
});

const transformResponseToAssistantServiceInfos = (response: any): AssistantServiceInfo[] =>
    (response.assistant_service_infos || []).map(transformResponseToAssistantServiceInfo);

const transformResponseToAssistantServiceRegistration = (response: any): AssistantServiceRegistration => ({
    assistantServiceId: response.assistant_service_id,
    assistantServiceOnline: response.assistant_service_online,
    assistantServiceUrl: response.assistant_service_url,
    name: response.name,
    description: response.description,
    includeInListing: response.include_in_listing,
    createdDateTime: response.create_date_time,
    createdByUserId: response.created_by_user_id,
    createdByUserName: response.created_by_user_name,
    apiKeyName: response.api_key_name,
    apiKey: response.api_key,
});

const transformRequestToAssistantServiceRegistration = (request: NewAssistantServiceRegistration): any => ({
    assistant_service_id: request.assistantServiceId,
    name: request.name,
    description: request.description,
    include_in_listing: request.includeInListing,
});


=== File: workbench-app/src/services/workbench/conversation.ts ===
import { Conversation } from '../../models/Conversation';
import { ConversationMessage, conversationMessageFromJSON } from '../../models/ConversationMessage';
import { ConversationMessageDebug, conversationMessageDebugFromJSON } from '../../models/ConversationMessageDebug';
import { transformResponseToConversationParticipant } from './participant';
import { workbenchApi } from './workbench';

interface GetConversationMessagesProps {
    conversationId: string;
    messageTypes?: string[];
    participantRoles?: string[];
    participantIds?: string[];
}

export const conversationApi = workbenchApi.injectEndpoints({
    endpoints: (builder) => ({
        createConversation: builder.mutation<Conversation, Partial<Conversation>>({
            query: (body) => ({
                url: '/conversations',
                method: 'POST',
                body: transformConversationForRequest(body),
            }),
            invalidatesTags: ['Conversation'],
            transformResponse: (response: any) => transformResponseToConversation(response),
        }),
        duplicateConversation: builder.mutation<
            { conversationIds: string[]; assistantIds: string[] },
            Pick<Conversation, 'id' | 'title'>
        >({
            query: (body) => ({
                url: `/conversations/${body.id}`,
                method: 'POST',
                body: transformConversationForRequest(body),
            }),
            invalidatesTags: ['Conversation'],
            transformResponse: (response: any) => transformResponseToImportResult(response),
        }),
        updateConversation: builder.mutation<Conversation, Partial<Conversation> & Pick<Conversation, 'id'>>({
            query: (body) => ({
                url: `/conversations/${body.id}`,
                method: 'PATCH',
                body: transformConversationForRequest(body),
            }),
            invalidatesTags: ['Conversation'],
            transformResponse: (response: any) => transformResponseToConversation(response),
        }),
        getConversations: builder.query<Conversation[], void>({
            query: () => '/conversations',
            providesTags: ['Conversation'],
            transformResponse: (response: any) => response.conversations.map(transformResponseToConversation),
        }),
        getAssistantConversations: builder.query<Conversation[], string>({
            query: (id) => `/assistants/${id}/conversations`,
            providesTags: ['Conversation'],
            transformResponse: (response: any) => response.conversations.map(transformResponseToConversation),
        }),
        getConversation: builder.query<Conversation, string>({
            query: (id) => `/conversations/${id}`,
            providesTags: ['Conversation'],
            transformResponse: (response: any) => transformResponseToConversation(response),
        }),
        getConversationMessages: builder.query<ConversationMessage[], GetConversationMessagesProps>({
            async queryFn(
                {
                    conversationId,
                    messageTypes = ['chat', 'log', 'note', 'notice', 'command', 'command-response'],
                    participantRoles,
                    participantIds,
                },
                _queryApi,
                _extraOptions,
                fetchWithBQ,
            ) {
                let allMessages: ConversationMessage[] = [];
                let before = undefined;

                while (true) {
                    const params = new URLSearchParams();

                    if (before) {
                        params.set('before', before);
                    }

                    // Append parameters to the query string, one by one for arrays
                    messageTypes?.forEach((type) => params.append('message_type', type));
                    participantRoles?.forEach((role) => params.append('participant_role', role));
                    participantIds?.forEach((id) => params.append('participant_id', id));

                    const limit = 500;
                    params.set('limit', String(limit));

                    const url = `/conversations/${conversationId}/messages?${params.toString()}`;

                    const response = await fetchWithBQ(url);
                    if (response.error) {
                        return { error: response.error };
                    }

                    const messages: ConversationMessage[] = transformResponseToConversationMessages(response.data);
                    allMessages = [...allMessages, ...messages];

                    if (messages.length !== limit) {
                        break;
                    }

                    before = messages[0].id;
                }

                return { data: allMessages };
            },
            providesTags: ['Conversation', 'ConversationMessage'],
        }),
        getConversationMessageDebugData: builder.query<
            ConversationMessageDebug,
            { conversationId: string; messageId: string }
        >({
            query: ({ conversationId, messageId }) =>
                `/conversations/${conversationId}/messages/${messageId}/debug_data`,
            transformResponse: (response: any) => transformResponseToConversationMessageDebug(response),
        }),
        createConversationMessage: builder.mutation<
            ConversationMessage,
            { conversationId: string } & Partial<ConversationMessage> &
                Pick<ConversationMessage, 'content' | 'messageType' | 'metadata'>
        >({
            query: (input) => ({
                url: `/conversations/${input.conversationId}/messages`,
                method: 'POST',
                body: transformMessageForRequest(input),
            }),
            invalidatesTags: ['Conversation'],
            transformResponse: (response: any) => transformResponseToMessage(response),
        }),
        deleteConversationMessage: builder.mutation<void, { conversationId: string; messageId: string }>({
            query: ({ conversationId, messageId }) => ({
                url: `/conversations/${conversationId}/messages/${messageId}`,
                method: 'DELETE',
            }),
            invalidatesTags: ['Conversation'],
        }),
    }),
    overrideExisting: false,
});

// Non-hook helpers

export const {
    useCreateConversationMutation,
    useDuplicateConversationMutation,
    useUpdateConversationMutation,
    useGetConversationsQuery,
    useLazyGetConversationQuery,
    useGetAssistantConversationsQuery,
    useGetConversationQuery,
    useGetConversationMessagesQuery,
    useGetConversationMessageDebugDataQuery,
    useCreateConversationMessageMutation,
    useDeleteConversationMessageMutation,
} = conversationApi;

export const updateGetConversationMessagesQueryData = (
    options: GetConversationMessagesProps,
    messages: ConversationMessage[],
) => conversationApi.util.updateQueryData('getConversationMessages', options, () => messages);

const transformConversationForRequest = (conversation: Partial<Conversation>) => ({
    id: conversation.id,
    title: conversation.title,
    metadata: conversation.metadata,
});

const transformResponseToConversation = (response: any): Conversation => {
    try {
        return {
            id: response.id,
            ownerId: response.owner_id,
            title: response.title,
            created: response.created_datetime,
            latest_message: response.latest_message ? transformResponseToMessage(response.latest_message) : undefined,
            participants: response.participants.map(transformResponseToConversationParticipant),
            metadata: response.metadata,
            conversationPermission: response.conversation_permission,
            importedFromConversationId: response.imported_from_conversation_id,
        };
    } catch (error) {
        throw new Error(`Failed to transform conversation response: ${error}`);
    }
};

const transformResponseToImportResult = (response: any): { conversationIds: string[]; assistantIds: string[] } => {
    try {
        return {
            conversationIds: response.conversation_ids,
            assistantIds: response.assistant_ids,
        };
    } catch (error) {
        throw new Error(`Failed to transform import result response: ${error}`);
    }
};

const transformResponseToConversationMessages = (response: any): ConversationMessage[] => {
    try {
        return response.messages.map(transformResponseToMessage);
    } catch (error) {
        throw new Error(`Failed to transform messages response: ${error}`);
    }
};

const transformResponseToMessage = (response: any): ConversationMessage => {
    try {
        return conversationMessageFromJSON(response);
    } catch (error) {
        throw new Error(`Failed to transform message response: ${error}`);
    }
};

const transformResponseToConversationMessageDebug = (response: any): ConversationMessageDebug => {
    try {
        return conversationMessageDebugFromJSON(response);
    } catch (error) {
        throw new Error(`Failed to transform message debug response: ${error}`);
    }
};

const transformMessageForRequest = (message: Partial<ConversationMessage>) => {
    const request: Record<string, any> = {
        timestamp: message.timestamp,
        content: message.content,
        message_type: message.messageType,
        content_type: message.contentType,
        filenames: message.filenames,
        metadata: message.metadata,
    };

    if (message.sender) {
        request.sender = {
            participant_id: message.sender.participantId,
            participant_role: message.sender.participantRole,
        };
    }

    return request;
};


=== File: workbench-app/src/services/workbench/file.ts ===
import { ConversationFile } from '../../models/ConversationFile';
import { workbenchApi } from './workbench';

const fileApi = workbenchApi.injectEndpoints({
    endpoints: (builder) => ({
        getConversationFiles: builder.query<ConversationFile[], string>({
            query: (id) => `/conversations/${id}/files`,
            providesTags: ['Conversation'],
            transformResponse: (response: any) => response.files.map(transformResponseToFile),
        }),
        uploadConversationFiles: builder.mutation<ConversationFile, { conversationId: string; files: File[] }>({
            query: ({ conversationId, files }) => {
                return {
                    url: `/conversations/${conversationId}/files`,
                    method: 'PUT',
                    body: transformConversationFilesForRequest(files),
                };
            },
            invalidatesTags: ['Conversation'],
            transformResponse: (response: any) => transformResponseToFile(response),
        }),
        deleteConversationFile: builder.mutation<void, { conversationId: string; filename: string }>({
            query: ({ conversationId, filename }) => ({
                url: `/conversations/${conversationId}/files/${filename}`,
                method: 'DELETE',
            }),
            invalidatesTags: ['Conversation'],
        }),
    }),
    overrideExisting: false,
});

export const { useGetConversationFilesQuery, useUploadConversationFilesMutation, useDeleteConversationFileMutation } =
    fileApi;

const transformResponseToFile = (response: any): ConversationFile => {
    try {
        return {
            name: response.filename,
            created: response.created_datetime,
            updated: response.updated_datetime,
            size: response.file_size,
            version: response.current_version,
            contentType: response.content_type,
            metadata: response.metadata,
        };
    } catch (error) {
        throw new Error(`Failed to transform file response: ${error}`);
    }
};

const transformConversationFilesForRequest = (files: File[]) => {
    const formData = new FormData();
    for (var i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }
    return formData;
};


=== File: workbench-app/src/services/workbench/index.ts ===
// Copyright (c) Microsoft. All rights reserved.

export * from './assistant';
export * from './assistantService';
export * from './conversation';
export * from './file';
export * from './participant';
export * from './state';
export * from './workbench';


=== File: workbench-app/src/services/workbench/participant.ts ===
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { workbenchApi } from './workbench';

const participantApi = workbenchApi.injectEndpoints({
    endpoints: (builder) => ({
        getConversationParticipants: builder.query<ConversationParticipant[], string>({
            query: (conversationId) => `/conversations/${conversationId}/participants?include_inactive=true`,
            providesTags: ['Conversation'],
            transformResponse: (response: any) => transformResponseToConversationParticipants(response),
        }),
        addConversationParticipant: builder.mutation<
            void,
            { conversationId: string; participantId: string; metadata?: Record<string, any> }
        >({
            query: ({ conversationId, participantId, metadata }) => ({
                url: `/conversations/${conversationId}/participants/${participantId}`,
                method: 'PUT',
                body: { active_participant: true, metadata },
            }),
            invalidatesTags: ['Conversation'],
        }),
        updateConversationParticipant: builder.mutation<
            void,
            { conversationId: string; participantId: string; status?: string; metadata?: Record<string, any> }
        >({
            query: ({ conversationId, participantId, status, metadata }) => ({
                url: `/conversations/${conversationId}/participants/${participantId}`,
                method: 'PUT',
                body: { status, active_participant: true, metadata },
            }),
            // This mutation should not invalidate the conversation query because it does not add or remove participants
            invalidatesTags: [],
        }),
        removeConversationParticipant: builder.mutation<void, { conversationId: string; participantId: string }>({
            query: ({ conversationId, participantId }) => ({
                url: `/conversations/${conversationId}/participants/${participantId}`,
                method: 'PUT',
                body: { active_participant: false },
            }),
            invalidatesTags: ['Conversation'],
        }),
    }),
    overrideExisting: false,
});

// Non-hook helpers

export const updateGetConversationParticipantsQueryData = (conversationId: string, data: any) =>
    participantApi.util.updateQueryData('getConversationParticipants', conversationId, () =>
        transformResponseToConversationParticipants(data),
    );

export const {
    useGetConversationParticipantsQuery,
    useAddConversationParticipantMutation,
    useUpdateConversationParticipantMutation,
    useRemoveConversationParticipantMutation,
} = participantApi;

const transformResponseToConversationParticipants = (response: any): ConversationParticipant[] => {
    try {
        return response.participants.map(transformResponseToConversationParticipant);
    } catch (error) {
        throw new Error(`Failed to transform participants response: ${error}`);
    }
};

export const transformResponseToConversationParticipant = (response: any): ConversationParticipant => {
    try {
        return {
            id: response.id,
            conversationId: response.conversation_id,
            role: response.role,
            name: response.name,
            image: response.image ?? undefined,
            online: response.online ?? undefined,
            status: response.status,
            statusTimestamp: response.status_updated_timestamp,
            conversationPermission: response.conversation_permission,
            active: response.active_participant,
            metadata: response.metadata,
        };
    } catch (error) {
        throw new Error(`Failed to transform participant response: ${error}`);
    }
};


=== File: workbench-app/src/services/workbench/share.ts ===
import { ConversationShare } from '../../models/ConversationShare';
import { ConversationShareRedemption } from '../../models/ConversationShareRedemption';
import { workbenchApi } from './workbench';

const shareApi = workbenchApi.injectEndpoints({
    endpoints: (builder) => ({
        createShare: builder.mutation<
            ConversationShare,
            Pick<ConversationShare, 'conversationId' | 'label' | 'conversationPermission' | 'metadata'>
        >({
            query: (body) => ({
                url: '/conversation-shares',
                method: 'POST',
                body: transformConversationShareForRequest(body),
            }),
            invalidatesTags: ['ConversationShare'],
            transformResponse: (response: any) => transformResponseToConversationShare(response),
        }),
        getShares: builder.query<
            ConversationShare[],
            { conversationId: string | undefined; includeUnredeemable: boolean }
        >({
            query: ({ conversationId, includeUnredeemable }) =>
                `/conversation-shares?include_unredeemable=${includeUnredeemable}` +
                (conversationId ? `&conversation_id=${conversationId}` : ''),
            providesTags: ['ConversationShare'],
            transformResponse: (response: any) => transformResponseToConversationShares(response),
        }),
        getShare: builder.query<ConversationShare, string>({
            query: (conversationShareId: string) => `/conversation-shares/${encodeURIComponent(conversationShareId)}`,
            providesTags: ['ConversationShare'],
            transformResponse: (response: any) => transformResponseToConversationShare(response),
        }),
        deleteShare: builder.mutation<void, string>({
            query: (conversationShareId: string) => ({
                url: `/conversation-shares/${conversationShareId}`,
                method: 'DELETE',
            }),
            invalidatesTags: ['ConversationShare'],
        }),
        redeemShare: builder.mutation<ConversationShareRedemption, string>({
            query: (conversationShareId: string) => ({
                url: `/conversation-shares/${conversationShareId}/redemptions`,
                method: 'POST',
            }),
            // redeeming a share can add a user to a conversation
            invalidatesTags: ['ConversationShare', 'Conversation'],
            transformResponse: (response: any) => transformResponseToConversationShareRedemption(response),
        }),
    }),
    overrideExisting: false,
});

export const {
    useGetSharesQuery,
    useGetShareQuery,
    useDeleteShareMutation,
    useRedeemShareMutation,
    useCreateShareMutation,
} = shareApi;

const transformConversationShareForRequest = (
    newShare: Pick<ConversationShare, 'conversationId' | 'label' | 'conversationPermission' | 'metadata'>,
): any => {
    return {
        conversation_id: newShare.conversationId,
        label: newShare.label,
        conversation_permission: newShare.conversationPermission,
        metadata: newShare.metadata,
    };
};

const transformResponseToConversationShares = (response: any): ConversationShare[] => {
    try {
        return response.conversation_shares.map(transformResponseToConversationShare);
    } catch (error) {
        throw new Error(`Failed to transform shares response: ${error}`);
    }
};

const transformResponseToConversationShare = (response: any): ConversationShare => {
    try {
        return {
            id: response.id,
            createdByUser: response.created_by_user,
            label: response.label,
            conversationId: response.conversation_id,
            conversationTitle: response.conversation_title,
            conversationPermission: response.conversation_permission,
            isRedeemable: response.is_redeemable,
            createdDateTime: response.created_datetime,
            metadata: response.metadata,
        };
    } catch (error) {
        throw new Error(`Failed to transform share response: ${error}`);
    }
};

const transformResponseToConversationShareRedemption = (response: any): ConversationShareRedemption => {
    try {
        return {
            id: response.id,
            conversationId: response.conversation_id,
            conversationShareId: response.conversation_share_id,
            redeemedByUser: response.redeemed_by_user,
            conversationPermission: response.conversation_permission,
            createdDateTime: response.created_datetime,
            isNewParticipant: response.new_participant,
        };
    } catch (error) {
        throw new Error(`Failed to transform share response: ${error}`);
    }
};


=== File: workbench-app/src/services/workbench/state.ts ===
import { Config } from '../../models/Config';
import { ConversationState } from '../../models/ConversationState';
import { ConversationStateDescription } from '../../models/ConversationStateDescription';
import { workbenchApi } from './workbench';

const stateApi = workbenchApi.injectEndpoints({
    endpoints: (builder) => ({
        getConfig: builder.query<Config, { assistantId: string }>({
            query: ({ assistantId }) => `/assistants/${assistantId}/config`,
            providesTags: ['Config'],
            transformResponse: (response: any) => transformResponseToConfig(response),
        }),
        updateConfig: builder.mutation<Config, { assistantId: string; config: Config }>({
            query: (body) => ({
                url: `/assistants/${body.assistantId}/config`,
                method: 'PUT',
                body: transformConfigForRequest(body.config),
            }),
            invalidatesTags: ['Config', 'State'],
            transformResponse: (response: any) => transformResponseToConfig(response),
        }),
        getConversationStateDescriptions: builder.query<
            ConversationStateDescription[],
            { assistantId: string; conversationId: string }
        >({
            query: ({ assistantId, conversationId }) =>
                `/assistants/${assistantId}/conversations/${conversationId}/states`,
            providesTags: ['State'],
            transformResponse: (response: any) =>
                response.states.map((stateDescription: any) => ({
                    id: stateDescription.id,
                    displayName: stateDescription.display_name,
                    description: stateDescription.description,
                    enabled: stateDescription.enabled,
                })),
        }),
        getConversationState: builder.query<
            ConversationState,
            { assistantId: string; conversationId: string; stateId: string }
        >({
            query: ({ assistantId, conversationId, stateId }) =>
                `/assistants/${assistantId}/conversations/${conversationId}/states/${stateId}`,
            providesTags: ['State'],
            transformResponse: (response: any, _meta, { stateId }) =>
                transformResponseToConversationState(response, stateId),
        }),
        updateConversationState: builder.mutation<
            ConversationState,
            { assistantId: string; conversationId: string; state: ConversationState }
        >({
            query: (body) => ({
                url: `/assistants/${body.assistantId}/conversations/${body.conversationId}/states/${body.state.id}`,
                method: 'PUT',
                body: transformConversationStateForRequest(body.state),
            }),
            invalidatesTags: ['State'],
            transformResponse: (response: any, _meta, { state }) =>
                transformResponseToConversationState(response, state.id),
        }),
    }),
    overrideExisting: false,
});

export const {
    useGetConfigQuery,
    useUpdateConfigMutation,
    useGetConversationStateDescriptionsQuery,
    useGetConversationStateQuery,
    useUpdateConversationStateMutation,
} = stateApi;

const transformResponseToConfig = (response: any) => {
    try {
        return {
            config: response.config,
            jsonSchema: response.json_schema,
            uiSchema: response.ui_schema,
        };
    } catch (error) {
        throw new Error(`Failed to transform config response: ${error}`);
    }
};

const transformConfigForRequest = (config: Config) => ({
    config: config.config,
    json_schema: config.jsonSchema,
    ui_schema: config.uiSchema,
});

const transformResponseToConversationState = (response: any, stateId: string) => {
    try {
        return {
            id: stateId,
            data: response.data,
            jsonSchema: response.json_schema,
            uiSchema: response.ui_schema,
        };
    } catch (error) {
        throw new Error(`Failed to transform conversation state response: ${error}`);
    }
};

const transformConversationStateForRequest = (conversationState: ConversationState) => ({
    data: conversationState.data,
    json_schema: conversationState.jsonSchema,
    ui_schema: conversationState.uiSchema,
});


=== File: workbench-app/src/services/workbench/workbench.ts ===
// Copyright (c) Microsoft. All rights reserved.

import { generateUuid } from '@azure/ms-rest-js';
import { InteractionRequiredAuthError } from '@azure/msal-browser';
import { BaseQueryFn, FetchArgs, FetchBaseQueryError, createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { AuthHelper } from '../../libs/AuthHelper';
import { getEnvironment } from '../../libs/useEnvironment';
import { getMsalInstance } from '../../main';
import { RootState } from '../../redux/app/store';

const onAuthFailure = async () => {
    // If authentication fails, we need to reload the current page, after
    // which the user will be redirected to the login page.
    console.warn('clearing MSAL cache due to auth failure');
    const msalInstance = await getMsalInstance();
    msalInstance.clearCache();
    window.location.reload();
};

const dynamicBaseQuery: BaseQueryFn<string | FetchArgs, unknown, FetchBaseQueryError> = async (
    args,
    workbenchApi,
    extraOptions,
) => {
    const { environmentId } = (workbenchApi.getState() as RootState).settings;
    const environment = getEnvironment(environmentId);

    const prepareHeaders = async (headers: Headers) => {
        const msalInstance = await getMsalInstance();
        const account = msalInstance.getActiveAccount();
        if (!account) {
            await onAuthFailure();
            throw new Error('No active account');
        }

        const response = await msalInstance
            .acquireTokenSilent({
                ...AuthHelper.loginRequest,
                account,
            })
            .catch(async (error) => {
                if (error instanceof InteractionRequiredAuthError) {
                    return await AuthHelper.loginAsync(msalInstance);
                }
                await onAuthFailure();
                throw error;
            });
        if (!response) {
            await onAuthFailure();
            throw new Error('Could not acquire token');
        }

        headers.set('Authorization', `Bearer ${response.accessToken}`);
        headers.set('X-Request-ID', generateUuid().replace(/-/g, '').toLowerCase());
        return headers;
    };

    const rawBaseQuery = fetchBaseQuery({ baseUrl: environment.url, prepareHeaders });

    return rawBaseQuery(args, workbenchApi, extraOptions);
};

export const workbenchApi = createApi({
    reducerPath: 'workbenchApi',
    baseQuery: dynamicBaseQuery,
    tagTypes: [
        'AssistantServiceRegistration',
        'AssistantServiceInfo',
        'Assistant',
        'Conversation',
        'ConversationShare',
        'Config',
        'State',
        'ConversationMessage',
    ],
    endpoints: () => ({}),
});


=== File: workbench-app/src/vite-env.d.ts ===
/// <reference types="vite/client" />


