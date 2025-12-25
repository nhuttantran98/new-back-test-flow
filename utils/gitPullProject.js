const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const util = require('util');
const execAsync = util.promisify(exec);
const PROJECT_DIR = path.join(__dirname, "..", "project");

async function gitPullProject(req, res) {
    const gitLink = req.body.repoUrl;
    const branchName = req.body.branchName || 'main';
    if (!gitLink) return res.status(400).send('URL Required!');

    if (fs.existsSync(PROJECT_DIR)) {
      fs.rmSync(PROJECT_DIR, { recursive: true, force: true });
    }
    console.log("Cloning repo...");
    // Clone repo (await)
    await execAsync(
      `git clone --branch ${branchName} --single-branch "${gitLink}" "${PROJECT_DIR}"`,
      { timeout: 120000 } // optional timeout
    );

    try {
        const hasPythonPackage =
            fs.existsSync(path.join(PROJECT_DIR, 'setup.py')) ||
            fs.existsSync(path.join(PROJECT_DIR, 'pyproject.toml'));
        console.log(`Python package found: ${hasPythonPackage}`);

        await execAsync('python -m venv .venv', {
            cwd: PROJECT_DIR,
            timeout: 120000,
        });

        await execAsync('. .venv/Scripts/activate', {
            cwd: PROJECT_DIR,
            timeout: 120000,
        });

        await execAsync('python -m pip install -r requirements.txt -c constraints.txt', {
            cwd: PROJECT_DIR,
            timeout: 120000,
        });

        await execAsync('python -m playwright install', {
            cwd: PROJECT_DIR,
            timeout: 120000,
        });

        await execAsync('python -m pip install -e .', {
            cwd: PROJECT_DIR,
            timeout: 120000,
        });

        
    } catch (err) {
        console.error("GIT PULL ERROR:", err);
        res.status(500).json({ success: false, message: err.message });
    }
}

module.exports = { gitPullProject };