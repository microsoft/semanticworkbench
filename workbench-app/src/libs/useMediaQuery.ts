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
