// Copyright (c) Microsoft. All rights reserved.

import dayjs from 'dayjs';
import tz from 'dayjs/plugin/timezone';
import utc from 'dayjs/plugin/utc';
import { diff } from 'deep-object-diff';
import merge from 'deepmerge';

dayjs.extend(utc);
dayjs.extend(tz);

const deepEqual = (object1: object, object2: object) => {
    const differences = diff(object1, object2);
    return Object.keys(differences).length === 0;
};

const deepCopy = (object: object): object => {
    return JSON.parse(JSON.stringify(object));
};

const deepMerge = (target: object, source: object): object => {
    return merge(target, source, {
        arrayMerge: (_destinationArray: any[], sourceArray: any[]) => sourceArray,
    });
};

// Check if two values are equal, including handling undefined, null, and empty string
const isEqual = (value1: any, value2: any): boolean => {
    if (value1 === value2) return true;
    if (
        (value1 === undefined || value1 === null || value1 === '') &&
        (value2 === undefined || value2 === null || value2 === '')
    ) {
        return true;
    }
    return false;
};

// Deep diff between two objects, using dot-notation for nested keys
// Returns an object with the differences
const deepDiff = (obj1: ObjectLiteral, obj2: ObjectLiteral, parentKey = ''): ObjectLiteral => {
    const diff: ObjectLiteral = {};
    const allKeys = new Set([...Object.keys(obj1), ...Object.keys(obj2)]);

    allKeys.forEach((key) => {
        const value1 = obj1[key];
        const value2 = obj2[key];
        const currentKey = parentKey ? `${parentKey}.${key}` : key;

        if (!isEqual(value1, value2)) {
            if (typeof value1 === 'object' && typeof value2 === 'object') {
                const nestedDiff = deepDiff(value1, value2, currentKey);
                if (Object.keys(nestedDiff).length > 0) {
                    diff[currentKey] = nestedDiff;
                }
            } else {
                diff[currentKey] = { oldValue: value1, newValue: value2 };
            }
        }
    });

    return diff;
};

type ObjectLiteral = { [key: string]: any };

const debounce = (func: Function, wait: number) => {
    let timeout: NodeJS.Timeout;
    return function (this: any, ...args: any[]) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
};

const toDayJs = (value: string | Date, timezone: string = dayjs.tz.guess()) => {
    return dayjs.utc(value).tz(timezone);
};

const toDate = (value: string, timezone: string = dayjs.tz.guess()): Date => {
    return toDayJs(value, timezone).toDate();
};

const toSimpleDateString = (value: string | Date, timezone: string = dayjs.tz.guess()): string => {
    const now = dayjs.utc();
    const date = toDayJs(value, timezone);

    // If the date is today, return the time
    if (date.isSame(now, 'day')) {
        return date.format('h:mm A');
    }

    // If the date is within the last week, return the day of the week
    if (date.isAfter(now.subtract(7, 'days'))) {
        return date.format('ddd');
    }

    // Otherwise, return the month and day if it's within the current year
    if (date.isSame(now, 'year')) {
        return date.format('MMM D');
    }

    // Otherwise, return the month, day, and year
    return date.format('MMM D, YYYY');
};

const toFormattedDateString = (value: string | Date, format: string, timezone: string = dayjs.tz.guess()): string => {
    return toDayJs(value, timezone).format(format);
};

const getTimestampForFilename = (timezone: string = dayjs.tz.guess()) => {
    // return in format YYYYMMDDHHmm
    return toDayJs(new Date(), timezone).format('YYYYMMDDHHmm');
};

const sortKeys = (obj: any): any => {
    if (Array.isArray(obj)) {
        return obj.map(sortKeys);
    } else if (obj !== null && typeof obj === 'object') {
        return Object.keys(obj)
            .sort()
            .reduce((result: any, key: string) => {
                result[key] = sortKeys(obj[key]);
                return result;
            }, {});
    }
    return obj;
};

const errorToMessageString = (error?: Record<string, any> | string) => {
    // Check if the error is undefined
    if (error === undefined) {
        // Return an empty string
        return undefined;
    }

    // Check if the error is a string
    if (typeof error === 'string') {
        // Return the error as is
        return error;
    }

    // Set the message for the error message, displayed as the error details
    let message = '';

    // Check if the action payload contains a 'data.detail' property
    if ('data' in error && 'detail' in error.data) {
        // Check if the 'detail' property is a string
        if (typeof error.data.detail === 'string') {
            // Set the message to the 'detail' property
            message = (error.data as { detail: string }).detail;
        } else {
            // Set the message to the 'detail' property as a stringified JSON object
            message = JSON.stringify(error.data.detail);
        }
    } else if ('message' in error) {
        message = error.message;
    } else if ('error' in error && 'status' in error) {
        message = error.status;

        // Additional error handling for specific error types
        if (error.status === 'FETCH_ERROR') {
            message = `Error connecting to Semantic Workbench service, ensure service is running`;
            // Check if the url contains a GitHub Codespaces hostname
            if (error.meta.baseQueryMeta.request.url.includes('app.github.dev')) {
                // Append a message to the error message to indicate it may be due
                // to the port not being forwarded correctly
                message = `${message} and port is visible`;
            }
        }
    }

    return message;
};

export const Utility = {
    deepEqual,
    deepCopy,
    deepMerge,
    deepDiff,
    debounce,
    toDate,
    toSimpleDateString,
    toFormattedDateString,
    getTimestampForFilename,
    sortKeys,
    errorToMessageString,
};
