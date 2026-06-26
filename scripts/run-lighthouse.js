const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const outputPath = path.join("tmp", "lighthouse-flora.json");
fs.mkdirSync(path.dirname(outputPath), { recursive: true });

const npx = process.platform === "win32" ? "npx.cmd" : "npx";
const result = spawnSync(
  npx,
  [
    "--yes",
    "lighthouse",
    "http://127.0.0.1:5000/",
    "--only-categories=accessibility,best-practices",
    "--output=json",
    `--output-path=${outputPath}`,
  ],
  { encoding: "utf8" },
);

if (!fs.existsSync(outputPath)) {
  process.stdout.write(result.stdout || "");
  process.stderr.write(result.stderr || "");
  process.exit(result.status || 1);
}

const report = JSON.parse(fs.readFileSync(outputPath, "utf8"));
if (report.runtimeError) {
  console.error(report.runtimeError.message || report.runtimeError.code);
  process.exit(1);
}

const accessibility = report.categories.accessibility.score;
const bestPractices = report.categories["best-practices"].score;
console.log(`Lighthouse accessibility: ${Math.round(accessibility * 100)}`);
console.log(`Lighthouse best-practices: ${Math.round(bestPractices * 100)}`);

if (accessibility < 0.9 || bestPractices < 0.9) {
  process.stdout.write(result.stdout || "");
  process.stderr.write(result.stderr || "");
  process.exit(1);
}

if (result.status !== 0) {
  console.warn("Lighthouse generated a valid report; ignored Windows temp cleanup warning.");
}
