// Copyright (c) Microsoft. All rights reserved.

import { diff } from 'deep-object-diff';
import merge from 'deepmerge';

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

const getTimestampForExport = () => {
    // return in format YYYYMMDDHHmmss
    const date = new Date();
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const hours = date.getHours();
    const minutes = date.getMinutes();

    const formattedMonth = month < 10 ? `0${month}` : month;

    return `${year}${formattedMonth}${day}${hours}${minutes}`;
};

export const Utility = {
    deepEqual,
    deepCopy,
    deepMerge,
    deepDiff,
    getTimestampForExport,
};
