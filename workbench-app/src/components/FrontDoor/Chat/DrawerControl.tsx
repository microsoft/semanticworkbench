import {
    Drawer,
    DrawerBody,
    DrawerHeader,
    DrawerHeaderTitle,
    makeStyles,
    mergeClasses,
    shorthands,
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
        ...shorthands.border(tokens.strokeWidthThick, 'solid', tokens.colorNeutralStroke2),
        overflow: 'hidden',

        display: 'flex',
        height: '100%',
        boxSizing: 'border-box',
        backgroundColor: '#fff',
        userSelect: 'auto',
    },
    rootResizerActive: {
        userSelect: 'none',
    },
    drawer: {
        willChange: 'width',
        transitionProperty: 'width',
        transitionDuration: '16.666ms', // 60fps
        // minWidth: '400px',
    },
    // drawerContainer: {
    //     top: 0,
    //     height: '100%',
    //     transition: `width ${tokens.durationNormal} ${tokens.curveEasyEase}`,
    //     overflow: 'hidden',
    //     backgroundColor: tokens.colorNeutralBackground1,
    //     zIndex: tokens.zIndexContent,
    //     display: 'flex',
    //     flexDirection: 'column',
    //     paddingTop: tokens.spacingVerticalXXL,
    //     boxSizing: 'border-box',

    //     '&.left': {
    //         ...shorthands.borderRight(tokens.strokeWidthThick, 'solid', tokens.colorNeutralStroke3),
    //     },

    //     '&.right': {
    //         ...shorthands.borderLeft(tokens.strokeWidthThick, 'solid', tokens.colorNeutralStroke3),
    //     },
    // },
    // drawerTitle: {
    //     flexShrink: 0,
    //     ...shorthands.padding(
    //         tokens.spacingVerticalXXL,
    //         tokens.spacingHorizontalXXL,
    //         tokens.spacingVerticalS,
    //         tokens.spacingHorizontalXXL,
    //     ),
    // },
    // drawerContent: {
    //     flexGrow: 1,
    //     padding: tokens.spacingHorizontalM,
    //     overflow: 'auto',
    //     '::-webkit-scrollbar-track': {
    //         backgroundColor: tokens.colorNeutralBackground1,
    //     },
    //     '::-webkit-scrollbar-thumb': {
    //         backgroundColor: tokens.colorNeutralStencil1Alpha,
    //     },
    // },
    resizer: {
        width: '8px',
        position: 'absolute',
        top: 0,
        bottom: 0,
        cursor: 'col-resize',
        resize: 'horizontal',
        zIndex: tokens.zIndexOverlay,

        '&.left': {
            right: 0,
            borderRight: `1px solid ${tokens.colorNeutralBackground5}`,
        },

        '&.right': {
            left: 0,
            borderLeft: `1px solid ${tokens.colorNeutralBackground5}`,
        },

        ':hover': {
            borderRightWidth: '4px',
        },
    },
    resizerActive: {
        borderRightWidth: '4px',
        borderRightColor: tokens.colorNeutralBackground5Pressed,
    },
});

interface DrawerControlProps {
    classNames?: {
        container?: string;
        drawer?: string;
        header?: string;
        title?: string;
        body?: string;
    };
    open?: boolean;
    mode?: 'inline' | 'overlay';
    side?: 'left' | 'right';
    title?: string | React.ReactNode;
    size?: 'small' | 'medium' | 'large' | 'full';
    resizable?: boolean;
    children?: React.ReactNode;
}

export const DrawerControl: React.FC<DrawerControlProps> = (props) => {
    const { classNames, open, mode, side, title, size, resizable, children } = props;
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
                    const clientRect =
                        side === 'right'
                            ? sidebarRef.current.getBoundingClientRect().right
                            : sidebarRef.current.getBoundingClientRect().left;

                    const desiredWidth = clientRect - clientX;
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
            className={mergeClasses(classes.resizer, isResizing && classes.resizerActive, props.className)}
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
        <div className={mergeClasses(classes.root, isResizing && classes.rootResizerActive, classNames?.container)}>
            {resizable && <ResizeComponent className={side} />}
            <Drawer
                className={mergeClasses(classes.drawer, classNames?.drawer)}
                ref={sidebarRef}
                size={resizable ? undefined : size}
                style={resizable ? { width: `${chatWidthPercent}vw` } : undefined}
                onMouseDown={(event) => event.preventDefault()}
                position={side === 'right' ? 'end' : 'start'}
                open={open}
                type={mode}
            >
                <DrawerHeader className={classNames?.header}>
                    <DrawerHeaderTitle className={classNames?.title}>{titleContent}</DrawerHeaderTitle>
                </DrawerHeader>
                <DrawerBody className={classNames?.body}>{children}</DrawerBody>
            </Drawer>
        </div>
    );
};
