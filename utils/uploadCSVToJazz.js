const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

const getNewestCSVFileName = require('./convert').getNewestCSVFileName;

const ROOT_DIR = path.dirname(__dirname, "..");
const UPLOAD_DIR = path.join(ROOT_DIR, "uploads");
const PYTHON_HELPERS_DIR = path.join(ROOT_DIR, "python_helpers");

function uploadCSVToJazz(req, res) {
    return new Promise((resolve, reject) => {
        try {
            const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
            const pushJazzScriptPath = path.join(PYTHON_HELPERS_DIR, 'updateTCR.py');
            const { ['username']: userName, ['password']: password, ['project-name']: projectJazzName } = req.body || {};

            if (!userName || !password || !projectJazzName) {
                return reject(new Error('Missing required fields: username, password, project-name'));
            }

            // Find newest CSV
            const updatedCSVFileName = getNewestCSVFileName(UPLOAD_DIR);
            if (!updatedCSVFileName) {
                return reject(new Error(`No CSV file found in upload directory: ${UPLOAD_DIR}`));
            }

            const updatedCSVPath = path.join(UPLOAD_DIR, updatedCSVFileName);

            // Sanity checks
            if (!fs.existsSync(pushJazzScriptPath)) {
                return reject(new Error(`Python script not found: ${pushJazzScriptPath}`));
            }
            if (!fs.existsSync(updatedCSVPath)) {
                return reject(new Error(`CSV file not found: ${updatedCSVPath}`));
            }

            // Build args for Python script
            const args = [
                pushJazzScriptPath,
                '-u', userName,
                '-p', password,
                '-a', projectJazzName,
                '-f', updatedCSVPath, 
                '-q', 'True'
            ];

            const py = spawn(pythonCmd, args, {
                cwd: PYTHON_HELPERS_DIR,           
                stdio: ['ignore', 'pipe', 'pipe'],
                env: { ...process.env }
            });

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

            py.on('error', (err) => {
                // failed to start process
                reject(err);
            });

            py.on('close', (code) => {
                if (code === 0) {
                    resolve({ ok: true, stdout, csvPath: updatedCSVPath });
                } else {
                    const err = new Error(`Jazz upload failed with exit code ${code}`);
                    err.stdout = stdout;
                    err.stderr = stderr;
                    reject(err);
                }
            });
        } catch (err) {
            reject(err);
        }
  });
}


module.exports = { uploadCSVToJazz };