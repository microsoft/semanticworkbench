import React from 'react';

export const useUnreadMessages = () => {
    const [isMessageVisible, setIsVisible] = React.useState(false);
    const isMessageVisibleRef = React.useRef(null);

    React.useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                setIsVisible(entry.isIntersecting);
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

    return { isMessageVisibleRef, isMessageVisible };
};
