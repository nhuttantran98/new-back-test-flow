const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const ROOT_DIR = path.dirname(__dirname, "..");
const PROJECT_DIR = path.join(ROOT_DIR, 'web-sentinel-test');

function runTestCase (test_case_name, res) {
    return new Promise((resolve, reject) => {
        console.log(`Running test case: ${test_case_name} in ${PROJECT_DIR}`);
        const isWin = process.platform === 'win32';
        const venvWin = path.join(PROJECT_DIR, '.venv','Scripts','python.exe');
        const venvUnix = path.join(PROJECT_DIR, '.venv','bin','python');
        const pythonCmd = fs.existsSync(venvWin) ? venvWin : fs.existsSync(venvUnix) ? venvUnix : 'python';
        const proc = spawn(pythonCmd, ['-m', 'pytest', test_case_name], { cwd: PROJECT_DIR });
        proc.stdout.on('data', (chunk) => {
            try { console.log(chunk.toString()); } catch (e) { console.log(String(chunk)); }
        });
        proc.stderr.on('data', (chunk) => {
            try { console.error(chunk.toString()); } catch (e) { console.error(String(chunk)); }
        });
        proc.on('error', (err) => {
            console.error(`Failed to start pytest: ${err.message}`);
            reject(err);
        });
        proc.on('close', (code) => {
            console.log(`Process exited with code ${code}`);
            resolve(code);
        });
    });
}

module.exports = { runTestCase };