const fs = require("fs");
const path = require("path");

const ROOT_DIR = path.join(__dirname, "..");
const PROJECT_DIR = path.join(ROOT_DIR, "project");
const UPLOAD_DIR = path.join(ROOT_DIR, "uploads");

function uploadEnv(req, res){
    if (!req.file) {
        return res.status(400).json({ success: false, message: "No file uploaded" });
    }

    const sourcePath = path.join(UPLOAD_DIR, req.file.originalname);
    const destPath = path.join(PROJECT_DIR, ".env");

    // Copy file to PROJECT_DIR
    fs.copyFileSync(sourcePath, destPath);

    // Set secure permissions
    fs.chmodSync(destPath, 0o600);

    // Remove temp file
    fs.unlinkSync(sourcePath);
    console.log("Env created at ", destPath);
    return res.json({ success: true, path: destPath });
}

module.exports = { uploadEnv };