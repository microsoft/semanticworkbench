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
