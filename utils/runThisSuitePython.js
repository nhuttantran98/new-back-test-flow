const readFileSync = require("fs").readFileSync;
const path = require("path");

const { runTestCase } = require("./runTestCase");

const ROOT_DIR = path.dirname(__dirname);

function getAllDefaultTestScripts(test_case_data_json, suite_name) {
    const scripts = [];
    for (const testCaseKey in test_case_data_json[suite_name]) {
        if (testCaseKey.startsWith("Test case ")) {
        const testCase = test_case_data_json[suite_name][testCaseKey];
        if (testCase && testCase["Default Test Script"]) {
            scripts.push(testCase["Default Test Script"]);
        }
        }
    }
    return scripts;
}


async function runThisSuitePython(req, res) {
    const { suiteName } = req.body || {};
    console.log(`Running test suite: ${suiteName}`);
    const testCaseDataJson = JSON.parse(readFileSync(path.join(ROOT_DIR, "outputs", "out.json"), "utf8"));
    const allTestCaseScripts = getAllDefaultTestScripts(testCaseDataJson, suiteName);
    if (allTestCaseScripts.length === 0) {
        res.status(400).json({ success: false, message: `No test cases found for suite: ${suiteName}` });
        return;
    }
    else {
        // for (const testScript of allTestCaseScripts) {
        //     await runTestCase(testScript, res);
        // }
        await runTestCase(allTestCaseScripts, res);
        console.log(`Finished running all test cases for suite: ${suiteName}`);
        res.json({ success: true, message: `All test cases executed for suite: ${suiteName}` });
        return;
    }
}

module.exports = { runThisSuitePython };