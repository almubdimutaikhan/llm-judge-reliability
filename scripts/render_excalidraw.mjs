#!/usr/bin/env node
import { build } from "esbuild";
import { chromium } from "playwright";
import { createServer } from "node:http";
import { readFile, writeFile, mkdir, access } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const tmp = path.join(root, "tmp");
await mkdir(tmp, { recursive: true });
await build({
  entryPoints: [path.join(root, "scripts/excalidraw_browser.js")],
  outfile: path.join(tmp, "excalidraw-bundle.js"), bundle: true, format: "iife",
  platform: "browser", target: "es2022", define: { "process.env.NODE_ENV": '"production"' },
  logLevel: "warning",
});
const assets = path.join(root, "node_modules/@excalidraw/excalidraw/dist/prod");
const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url, "http://localhost");
    if (url.pathname === "/") {
      res.setHeader("Content-Type", "text/html");
      res.end('<!doctype html><html><body><script>window.EXCALIDRAW_ASSET_PATH="/assets/";</script><script src="/bundle.js"></script></body></html>');
      return;
    }
    const file = url.pathname === "/bundle.js" ? path.join(tmp, "excalidraw-bundle.js") :
      url.pathname.startsWith("/assets/") ? path.resolve(assets, "." + url.pathname.slice(7)) : null;
    if (!file || (file !== path.join(tmp, "excalidraw-bundle.js") && !file.startsWith(assets + path.sep))) {
      res.writeHead(404); res.end(); return;
    }
    res.setHeader("Content-Type", file.endsWith(".woff2") ? "font/woff2" : file.endsWith(".wasm") ? "application/wasm" : "text/javascript");
    res.end(await readFile(file));
  } catch {
    res.writeHead(404); res.end();
  }
});
await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
const address = `http://127.0.0.1:${server.address().port}`;
const options = { headless: true };
const localChrome = process.env.EXCALIDRAW_CHROME ||
  (process.platform === "darwin" ? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" : null);
if (localChrome) {
  try { await access(localChrome); options.executablePath = localChrome; } catch { /* use installed Playwright Chromium */ }
}
let browser;
try {
  browser = await chromium.launch(options);
  const page = await browser.newPage();
  page.on("pageerror", error => process.stderr.write(`Browser: ${error.message}\n`));
  await page.route("**/*", route => route.request().url().startsWith(address) ? route.continue() : route.abort());
  await page.goto(address);
  await page.waitForFunction(() => typeof window.renderResearchFigure === "function", { timeout: 30000 });
  const scenes = JSON.parse(await readFile(path.join(tmp, "excalidraw-specs.json"), "utf8"));
  const validation = [];
  for (const spec of scenes) {
    const result = await page.evaluate(spec => window.renderResearchFigure(spec), spec);
    if (result.outside.length) throw new Error(`Text outside ${spec.name}: ${JSON.stringify(result.outside)}`);
    const base = path.join(root, "figures", spec.name);
    await writeFile(base + ".excalidraw", result.scene);
    await writeFile(base + ".svg", result.svg + "\n");
    await writeFile(base + ".png", Buffer.from(result.png, "base64"));
    const scene = JSON.parse(result.scene);
    validation.push({ name: spec.name, elements: scene.elements.length,
      text: scene.elements.filter(el => el.type === "text").length,
      allNative: scene.elements.every(el => ["text", "rectangle", "ellipse", "line", "arrow"].includes(el.type)),
      embeddedImages: Object.keys(scene.files).length });
    process.stdout.write(`${spec.name}: ${scene.elements.length} editable elements\n`);
  }
  await writeFile(path.join(tmp, "excalidraw-validation.json"), JSON.stringify(validation, null, 2) + "\n");
} finally {
  if (browser) await browser.close();
  await new Promise(resolve => server.close(resolve));
}
