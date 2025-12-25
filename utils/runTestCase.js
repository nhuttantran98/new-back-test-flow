
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const ROOT_DIR = path.join(__dirname, '..');
const PROJECT_DIR = path.join(ROOT_DIR, 'project');

function getVenvPythonPath() {
    const venvWin = path.join(ROOT_DIR, '.venv', 'Scripts', 'python.exe');
    const venvUnix = path.join(ROOT_DIR, '.venv', 'bin', 'python');
    if (fs.existsSync(venvWin)) return venvWin;
    if (fs.existsSync(venvUnix)) return venvUnix;
    return 'python'; // fallback to system python
}

function runTestCase(testCases) {
    return new Promise((resolve, reject) => {
        // Normalize input to array
        const cases = Array.isArray(testCases) ? testCases : (testCases ? [testCases] : []);

        if (cases.length === 0) {
            return reject(new Error('No test cases provided.'));
        }

        // Build command: python -m pytest <case1> <case2> ...
        const pythonCmd = getVenvPythonPath();
        const args = ['-m', 'pytest', ...cases];

        // Spawn subprocess in project directory
        const proc = spawn(pythonCmd, args, { cwd: PROJECT_DIR, stdio: ['ignore', 'pipe', 'pipe'] });

        let stdout = '';
        let stderr = '';

        py.stdout.on('data', (data) => {
            const text = data.toString();
            stdout += text;
            console.log('PY:', text.trim());
        });

        py.stderr.on('data', (data) => {
            const text = data.toString();
            stderr += text;
            console.error('PY ERROR:', text.trim());
        });

        proc.stdout.on('data', (data) => {
            try {
                const text = data.toString();
                stdout += text;
                console.log(text.trim());
            } catch { 
                console.log(String(data)); 
            }
        });

        proc.stderr.on('data', (data) => {
            try {
                const text = data.toString();
                stdout += text;
                console.log(text.trim()); 
            } catch {
                console.error(String(data));
            }
        });

        proc.on('error', (err) => {
            console.error(`Failed to start pytest: ${err.message}`);
            reject(err);
        });

        proc.on('close', (code, signal) => {
            console.log(`pytest exited with code ${code}${signal ? `, signal ${signal}` : ''}`);
            resolve(code);
        });
    });
}

module.exports = { runTestCase };
