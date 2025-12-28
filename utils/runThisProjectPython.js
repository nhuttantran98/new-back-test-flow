const path = require("path");
const readFileSync = require("fs").readFileSync;

const { runThisSuitePython } = require("./runThisSuitePython");

const ROOT_DIR = path.dirname(__dirname, "..");

function getAllTestSuiteNames(dataJson) {
    const testSuiteNames = Object.values(dataJson)
        .map(suite => suite["Test suite name"])
        .filter(name => name !== undefined);
    return testSuiteNames;
}

async function runThisProjectPython(req, res) {
    try {   
        const testCaseDataJson = JSON.parse(readFileSync(path.join(ROOT_DIR, "outputs", "out.json"), "utf8"));
        const allTestSuiteNames = getAllTestSuiteNames(testCaseDataJson);
        for (const suiteName of allTestSuiteNames) {
            console.log(`Running test suite for debugg at runThisProjectPython: ${suiteName}`);
            // Just run test suite without response
            const isReturn = false;
            await runThisSuitePython({ body: { suiteName } }, res, isReturn);
        }
        console.log(`Finished running all test suites for project.`);
        res.json({ success: true, message: `All test suites executed for project.` });
        return;
    } catch (error) {
        console.error("Error running project:", error);
        res.status(500).json({ success: false, message: error.message });
        return;
    }

}

module.exports = { runThisProjectPython };
