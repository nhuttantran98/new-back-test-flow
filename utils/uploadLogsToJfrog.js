const path = require('path');
const { spawn, execSync } = require('child_process');

const ROOT_DIR = path.dirname(__dirname, "..");
const PYTHON_HELPERS_DIR = path.join(ROOT_DIR, "python_helpers");

function uploadLogsToJfrog(jfrogArguments) {
    return new Promise((resolve, reject) => {
        console.log("Uploading logs to JFrog...");
        const jfrogFileBat = process.platform === 'win32'
            ? 'callPythonUpJFrog.bat'
            : 'callPythonUpJFrog.sh';
        const scriptPath = path.join(PYTHON_HELPERS_DIR, jfrogFileBat);
        // Ensure the script is executable and normalized on non-Windows systems
        if (process.platform !== 'win32') {
            try {
                execSync(`dos2unix "${scriptPath}"`);
                console.log("dos2unix applied to", scriptPath);
            } catch (err) {
                // dos2unix may not be installed; it's safe to continue
                console.warn("dos2unix failed or not installed (continuing):", err.message);
            }

            try {
                execSync(`chmod +x "${scriptPath}"`);
                console.log("chmod +x applied to", scriptPath);
            } catch (err) {
                console.warn("chmod failed (continuing):", err.message);
            }
        }
        let proc;
        if (process.platform !== 'win32') {
            proc = spawn(scriptPath, jfrogArguments, { shell: false, stdio: 'inherit', cwd: PYTHON_HELPERS_DIR });
        } else {
            // Need to wrap arguments in quotes for cmd.exe
            const cmd = [
            `"${jfrogArguments[0]}"`,
            `"${jfrogArguments[1]}"`,
            `"${jfrogArguments[2]}"`,
            `"${jfrogArguments[3]}"`
            ];
 
            proc = spawn('cmd.exe', ['/c', scriptPath, ...cmd], {
                cwd: PYTHON_HELPERS_DIR,
                stdio: ['ignore', 'pipe', 'pipe'],
                env: { ...process.env },
                shell: true});
        }

        let stdout = '';
        let stderr = '';

        proc.stdout.on('data', (d) => (stdout += d.toString()));
        proc.stderr.on('data', (d) => (stderr += d.toString()));
        proc.on('error', (err) => {
            reject(null);
        });

        proc.on('close', (code) => {
            console.log(stdout);
            const artifactUrl = getArtifactUrlAfterUpload(stdout);
            if (artifactUrl) {
                console.log("Upload successful!");
                resolve(artifactUrl);
            } else {
                console.error("Upload may have failed. Could not find artifact URL in output.");
                reject(null);
            }
            
        });


    });
}

function getArtifactUrlAfterUpload(stdout) {
    const start = stdout.indexOf("{");
    const end = stdout.lastIndexOf("}");
    if (start !== -1 && end !== -1 && end > start) {
        const jsonText = stdout.substring(start, end + 1);
        try {
            // ✅ Remove ANSI color codes or weird chars
            const cleanJson = jsonText.replace(/\x1b\[[0-9;]*m/g, "");
            const json = JSON.parse(cleanJson);
            return json.artifact_url;
        } catch (err) {
            console.error("❌ JSON parse error (retrying):", err.message);
            return null;
        }
    }
}

module.exports = { uploadLogsToJfrog };