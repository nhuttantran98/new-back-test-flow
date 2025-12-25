const path = require("path");
const fs = require("fs");
const { readFile, utils } = require("xlsx");
const { spawn } = require('child_process');

const ROOT_DIR = path.dirname(__dirname, "..");
const UPLOAD_DIR = path.join(ROOT_DIR, "uploads");
const OUTPUT_DIR = path.join(ROOT_DIR, "outputs");
const PYTHON_HELPERS_DIR = path.join(ROOT_DIR, "python_helpers");



function getNewestCSVFileName(folderPath) {
  try {
    const files = fs.readdirSync(folderPath)
      .filter((file) => file.toLowerCase().endsWith('.csv'))
      .map((file) => ({
        name: file,
        time: fs.statSync(path.join(folderPath, file)).mtime.getTime(),
      }))
      .sort((a, b) => b.time - a.time);

    if (files.length === 0) return null;
    return files[0].name;
  } catch (err) {
    console.error(`getNewestCSVFileName error: ${err.message}`);
    return null;
  }
}



function convertCSVToJson(csvFile, res) {
    const fileName = csvFile.originalname;
    const filePath = path.join(UPLOAD_DIR, fileName);
    // --- 1. Read file Excel ---
    const workbook = readFile(filePath);
    const sheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[sheetName];

    const rows = utils.sheet_to_json(worksheet, { defval: "" });

    // --- 2. Group according to Test suite ---
    const grouped = {};

    rows.forEach((row) => {
        const suiteName = row["Test Suite Execution Records"] || "Unknown Suite";

        if (!grouped[suiteName]) {
            grouped[suiteName] = { "Test suite name": suiteName };
        }

        const caseIndex = Object.keys(grouped[suiteName]).filter(k => k.startsWith("Test case")).length + 1;
        const caseName = `Test case ${caseIndex}`;

        grouped[suiteName][caseName] = row;
    });

    // --- 3. Write to out.json ---
    const outJSONPath = path.join(OUTPUT_DIR, "out.json");
    fs.writeFileSync(outJSONPath, JSON.stringify(grouped, null, 2), "utf8");

    res.json({
        success: true,
        output: path.join(OUTPUT_DIR, "out.json")
    });
}


function convertJsonToCSV() {
    return new Promise((resolve, reject) => {
        try {
            const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
            const scriptPath = path.join(PYTHON_HELPERS_DIR, 'update_last_result_from_json_modified.py');
            const outJSONPath = path.join(OUTPUT_DIR, 'out.json');

            const convertedCSVName = getNewestCSVFileName(UPLOAD_DIR);
            if (!convertedCSVName) {
                return reject(new Error('No CSV file found in upload directory.'));
            }
            const convertedCSVPath = path.join(UPLOAD_DIR, convertedCSVName);

            if (!fs.existsSync(scriptPath)) {
                return reject(new Error(`Python script not found: ${scriptPath}`));
            }
            if (!fs.existsSync(convertedCSVPath)) {
                return reject(new Error(`CSV file not found: ${convertedCSVPath}`));
            }

            const py = spawn(pythonCmd, [scriptPath, convertedCSVPath, outJSONPath], {
                cwd: PYTHON_HELPERS_DIR,        // if your script expects relative paths
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
                reject(err);
            });

            py.on('close', (code) => {
                if (code === 0) {
                    console.log('out.json converted to CSV successfully.');
                    resolve({ ok: true, stdout, outJSONPath, convertedCSVPath });
                } else {
                    const err = new Error(`Conversion failed with exit code ${code}`);
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

module.exports = { convertCSVToJson, convertJsonToCSV, getNewestCSVFileName };