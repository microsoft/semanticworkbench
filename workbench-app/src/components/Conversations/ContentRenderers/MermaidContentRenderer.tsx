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
