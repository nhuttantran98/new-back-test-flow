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


async function isPlaywrightInstalled () {
    const python = getVenvPythonPath();
    if (!python) return false;

    try {
        const { stdout } = await execAsync(`"${python}" -m playwright --version`, {
            cwd: ROOT_DIR,
        });
        console.log("Playwright version:", stdout.trim());
        return true;
    } catch (err) {
        return false;
    }
}

async function installProjectDeps() {
    try {
        const isNeedInstallPackage = await isPlaywrightInstalled();
        if (!isNeedInstallPackage) {
            console.log("Create venv folder")
            await createVenvFolder();
            console.log("Install Python packages, it will take a while ...");
            await runInVenv('-m pip install --upgrade pip', { cwd: PROJECT_DIR });
            await runInVenv('-m pip install -r requirements.txt -c constraints.txt', { cwd: PROJECT_DIR, timeout: 120000*10 });
            await runInVenv('-m playwright install', { cwd: PROJECT_DIR });
            // If the repo is a Python package (editable install)
            await runInVenv('-m pip install -e .', { cwd: PROJECT_DIR });
            console.log("Install packages done");
            return true;
        } else {
            console.log("Install packages done");
            return true;
        }
    } catch (err) {
        console.log("Install Python package failed.")
        console.log(err);
        return false;
    }
}


async function gitPullProject(req, res) {
    const isRemoveOldProject = req.body.removeOldProject || false;
    const gitLink = req.body.repoUrl;
    const branchName = req.body.branchName || 'main';
    if (!gitLink) return res.status(400).send('URL Required!');
    if (isRemoveOldProject && fs.existsSync(PROJECT_DIR)) {
        console.log("Removing old project folder ...");
        fs.rmSync(PROJECT_DIR, { recursive: true, force: true });
        console.log("Cloning repository ...");
        // Clone repo (await)
        await execAsync(
        `git clone --branch ${branchName} --single-branch "${gitLink}" "${PROJECT_DIR}"`,
        { timeout: 120000 }
        );
    }


    try {
        const hasPythonPackage =
            fs.existsSync(path.join(PROJECT_DIR, 'setup.py')) ||
            fs.existsSync(path.join(PROJECT_DIR, 'pyproject.toml'));

        if(hasPythonPackage) {
            console.log("Python project cloned sucessfully. Start installing project ...");
            const resultInstallPackage = await installProjectDeps();
            if (resultInstallPackage) {
                res.status(200).json({ success: true, message: "Install Python package done."})
            }
        }
        
    } catch (err) {
        console.error("GIT PULL ERROR:", err);
        res.status(500).json({ success: false, message: err.message });
    }
}

module.exports = { gitPullProject };