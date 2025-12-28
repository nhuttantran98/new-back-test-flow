const path = require('path');
const fs = require('fs');
const ROOT_DIR = path.dirname(__dirname, "..");
const OUTPUT_DIR = path.join(ROOT_DIR, "outputs");

function setLogPathForOutJson(logPath, testCaseName) {
    const outJsonPath = path.join(OUTPUT_DIR, 'out.json');
    if (!fs.existsSync(outJsonPath)) {
        console.warn("out.json does not exist at", outJsonPath);
        return;
    }
    const outJsonData = JSON.parse(fs.readFileSync(outJsonPath, 'utf-8'));
    for (const suiteName of Object.keys(outJsonData)) {
            for (const key of Object.keys(outJsonData[suiteName])) {
                if (!key.startsWith("Test case")) continue;
                const tc = outJsonData[suiteName][key];
                if (tc["Name"] != testCaseName) continue;
                tc["Log Path"] = logPath ?? null;
            }
        }
    fs.writeFileSync(outJsonPath, JSON.stringify(outJsonData, null, 2), 'utf-8');
    console.log("Updated log_path in out.json to", logPath);
}
module.exports = { setLogPathForOutJson };