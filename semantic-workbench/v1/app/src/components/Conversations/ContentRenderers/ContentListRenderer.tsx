// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { ContentRenderer } from './ContentRenderer';

interface ContentListRendererProps {
    contentList: string[];
}

export const ContentListRenderer: React.FC<ContentListRendererProps> = (props) => {
    const { contentList } = props;
    return (
        <div>
            {contentList.map((content, index) => (
                <ContentRenderer key={index} content={content} />
            ))}
        </div>
    );
};
