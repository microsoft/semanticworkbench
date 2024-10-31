import React, { MutableRefObject } from 'react';

interface IntersectionObserverOptions {
    root?: Element | null;
    rootMargin?: string;
    threshold?: number | number[];
}

export const useIsVisible = (options?: IntersectionObserverOptions): [MutableRefObject<null>, boolean] => {
    const [isVisible, setIsVisible] = React.useState(false);
    const isVisibleRef = React.useRef(null);

    React.useEffect(() => {
        const observer = new IntersectionObserver(([entry]) => {
            setIsVisible(entry.isIntersecting);
        }, options);

        const currentRef = isVisibleRef.current;
        if (currentRef) {
            observer.observe(currentRef);
        }

        return () => {
            if (currentRef) {
                observer.unobserve(currentRef);
            }
        };
    }, [options]);

    return [isVisibleRef, isVisible];
};
