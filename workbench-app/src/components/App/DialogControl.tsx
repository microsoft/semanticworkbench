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
} from '@fluentui/react-components';
import React from 'react';

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
    additionalActions?: React.ReactElement[];
    onOpenChange?: (event: DialogOpenChangeEvent, data: DialogOpenChangeData) => void;
}

export const DialogControl: React.FC<DialogControlContent> = (props) => {
    const { open, defaultOpen, trigger, classNames, title, content, closeLabel, additionalActions, onOpenChange } =
        props;

    return (
        <Dialog open={open} defaultOpen={defaultOpen} onOpenChange={onOpenChange}>
            <DialogTrigger disableButtonEnhancement>{trigger}</DialogTrigger>
            <DialogSurface className={classNames?.dialogSurface}>
                <DialogBody>
                    {title && <DialogTitle>{title}</DialogTitle>}
                    {content && <DialogContent className={classNames?.dialogContent}>{content}</DialogContent>}
                    <DialogActions fluid>
                        <DialogTrigger disableButtonEnhancement>
                            <Button appearance={additionalActions ? 'secondary' : 'primary'}>
                                {closeLabel ?? 'Close'}
                            </Button>
                        </DialogTrigger>
                        {additionalActions?.map((action, index) => (
                            <DialogTrigger key={index} disableButtonEnhancement>
                                {action}
                            </DialogTrigger>
                        ))}
                    </DialogActions>
                </DialogBody>
            </DialogSurface>
        </Dialog>
    );
};
