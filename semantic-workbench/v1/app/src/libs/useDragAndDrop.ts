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
