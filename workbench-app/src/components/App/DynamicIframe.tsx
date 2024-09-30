import React from 'react';

interface DynamicIframeProps {
    source: string;
}

const DynamicIframe: React.FC<DynamicIframeProps> = (props) => {
    const { source } = props;
    const iframeRef = React.useRef<HTMLIFrameElement>(null);

    React.useEffect(() => {
        if (!iframeRef.current) {
            return;
        }

        const iframe = iframeRef.current;
        const contentWindow = iframe.contentWindow;

        if (!contentWindow) {
            return;
        }

        const resizeIframe = () => {
            const body = contentWindow.document.body;
            const html = contentWindow.document.documentElement;

            // Calculate the height including margins, padding, etc.
            const height = Math.max(
                body.scrollHeight,
                body.offsetHeight,
                html.clientHeight,
                html.scrollHeight,
                html.offsetHeight,
            );

            iframe.style.height = height + 'px';
        };

        const onLoad = () => {
            resizeIframe();

            const observer = new MutationObserver(resizeIframe);
            observer.observe(contentWindow.document.body, {
                childList: true,
                subtree: true,
                attributes: true,
            });
        };

        if (iframe) {
            iframe.addEventListener('load', onLoad);
        }

        return () => {
            if (iframe) {
                iframe.removeEventListener('load', onLoad);
            }
        };
    }, []);

    return (
        <iframe
            ref={iframeRef}
            srcDoc={source}
            style={{ width: '100%', border: 'none' }}
            title="Dynamic Iframe"
        ></iframe>
    );
};

export default DynamicIframe;
