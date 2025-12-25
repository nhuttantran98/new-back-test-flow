const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const util = require('util');
const execAsync = util.promisify(exec);

const ROOT_DIR = path.join(__dirname, "..");
const PROJECT_DIR = path.join(__dirname, "..", "project");

function getVenvPythonPath () {
    return process.platform === 'win32'
        ? path.join(ROOT_DIR, '.venv', 'Scripts', 'python.exe')
        : path.join(ROOT_DIR, '.venv', 'bin', 'python');
}

async function createVenvFolder () {
    await execAsync('python -m venv .venv', {
        cwd: ROOT_DIR,
        timeout: 120000,
    });
}


async function runInVenv(args, options = {}) {
    const python = getVenvPythonPath();
    const cmd = `"${python}" ${args}`;
    const execOpts = {
        cwd: options.cwd || ROOT_DIR,
        timeout: options.timeout || 120000,
    };
    return execAsync(cmd, execOpts);
}



async function installProjectDeps() {
    console.log("Create venv folder")
    await createVenvFolder();

    console.log("Install Python packages, it will take a while ...");
    await runInVenv('-m pip install --upgrade pip', { cwd: PROJECT_DIR });
    await runInVenv('-m pip install -r requirements.txt -c constraints.txt', { cwd: PROJECT_DIR, timeout: 120000*10 });
    await runInVenv('-m playwright install', { cwd: PROJECT_DIR });
    // If the repo is a Python package (editable install)
    await runInVenv('-m pip install -e .', { cwd: PROJECT_DIR });

    console.log("Install packages done");
}


async function gitPullProject(req, res) {
    const gitLink = req.body.repoUrl;
    const branchName = req.body.branchName || 'main';
    if (!gitLink) return res.status(400).send('URL Required!');
    if (fs.existsSync(PROJECT_DIR)) {
      fs.rmSync(PROJECT_DIR, { recursive: true, force: true });
    }
    console.log("Cloning repository ...");
    // Clone repo (await)
    await execAsync(
      `git clone --branch ${branchName} --single-branch "${gitLink}" "${PROJECT_DIR}"`,
      { timeout: 120000 }
    );

    try {
        const hasPythonPackage =
            fs.existsSync(path.join(PROJECT_DIR, 'setup.py')) ||
            fs.existsSync(path.join(PROJECT_DIR, 'pyproject.toml'));

        if(hasPythonPackage) {
            console.log("Python project cloned sucessfully. Start installing project ...");
            await installProjectDeps();
        }
        
    } catch (err) {
        console.error("GIT PULL ERROR:", err);
        res.status(500).json({ success: false, message: err.message });
    }
}

module.exports = { gitPullProject };