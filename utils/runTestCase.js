function runTestCase(test_case_name, res) {
    const { spawn } = require('child_process');
    const path = require('path');
    const fs = require('fs');
    const rootDir = path.dirname(__dirname);
    const projectDir = path.join(rootDir, 'web-sentinel-test');
    console.log(`Running test case: ${test_case_name} in ${projectDir}`);
    res.setHeader('Content-Type', 'text/plain; charset=utf-8');
    res.write(`Running pytest ${test_case_name} in ${projectDir}\n\n`);
    const isWin = process.platform === 'win32';
    const venvWin = path.join(projectDir, '.venv','Scripts','python.exe');
    const venvUnix = path.join(projectDir, '.venv','bin','python');
    const pythonCmd = fs.existsSync(venvWin) ? venvWin : fs.existsSync(venvUnix) ? venvUnix : 'python';
    const proc = spawn(pythonCmd, ['-m','pytest', test_case_name], { cwd: projectDir });
    proc.stdout.on('data', (chunk) => {
        try { console.log(chunk.toString()); } catch (e) { console.log(String(chunk)); }
    });
    proc.stderr.on('data', (chunk) => {
        try { console.error(chunk.toString()); } catch (e) { console.error(String(chunk)); }
    });
    proc.on('error', (err) => {
        res.write(`\nFailed to start pytest: ${err.message}\n`);
        res.end();
    });
    proc.on('close', (code) => {
        res.write(`\nProcess exited with code ${code}\n`);
        res.end();
    });
}

module.exports = { runTestCase };