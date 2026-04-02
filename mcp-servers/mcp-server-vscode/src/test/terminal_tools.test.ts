import * as assert from 'assert';
import {
    closeTerminalSchema,
    createTerminalSchema,
    listTerminalsSchema,
    sendTerminalTextSchema,
} from '../tools/terminal_tools';

suite('Terminal Tools Schema Test Suite', () => {
    test('createTerminalSchema accepts valid params with all fields', () => {
        const result = createTerminalSchema.safeParse({
            name: 'my-terminal',
            cwd: '/tmp',
            command: 'echo hello',
            show: true,
        });
        assert.strictEqual(result.success, true);
    });

    test('createTerminalSchema accepts empty params (all optional)', () => {
        const result = createTerminalSchema.safeParse({});
        assert.strictEqual(result.success, true);
        if (result.success) {
            assert.strictEqual(result.data.show, true); // default value
        }
    });

    test('createTerminalSchema rejects invalid show type', () => {
        const result = createTerminalSchema.safeParse({ show: 'yes' });
        assert.strictEqual(result.success, false);
    });

    test('listTerminalsSchema accepts empty params', () => {
        const result = listTerminalsSchema.safeParse({});
        assert.strictEqual(result.success, true);
    });

    test('sendTerminalTextSchema requires name and text', () => {
        const valid = sendTerminalTextSchema.safeParse({
            name: 'my-terminal',
            text: 'ls -la',
        });
        assert.strictEqual(valid.success, true);

        const missingName = sendTerminalTextSchema.safeParse({ text: 'ls' });
        assert.strictEqual(missingName.success, false);

        const missingText = sendTerminalTextSchema.safeParse({ name: 'my-terminal' });
        assert.strictEqual(missingText.success, false);
    });

    test('sendTerminalTextSchema defaults addNewLine to true', () => {
        const result = sendTerminalTextSchema.safeParse({
            name: 'my-terminal',
            text: 'ls',
        });
        assert.strictEqual(result.success, true);
        if (result.success) {
            assert.strictEqual(result.data.addNewLine, true);
        }
    });

    test('closeTerminalSchema requires name', () => {
        const valid = closeTerminalSchema.safeParse({ name: 'my-terminal' });
        assert.strictEqual(valid.success, true);

        const missing = closeTerminalSchema.safeParse({});
        assert.strictEqual(missing.success, false);
    });
});
