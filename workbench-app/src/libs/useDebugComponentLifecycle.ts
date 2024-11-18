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
