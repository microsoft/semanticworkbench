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
        // ...shorthands.border(tokens.strokeWidthThick, 'solid', tokens.colorNeutralStroke2),
        overflow: 'hidden',

        display: 'flex',
        height: '100%',
        boxSizing: 'border-box',
        backgroundColor: '#fff',
    },
    // rootResizerActive: {
    //     userSelect: 'none',
    // },
    drawer: {
        willChange: 'width',
        transitionProperty: 'width',
        transitionDuration: '16.666ms', // 60fps
    },
    title: {
        marginTop: tokens.spacingVerticalXL,
    },
    resizer: {
        width: tokens.spacingHorizontalS,
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
                    const minChatWidthPercent = Constants.app.minChatWidthPercent;
                    const maxWidth = Math.min(desiredWidthPercent, 100 - minChatWidthPercent);
                    const updatedChatWidthPercent = Math.max(minChatWidthPercent, maxWidth);
                    console.log(
                        `clientRect: ${clientRect}`,
                        `clientX: ${clientX}`,
                        `desiredWidth: ${desiredWidth}`,
                        `desiredWidthPercent: ${desiredWidthPercent}`,
                        `minChatWidthPercent: ${minChatWidthPercent}`,
                        `maxWidth: ${maxWidth}`,
                        `updatedChatWidthPercent: ${updatedChatWidthPercent}`,
                    );
                    dispatch(setChatWidthPercent(updatedChatWidthPercent));
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
                className={mergeClasses(classes.drawer, classNames?.drawer)}
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
