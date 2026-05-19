import { DiagnosticSeverity, languages } from 'vscode';
import type { Diagnostic, Range } from 'vscode';

const serializeRange = (range: Range) => ({
    startLineNumber: range.start.line + 1,
    startColumn: range.start.character + 1,
    endLineNumber: range.end.line + 1,
    endColumn: range.end.character + 1,
});

const serializeCode = (code: Diagnostic['code']) => {
    if (typeof code === 'object' && code !== null) {
        return {
            value: code.value,
            target: code.target.toString(),
        };
    }

    return code;
};

/**
 * Retrieve diagnostics for the active workspace, with filtering by severity level.
 *
 * @param 'Warning' - Minimum severity level to include (default is Warning).
 */
export const codeCheckerTool = (severityLevel: DiagnosticSeverity = DiagnosticSeverity.Warning) => {
    // Retrieve diagnostics from all files
    const diagnosticsByFile = languages.getDiagnostics();

    // Filter diagnostics based on the target severity
    const aggregated = diagnosticsByFile
        .filter(([_uri, diags]) => diags.some((diag) => diag.severity <= severityLevel))
        .map(([uri, diags]) => ({
            file: uri.fsPath,
            diagnostics: diags
                .filter((diag) => diag.severity <= severityLevel)
                .map((diag) => ({
                    severity: DiagnosticSeverity[diag.severity],
                    message: diag.message,
                    source: diag.source || '',
                    code: serializeCode(diag.code),
                    range: serializeRange(diag.range),
                    tags: diag.tags,
                    relatedInformation: diag.relatedInformation?.map((info) => ({
                        message: info.message,
                        location: {
                            uri: info.location.uri.toString(),
                            range: serializeRange(info.location.range),
                        },
                    })),
                })),
        }));

    if (aggregated.length === 0) {
        // If no diagnostics found, return an empty result
        return { content: [{ type: 'text', text: 'No issues found.' }], isError: false };
    }

    // Otherwise, return the aggregated diagnostics as formatted JSON
    return { content: [{ type: 'text', text: JSON.stringify(aggregated, null, 2) }], isError: false };
};
