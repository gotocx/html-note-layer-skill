#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { spawn } = require("node:child_process");

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function parseArgs(argv) {
  const args = { html: "", edge: "" };
  for (let index = 2; index < argv.length; index += 1) {
    const item = argv[index];
    if (item === "--edge") {
      args.edge = argv[index + 1] || "";
      index += 1;
    } else if (!args.html) {
      args.html = item;
    }
  }
  return args;
}

function findEdge(explicit) {
  const candidates = [
    explicit,
    process.env.EDGE_PATH,
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "microsoft-edge",
    "msedge",
  ].filter(Boolean);
  for (const candidate of candidates) {
    if (candidate.includes(path.sep) || candidate.includes(":")) {
      if (fs.existsSync(candidate)) return candidate;
    } else {
      return candidate;
    }
  }
  throw new Error("Microsoft Edge executable was not found. Pass --edge <path>.");
}

function makeSampleHtml() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "hnl-sample-"));
  const html = path.join(dir, "sample.html");
  fs.writeFileSync(html, `<!doctype html>
<html>
<head><meta charset="utf-8"><title>HTML Note Layer Smoke</title></head>
<body>
  <main>
    <h1>Smoke page</h1>
    <p id="target">Selected text should open a note editor without changing this paragraph.</p>
    <section><p>Double click here to create a free anchor note.</p></section>
  </main>
</body>
</html>`, "utf-8");
  return { html, dir };
}

async function waitForPage(port, targetUrl) {
  for (let index = 0; index < 80; index += 1) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/json`);
      const tabs = await response.json();
      const page = tabs.find((tab) => tab.type === "page" && (tab.url === targetUrl || tab.url.startsWith("file:///")));
      if (page) return page;
    } catch {
      // Browser is still starting.
    }
    await sleep(200);
  }
  throw new Error("Browser debugging endpoint did not expose the note-layer page.");
}

function connect(wsUrl) {
  return new Promise((resolve, reject) => {
    if (typeof WebSocket === "undefined") {
      reject(new Error("This smoke script requires a Node.js runtime with global WebSocket support."));
      return;
    }
    const ws = new WebSocket(wsUrl);
    const pending = new Map();
    let seq = 0;
    ws.addEventListener("open", () => {
      resolve({
        send(method, params = {}) {
          const id = ++seq;
          ws.send(JSON.stringify({ id, method, params }));
          return new Promise((res, rej) => pending.set(id, { res, rej, method }));
        },
        close() {
          ws.close();
        },
      });
    });
    ws.addEventListener("message", (event) => {
      const message = JSON.parse(event.data);
      if (!message.id || !pending.has(message.id)) return;
      const item = pending.get(message.id);
      pending.delete(message.id);
      if (message.error) item.rej(new Error(`${item.method}: ${message.error.message}`));
      else item.res(message.result);
    });
    ws.addEventListener("error", reject);
  });
}

async function evaluate(cdp, fn) {
  const result = await cdp.send("Runtime.evaluate", {
    expression: `(${fn.toString()})()`,
    awaitPromise: true,
    returnByValue: true,
  });
  if (result.exceptionDetails) {
    const details = result.exceptionDetails;
    const message = details.exception?.description || details.text || "Page evaluation failed.";
    throw new Error(message);
  }
  return result.result.value;
}

async function waitForReady(cdp) {
  for (let index = 0; index < 50; index += 1) {
    const ready = await evaluate(cdp, () => document.readyState);
    if (ready === "complete" || ready === "interactive") return;
    await sleep(120);
  }
}

function pageSmoke() {
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  function shadow() {
    return document.querySelector("html-note-layer")?.shadowRoot;
  }
  function firstTextNode(el) {
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    let node = walker.nextNode();
    while (node) {
      if ((node.textContent || "").replace(/\s+/g, " ").trim().length >= 16) return node;
      node = walker.nextNode();
    }
    return null;
  }
  function findTextTarget() {
    const candidates = Array.from(document.querySelectorAll("p, li, td, th, h1, h2, h3, pre, code, article, section, div"))
      .filter((el) => !el.closest("html-note-layer") && firstTextNode(el));
    return candidates.find((el) => {
      const rect = el.getBoundingClientRect();
      return rect.width > 20 && rect.height > 10;
    }) || document.body;
  }
  function fireMouse(type, el, detail = 1) {
    const rect = el.getBoundingClientRect();
    el.dispatchEvent(new MouseEvent(type, {
      bubbles: true,
      cancelable: true,
      view: window,
      clientX: rect.left + Math.min(60, Math.max(10, rect.width / 2)),
      clientY: rect.top + Math.min(24, Math.max(10, rect.height / 2)),
      detail,
    }));
  }
  return (async () => {
    localStorage.clear();
    const summary = {};
    const target = document.querySelector("#target") || findTextTarget();
    const root = shadow();
    summary.hasLayer = Boolean(root);
    summary.originalTextBefore = target.textContent;

    const textNode = firstTextNode(target);
    if (!textNode) throw new Error("No selectable text node found for smoke test.");
    const range = document.createRange();
    range.setStart(textNode, 0);
    range.setEnd(textNode, Math.min(13, textNode.length));
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
    fireMouse("mouseup", target, 1);
    await sleep(420);
    summary.selectionEditors = root.querySelectorAll(".hnl-editor").length;
    summary.selectionCopyButton = Boolean(root.querySelector(".hnl-copy-quote"));
    root.querySelector(".hnl-copy-quote")?.click();
    const editorText = root.querySelector(".hnl-editor textarea");
    if (editorText) {
      editorText.value = "selection note";
      editorText.dispatchEvent(new Event("input", { bubbles: true }));
    }
    document.body.click();
    await sleep(220);
    summary.savedSelectionNotes = root.querySelectorAll(".hnl-note").length;
    sel.removeAllRanges();

    const freeTarget = Array.from(document.querySelectorAll("section p, p, li, td, div")).find((el) => el !== target && firstTextNode(el)) || target;
    fireMouse("dblclick", freeTarget, 2);
    await sleep(200);
    const freeInput = root.querySelector(".hnl-editor textarea");
    summary.doubleClickEditor = Boolean(freeInput);
    if (freeInput) {
      freeInput.value = "free note";
      freeInput.dispatchEvent(new Event("input", { bubbles: true }));
    }
    document.body.click();
    await sleep(220);
    summary.savedAfterDoubleClick = root.querySelectorAll(".hnl-note").length;

    const noteForEdit = root.querySelector(".hnl-note");
    if (noteForEdit) {
      const editId = noteForEdit.dataset.noteId;
      const rect = noteForEdit.getBoundingClientRect();
      noteForEdit.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true, cancelable: true, pointerId: 2, clientX: rect.left + 8, clientY: rect.top + 8 }));
      noteForEdit.dispatchEvent(new PointerEvent("pointerup", { bubbles: true, cancelable: true, pointerId: 2, clientX: rect.left + 8, clientY: rect.top + 8 }));
      await sleep(220);
      const editBox = root.querySelector(".hnl-editor");
      const editInput = editBox?.querySelector("textarea");
      const editRect = editBox?.getBoundingClientRect();
      summary.clickEditEditor = Boolean(editInput);
      summary.activeNoteHiddenWhileEditing = !root.querySelector(`.hnl-note[data-note-id="${editId}"]`);
      summary.editorWithinViewport = Boolean(editRect && editRect.left >= 0 && editRect.top >= 0 && editRect.right <= window.innerWidth && editRect.bottom <= window.innerHeight);
      summary.editorCompact = Boolean(editRect && editRect.width <= 430 && editRect.height <= 170);
      if (editInput) {
        editInput.value = "selection note edited";
        editInput.dispatchEvent(new Event("input", { bubbles: true }));
      }
      document.body.click();
      await sleep(220);
      summary.savedAfterEdit = root.querySelectorAll(".hnl-note").length;
    }

    const note = root.querySelector(".hnl-note");
    if (note) {
      const rect = note.getBoundingClientRect();
      note.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true, cancelable: true, pointerId: 1, clientX: rect.left + 8, clientY: rect.top + 8 }));
      note.dispatchEvent(new PointerEvent("pointermove", { bubbles: true, cancelable: true, pointerId: 1, clientX: rect.left + 44, clientY: rect.top + 24 }));
      note.dispatchEvent(new PointerEvent("pointerup", { bubbles: true, cancelable: true, pointerId: 1, clientX: rect.left + 44, clientY: rect.top + 24 }));
    }
    await sleep(220);
    const key = Object.keys(localStorage).find((item) => item.startsWith("html-note-layer:v1:"));
    const stored = key ? localStorage.getItem(key) || "" : "";
    summary.dragPersisted = stored.includes("\"dx\"") && stored.includes("\"dy\"");
    const fabRect = root.querySelector(".hnl-fab")?.getBoundingClientRect();
    summary.fabSizeOk = Boolean(fabRect && fabRect.width >= 52 && fabRect.height >= 52);

    const scroller = document.scrollingElement || document.documentElement;
    const originalScrollTop = scroller.scrollTop;
    if (scroller.scrollHeight > window.innerHeight + 320) {
      window.scrollTo(0, scroller.scrollHeight);
      await sleep(320);
      const stackedAtTop = Array.from(root.querySelectorAll(".hnl-note")).filter((el) => {
        const rect = el.getBoundingClientRect();
        return rect.top <= 12 && rect.bottom > 0;
      });
      summary.offscreenNotesDoNotStackAtTop = stackedAtTop.length === 0;
      window.scrollTo(0, originalScrollTop);
      await sleep(320);
    }

    root.querySelector(".hnl-fab")?.click();
    await sleep(120);
    summary.panelOpen = !root.querySelector(".hnl-panel")?.hidden;
    summary.panelItems = root.querySelectorAll(".hnl-item").length;
    summary.exportText = root.querySelector(".hnl-export")?.value || "";
    root.querySelector(".hnl-copy-all")?.click();
    summary.originalTextAfter = target.textContent;
    summary.originalUnchanged = summary.originalTextBefore === summary.originalTextAfter;
    return summary;
  })();
}

function reloadCheck() {
  const root = document.querySelector("html-note-layer")?.shadowRoot;
  const exportText = root?.querySelector(".hnl-export")?.value || "";
  return {
    savedAfterReload: root?.querySelectorAll(".hnl-note").length || 0,
    countText: root?.querySelector(".hnl-count")?.textContent || "",
    exportText,
  };
}

function assertSmoke(summary, reloadSummary) {
  const failures = [];
  if (!summary.hasLayer) failures.push("note layer shadow root missing");
  if (summary.selectionEditors !== 1 || !summary.selectionCopyButton) failures.push("text selection did not create editor with copy button");
  if (summary.savedSelectionNotes < 1) failures.push("selection note was not saved");
  if (!summary.doubleClickEditor || summary.savedAfterDoubleClick < 2) failures.push("double-click free note was not saved");
  if (!summary.clickEditEditor) failures.push("saved note did not open an editor when activated");
  if (!summary.activeNoteHiddenWhileEditing) failures.push("saved note chip remained visible while its editor was active");
  if (!summary.editorWithinViewport || !summary.editorCompact) failures.push("note editor is not compact or within the viewport");
  if (summary.savedAfterEdit < 2) failures.push("edited note was not saved");
  if (!summary.dragPersisted) failures.push("drag offset was not persisted");
  if (!summary.fabSizeOk) failures.push("floating notes button was squeezed below usable size");
  if (summary.offscreenNotesDoNotStackAtTop === false) failures.push("offscreen notes stacked at the top during scroll");
  if (!summary.panelOpen || summary.panelItems < 2) failures.push("floating notes panel did not show all notes");
  if (!summary.exportText.includes("selection note edited") || !summary.exportText.includes("free note")) failures.push("export text missing notes");
  if (!summary.originalUnchanged) failures.push("original page text was modified");
  if (reloadSummary.savedAfterReload < 2 || reloadSummary.countText !== "2") failures.push("notes did not survive reload");
  if (failures.length) {
    throw new Error("NOTE_LAYER_SMOKE_FAILED\n" + failures.join("\n") + "\nSUMMARY\n" + JSON.stringify({ summary, reloadSummary }, null, 2));
  }
}

async function main() {
  const args = parseArgs(process.argv);
  let sample = null;
  const reportPath = args.html ? path.resolve(args.html) : (sample = makeSampleHtml()).html;
  if (!fs.existsSync(reportPath)) throw new Error(`HTML does not exist: ${reportPath}`);
  const edge = findEdge(args.edge);
  const port = 9500 + Math.floor(Math.random() * 400);
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), "hnl-browser-"));
  const url = pathToFileURL(reportPath).href;
  const proc = spawn(edge, [
    "--headless=new",
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${profile}`,
    "--disable-gpu",
    "--no-first-run",
    url,
  ], { stdio: "ignore", windowsHide: true });

  try {
    const page = await waitForPage(port, url);
    const cdp = await connect(page.webSocketDebuggerUrl);
    await cdp.send("Runtime.enable");
    await cdp.send("Page.enable");
    await waitForReady(cdp);
    const summary = await evaluate(cdp, pageSmoke);
    await cdp.send("Page.reload", { ignoreCache: true });
    await sleep(1000);
    await waitForReady(cdp);
    const reloadSummary = await evaluate(cdp, reloadCheck);
    assertSmoke(summary, reloadSummary);
    console.log(JSON.stringify({ summary, reloadSummary }, null, 2));
    console.log("NOTE_LAYER_SMOKE_OK");
    cdp.close();
  } finally {
    proc.kill();
    await sleep(400);
    try { fs.rmSync(profile, { recursive: true, force: true }); } catch {}
    if (sample) {
      try { fs.rmSync(sample.dir, { recursive: true, force: true }); } catch {}
    }
  }
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
