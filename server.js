const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');

const runTestCase = require('./utils/runTestCase').runTestCase;
const convertCSVToJson = require('./utils/convertCSVToJson').convertCSVToJson;
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
        convertCSVToJson(req.file, res);
    } catch (err) {
        console.error("Error converting:", err);
        res.status(500).json({ success: false, message: err.message });
    }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server listening on port ${PORT}`));

