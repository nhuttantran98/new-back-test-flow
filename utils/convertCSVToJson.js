const path = require("path");
const fs = require("fs");
const { readFile, utils } = require("xlsx");


const rootDir = path.dirname(__dirname);
const UPLOAD_DIR = path.join(rootDir, "uploads");
const OUTPUT_DIR = path.join(rootDir, "outputs");

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

module.exports = { convertCSVToJson };