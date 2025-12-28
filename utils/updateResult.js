const path = require('path');
const fs = require('fs');

const ROOT_DIR = path.dirname(__dirname, "..");
const PROJECT_DIR = path.join(ROOT_DIR, "project");
const OUTPUT_DIR = path.join(ROOT_DIR, "outputs");
const outJsonPath = path.join(OUTPUT_DIR, "out.json");
const outJson = JSON.parse(fs.readFileSync(outJsonPath, 'utf-8')); //out.json data

function waitForFile(path, timeout = 60000*3) {
    console.log("Waiting for file:", path);
    return new Promise((resolve, reject) => {
        const start = Date.now();
        const timer = setInterval(() => {
            if (fs.existsSync(path)) {
                clearInterval(timer);
                resolve(true);
            }
            if (Date.now() - start > timeout) {
                clearInterval(timer);
                reject(new Error(`Timeout waiting for file: ${path}`));
            }
        }, 500);
    });
}

function extractTestResults (jsonData) {
    const results = [];
    const [key, arr] = Object.entries(jsonData)[0];
    for (const testCase of arr) {
        const title = testCase.jazz_id;
        const status = testCase.outcome;
        results.push({ title, status });
    }
    return results;
}

function cleanFolderName(folderName) {
    const symbols = ["["];
    const indexes = symbols
        .map(sym => folderName.lastIndexOf(sym))
        .filter(i => i !== -1);
    if (indexes.length === 0) return folderName;
    const cutIndex = Math.min(...indexes);
    return folderName.substring(0, cutIndex).trim();
}

function resetAllNeedUploadFlags(outJson) {
    const outJsonPath = path.join(OUTPUT_DIR, "out.json");
    for (const suiteName of Object.keys(outJson)) {
        for (const key of Object.keys(outJson[suiteName])) {
            if (!key.startsWith("Test case ")) continue;
            const testCase = outJson[suiteName][key];
            if( testCase["Need Upload"] === undefined ) continue;
            testCase["Need Upload"] = "False";
        }
    }
    fs.writeFileSync(outJsonPath, JSON.stringify(outJson, null, 2));
}

async function updateResult(req, res) {
    const testResultJsonPath = path.join(PROJECT_DIR, "test-results", "test-results.json");
    const outJsonPath = path.join(OUTPUT_DIR, "out.json");
    console.log("Updating test results from", testResultJsonPath, "to", outJsonPath);
    const fileExists = await waitForFile(testResultJsonPath);
    if (fileExists) {
        const testResultJson = JSON.parse(fs.readFileSync(testResultJsonPath, 'utf-8')); //test_results.json data
        const outJson = JSON.parse(fs.readFileSync(outJsonPath, 'utf-8')); //out.json data
        const testResults = extractTestResults(testResultJson);
        const logFolders = fs
            .readdirSync(path.join(PROJECT_DIR, "test-results"), { withFileTypes: true })
            .filter(dir => dir.isDirectory())
            .map(dir => ({
                raw: dir.name,
                cleanName: cleanFolderName(dir.name)
            }))

        resetAllNeedUploadFlags(outJson);

        for (const { title, status } of testResults) {
            for (const suiteName of Object.keys(outJson)) {
                for (const key of Object.keys(outJson[suiteName])) {
                    if (!key.startsWith("Test case ")) continue;
                    const testCase = outJson[suiteName][key];
                    if (testCase["Name"] !== title) continue;
                    testCase["Last Result"] = status;
                    testCase["Need Upload"] = "True";
                    testCase["Log Path"] = null;
                    const matched = logFolders.find(folder => folder.cleanName == testCase["Name"]);
                    if (matched) {
                        testCase["Folder Raw"] = matched?.raw || null;
                        testCase["Folder Clean"] = matched?.cleanName || null;
                    }
                }
            }
        }
        fs.writeFileSync(outJsonPath, JSON.stringify(outJson, null, 2));
        res.status(200).json({ success: true, message: "Test results updated successfully" });
        return true;
    } else {
        res.status(500).json({ success: false, message: `Test result file not found: ${testResultJsonPath}` });
        throw new Error(`Test result file not found: ${testResultJsonPath}`);
    }

}

module.exports = { updateResult };