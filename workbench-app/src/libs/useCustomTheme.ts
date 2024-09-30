// Copyright (c) Microsoft. All rights reserved.

import { BrandVariants, createDarkTheme, createLightTheme } from '@fluentui/react-components';

export const getCustomTheme = (theme: string, brand?: string) => {
    let customBrandRamp: BrandVariants;
    switch (brand) {
        case 'orange':
            customBrandRamp = ramp2;
            break;
        case 'purple':
            customBrandRamp = ramp3;
            break;
        default:
            customBrandRamp = ramp1;
            break;
    }

    return theme === 'light' ? createLightTheme(customBrandRamp) : createDarkTheme(customBrandRamp);
};

// Generate at: https://fluentuipr.z22.web.core.windows.net/pull/24507/theme-designer/storybook/index.html?path=/story/themedesigner--page

const ramp1: BrandVariants = {
    10: '#000000',
    20: '#0F141D',
    30: '#152133',
    40: '#1A2E4C',
    50: '#1E3D65',
    60: '#1F4B80',
    70: '#1F5B9C',
    80: '#1D6BB9',
    90: '#177BD6',
    100: '#098BF5',
    110: '#469BFF',
    120: '#73ABFF',
    130: '#94BBFF',
    140: '#B1CCFF',
    150: '#CDDDFF',
    160: '#E6EEFF',
};

const ramp2: BrandVariants = {
    10: '#000000',
    20: '#210F04',
    30: '#381608',
    40: '#511C0B',
    50: '#6B210C',
    60: '#86260C',
    70: '#A32A0B',
    80: '#C02D09',
    90: '#DE3005',
    100: '#FD3300',
    110: '#FF6134',
    120: '#FF825B',
    130: '#FF9F7E',
    140: '#FFB9A0',
    150: '#FFD1C1',
    160: '#FFE9E1',
};

const ramp3: BrandVariants = {
    10: '#000000',
    20: '#1D0E20',
    30: '#32143B',
    40: '#481858',
    50: '#5F1A76',
    60: '#781A96',
    70: '#9118B7',
    80: '#AB12D9',
    90: '#C602FC',
    100: '#D142FF',
    110: '#DA65FF',
    120: '#E382FF',
    130: '#EA9DFF',
    140: '#F0B6FF',
    150: '#F6CFFF',
    160: '#FBE7FF',
};
