const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const routes = [
  { label: "home", url: "http://127.0.0.1:5000/" },
  { label: "rekomendasi", url: "http://127.0.0.1:5000/rekomendasi" },
  { label: "tentang", url: "http://127.0.0.1:5000/tentang" },
];
const thresholds = {
  performance: 0.8,
  accessibility: 0.9,
  "best-practices": 0.9,
};
const maxAttempts = 2;

fs.mkdirSync("tmp", { recursive: true });

function runLighthouse(route, outputPath) {
  const args = [
    "--yes",
    "lighthouse",
    route.url,
    "--only-categories=performance,accessibility,best-practices",
    "--chrome-flags=--headless=new",
    "--output=json",
    `--output-path=${outputPath}`,
  ];

  if (process.platform === "win32") {
    return spawnSync("cmd.exe", ["/d", "/s", "/c", `npx ${args.join(" ")}`], { encoding: "utf8" });
  }

  return spawnSync("npx", args, { encoding: "utf8" });
}

for (const route of routes) {
  const outputPath = path.join("tmp", `lighthouse-flora-${route.label}.json`);
  let report = null;
  let result = null;

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    if (fs.existsSync(outputPath)) fs.unlinkSync(outputPath);
    result = runLighthouse(route, outputPath);

    if (result.error) {
      if (attempt < maxAttempts) {
        console.warn(`Retrying Lighthouse ${route.label}: ${result.error.message}`);
        continue;
      }

      console.error(result.error.message);
      process.exit(1);
    }

    if (!fs.existsSync(outputPath)) {
      if (attempt < maxAttempts) {
        console.warn(`Retrying Lighthouse ${route.label}: report was not generated.`);
        continue;
      }

      process.stdout.write(result.stdout || "");
      process.stderr.write(result.stderr || "");
      process.exit(result.status || 1);
    }

    report = JSON.parse(fs.readFileSync(outputPath, "utf8"));
    if (!report.runtimeError) break;

    if (attempt < maxAttempts) {
      console.warn(`Retrying Lighthouse ${route.label}: ${report.runtimeError.message || report.runtimeError.code}`);
      report = null;
      continue;
    }

    console.error(`${route.label}: ${report.runtimeError.message || report.runtimeError.code}`);
    process.exit(1);
  }

  for (const [category, threshold] of Object.entries(thresholds)) {
    const score = report.categories[category].score;
    console.log(`Lighthouse ${route.label} ${category}: ${Math.round(score * 100)}`);

    if (score < threshold) {
      process.stdout.write(result.stdout || "");
      process.stderr.write(result.stderr || "");
      process.exit(1);
    }
  }

  if (result.status !== 0) {
    console.warn(`Lighthouse generated a valid ${route.label} report; ignored Windows temp cleanup warning.`);
  }
}
