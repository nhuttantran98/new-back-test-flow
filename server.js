const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const cors = require('cors');

const convertCSVToJson = require('./utils/convert').convertCSVToJson;
const convertJsonToCSV = require('./utils/convert').convertJsonToCSV;
const uploadEnv = require('./utils/uploadEnv').uploadEnv;
const uploadLogsToJfrog = require('./utils/uploadLogsToJfrog').uploadLogsToJfrog;
const runTestCase = require('./utils/runTestCase').runTestCase;
const runThisSuitePython = require('./utils/runThisSuitePython').runThisSuitePython;
const getJfrogArgsFromRequest = require('./utils/getJfrogArgsFromRequest').getJfrogArgsFromRequest;
const uploadCSVToJazz = require('./utils/uploadCSVToJazz').uploadCSVToJazz;
const gitPullProject = require('./utils/gitPullProject').gitPullProject;

const app = express();
app.use(cors());
const ROOT_DIR = path.dirname(__filename);  
const UPLOAD_DIR = path.join(__dirname, "uploads");
const OUTPUT_DIR = path.join(__dirname, "outputs");
const PROJECT_DIR = path.join(__dirname, "project");
const PYTHON_HELPERS_DIR = path.join(__dirname, "python_helpers");

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

// Run pytest for a given test case name inside project directory
app.post('/run-test-case', (req, res) => {
	const { test_case_name } = req.body.test_case_name || {};
    console.log(`Received request to run test case: ${test_case_name}`);
	if (!test_case_name || typeof test_case_name !== 'string') {
		return res.status(400).json({ error: 'Missing or invalid test_case_name' });
	}
    runTestCase(test_case_name, res);
});

app.post('/convert', upload.single('file'), async (req, res) => {
    try {
        convertCSVToJson(req.file, res);
    } catch (err) {
        console.error("Error converting:", err);
        res.status(500).json({ success: false, message: err.message });
    }
});

app.get('/get-json-data', async (req, res) => {
    const outJSONPath = path.join(OUTPUT_DIR, "out.json");
    if (fs.existsSync(outJSONPath)) {
        res.sendFile(outJSONPath);
    } else {
        res.status(404).json({ error: "out.json not found" });
    }
});

app.post('/pull-project', async (req, res) => {
    try {
        gitPullProject(req, res);

    } catch (err) {
        console.error("GIT PULL ERROR:", err);
        res.status(500).json({ success: false, message: err.message });
    }   
});

app.post('/upload-env', upload.single('file'), (req, res) => {
    try {
        uploadEnv(req, res);
    } catch (err) {
        console.error("UPLOAD ENV ERROR:", err);
        return res.status(500).json({ success: false, message: err.message });
    }
});

app.post('/run-this-suite-python', async (req, res) => {
    runThisSuitePython(req, res);
});

app.post('/upload-logs-to-jfrog', async (req, res) => {
    try {
        const jfrogArguments = getJfrogArgsFromRequest(req, res);
        const allLogFoldersInTestResults = fs.readdirSync(path.join(PROJECT_DIR, "test-results")).filter(f => fs.statSync(path.join(PROJECT_DIR, "test-results", f)).isDirectory());
        let flagUploadSuccess = true;
        for (const folderName of allLogFoldersInTestResults) {
            let args = [folderName, ...jfrogArguments];
            const artifactUrl = await uploadLogsToJfrog(args);
            if(artifactUrl) {
                console.log(`Logs from folder ${folderName} uploaded successfully: ${artifactUrl}`);
            }
            else {
                console.error(`Failed to upload logs from folder ${folderName}`);
                flagUploadSuccess = false;
            }
        }
        if (flagUploadSuccess){
            res.status(200).json({ success: true, message: "All logs uploaded successfully" });
        }
        else {
            res.status(500).json({ success: false, message: "One or more log uploads failed" });
        }

    } catch (err) {
        console.error("UPLOAD LOGS ERROR:", err);
        res.status(500).json({ success: false, message: err.message });
    }
});

app.post('/push-jazz', async (req, res) => {
    try {
        // Update Last Result from out.json to current CSV
        const resultConvert = await convertJsonToCSV();
        if (!resultConvert.ok) {
            throw new Error('Conversion from JSON to CSV failed');
        }

        // Upload updated.CSV to Jazz
        const resultUpload = await uploadCSVToJazz(req, res);

    } catch (err) {
        console.error("PUSH JAZZ ERROR:", err);
        res.status(500).json({ success: false, message: err.message });
    }   
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server listening on port ${PORT}`));

