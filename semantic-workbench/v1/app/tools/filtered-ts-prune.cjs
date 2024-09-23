const { exec } = require('child_process');

exec('ts-prune', (error, stdout, stderr) => {
    if (error) {
        console.error(`Error: ${error.message}`);
        return;
    }
    if (stderr) {
        console.error(`Stderr: ${stderr}`);
        return;
    }
    const filteredOutput = stdout
        .split('\n')
        .filter((line) => !line.includes('used in module'))
        .join('\n');
    console.log(filteredOutput);
});
