import { DiagnosticSeverity } from 'vscode';
export declare const codeCheckerTool: (severityLevel?: DiagnosticSeverity) => {
    content: {
        type: string;
        text: string;
    }[];
    isError: boolean;
};
