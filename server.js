const express = require('express');
const multer = require('multer');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const runTestCase = require('./utils/runTestCase').runTestCase;

const app = express();

const UPLOAD_DIR = path.join(__dirname, "uploads");
const OUTPUT_DIR = path.join(__dirname, "outputs");

if (!fs.existsSync(UPLOAD_DIR)) fs.mkdirSync(UPLOAD_DIR);
if (!fs.existsSync(OUTPUT_DIR)) fs.mkdirSync(OUTPUT_DIR);

const storage = multer.diskStorage({
    destination: (req, file, cb) => cb(null, UPLOAD_DIR),
    filename: (req, file, cb) => cb(null, file.originalname)
});
const upload = multer({ storage });

app.use(express.json());

// Health check
app.get('/', (req, res) => res.json({ status: 'ok' }));

// Run pytest for a given test case name inside web-sentinel-test
app.post('/run-test-case', (req, res) => {
	const { test_case_name } = req.body || {};
    console.log(`Received request to run test case: ${test_case_name}`);
	if (!test_case_name || typeof test_case_name !== 'string') {
		return res.status(400).json({ error: 'Missing or invalid test_case_name' });
	}
    runTestCase(test_case_name, res);
});

app.post("/convert", upload.single("file"), async (req, res) => {
    try {
        const fileName = req.file.originalname;
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
            output: "/outputs/out.json"
        });

    } catch (err) {
        console.error("Error converting:", err);
        res.status(500).json({ success: false, message: err.message });
    }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server listening on port ${PORT}`));

