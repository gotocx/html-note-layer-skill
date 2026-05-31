#!/usr/bin/env python3
"""Inject a self-contained local note layer into an existing HTML file."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


START = "<!-- html-note-layer:start -->"
END = "<!-- html-note-layer:end -->"


RUNTIME = r"""
<!-- html-note-layer:start -->
<script data-html-note-layer="1">
(() => {
  "use strict";
  if (window.__HTML_NOTE_LAYER_ACTIVE__) return;
  window.__HTML_NOTE_LAYER_ACTIVE__ = true;

  const runtimeId = "html-note-layer";
  const oldRoot = document.querySelector(runtimeId);
  if (oldRoot) oldRoot.remove();

  const host = document.createElement(runtimeId);
  host.setAttribute("data-html-note-layer", "");
  document.documentElement.appendChild(host);
  const root = host.attachShadow ? host.attachShadow({ mode: "open" }) : host;
  const supportsPointer = "PointerEvent" in window;
  const noteIgnoreSelector = "html-note-layer, button, input, textarea, select, option, summary, a, [contenteditable='true'], [data-html-note-ignore]";
  const storageKey = "html-note-layer:v1:" + location.pathname + ":" + document.title;
  const nowIso = () => new Date().toISOString();
  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
  const escapeCss = (value) => window.CSS?.escape ? CSS.escape(value) : String(value).replace(/["\\#.:,[\]>+~*^$|=]/g, "\\$&");

  root.innerHTML = `
    <style>
      :host, html-note-layer { all: initial; }
      .hnl-layer {
        position: fixed;
        inset: 0;
        z-index: 2147483600;
        pointer-events: none;
        font-family: ui-sans-serif, "Segoe UI", "Microsoft YaHei", sans-serif;
        color: #172125;
      }
      .hnl-tethers {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        overflow: visible;
        pointer-events: none;
      }
      .hnl-tethers line {
        stroke: rgba(28, 95, 116, .42);
        stroke-width: 1.4;
        stroke-dasharray: 4 5;
      }
      .hnl-anchor {
        position: absolute;
        width: 11px;
        height: 11px;
        margin: -5px 0 0 -5px;
        border: 2px solid rgba(28, 95, 116, .78);
        border-radius: 999px;
        background: rgba(255, 250, 240, .82);
        box-shadow: 0 0 0 5px rgba(28, 95, 116, .08);
        pointer-events: none;
      }
      .hnl-stage {
        position: absolute;
        inset: 0;
        pointer-events: none;
      }
      .hnl-note,
      .hnl-editor,
      .hnl-panel,
      .hnl-fab {
        pointer-events: auto;
        box-sizing: border-box;
      }
      .hnl-note {
        position: absolute;
        z-index: 4;
        min-width: 34px;
        max-width: 260px;
        min-height: 32px;
        padding: 7px 10px;
        border: 1px solid rgba(58, 48, 34, .28);
        border-radius: 12px;
        background:
          linear-gradient(145deg, rgba(255, 247, 232, .78), rgba(216, 204, 182, .62));
        color: #172125;
        font: 700 13px/1.35 ui-sans-serif, "Segoe UI", "Microsoft YaHei", sans-serif;
        box-shadow: 7px 7px 16px rgba(80, 64, 42, .18), -7px -7px 16px rgba(255, 255, 255, .72);
        backdrop-filter: blur(8px) saturate(1.15);
        -webkit-backdrop-filter: blur(8px) saturate(1.15);
        cursor: grab;
        user-select: none;
      }
      .hnl-note:active { cursor: grabbing; }
      .hnl-note small {
        display: block;
        max-width: 230px;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
        color: rgba(23, 33, 37, .64);
        font-size: 11px;
        font-weight: 600;
      }
      .hnl-editor {
        position: absolute;
        z-index: 10;
        width: clamp(220px, 38vw, 420px);
        max-width: calc(100vw - 32px);
        padding: 7px;
        border: 1px solid rgba(58, 48, 34, .24);
        border-radius: 18px;
        background:
          linear-gradient(145deg, rgba(212, 199, 178, .50), rgba(255, 243, 221, .56));
        box-shadow: inset 6px 6px 13px rgba(80, 64, 42, .14), inset -6px -6px 13px rgba(255, 255, 255, .62), 0 10px 24px rgba(80, 64, 42, .12);
        backdrop-filter: blur(13px) saturate(1.18);
        -webkit-backdrop-filter: blur(13px) saturate(1.18);
      }
      .hnl-editor textarea {
        display: block;
        box-sizing: border-box;
        width: 100%;
        min-height: 48px;
        max-height: 132px;
        resize: none;
        overflow: auto;
        border: 0;
        outline: 0;
        border-radius: 13px;
        padding: 10px 12px;
        background: rgba(255, 250, 240, .42);
        color: #172125;
        font: 700 15px/1.45 ui-sans-serif, "Segoe UI", "Microsoft YaHei", sans-serif;
        box-shadow: inset 4px 4px 9px rgba(80, 64, 42, .11), inset -4px -4px 9px rgba(255, 255, 255, .50);
      }
      .hnl-editor textarea::-webkit-scrollbar {
        width: 8px;
      }
      .hnl-editor textarea::-webkit-scrollbar-thumb {
        border: 2px solid rgba(255, 250, 240, .62);
        border-radius: 999px;
        background: rgba(28, 95, 116, .72);
      }
      .hnl-copy-quote {
        position: absolute;
        left: 14px;
        top: -38px;
        width: 34px;
        height: 34px;
        border: 1px solid rgba(23, 33, 37, .24);
        border-radius: 10px;
        background: linear-gradient(145deg, rgba(255,250,240,.58), rgba(236,228,213,.26));
        color: #172125;
        box-shadow: 5px 5px 12px rgba(80, 64, 42, .12), -5px -5px 12px rgba(255, 255, 255, .62);
        backdrop-filter: blur(7px);
        -webkit-backdrop-filter: blur(7px);
        cursor: pointer;
      }
      .hnl-copy-quote::before,
      .hnl-copy-quote::after {
        content: "";
        position: absolute;
        width: 12px;
        height: 14px;
        border: 2px solid currentColor;
        border-radius: 2px;
      }
      .hnl-copy-quote::before { left: 9px; top: 8px; }
      .hnl-copy-quote::after { left: 13px; top: 12px; background: rgba(255,255,255,.18); }
      .hnl-copy-quote.is-copied { color: #28745c; transform: translateY(-1px); }
      .hnl-fab {
        position: fixed;
        right: 22px;
        bottom: 22px;
        z-index: 24;
        display: grid;
        place-items: center;
        width: 58px;
        height: 58px;
        border: 1px solid rgba(58, 48, 34, .28);
        border-radius: 16px;
        background: linear-gradient(145deg, #fff7e8, #d8ccb6);
        color: #172125;
        box-shadow: 9px 9px 20px rgba(80, 64, 42, .18), -9px -9px 20px rgba(255, 255, 255, .72);
        cursor: pointer;
        overflow: visible;
      }
      .hnl-fab-icon {
        display: block;
        position: relative;
        width: 22px;
        height: 22px;
        margin: 0;
        border: 2px solid currentColor;
        border-radius: 4px;
      }
      .hnl-fab-icon::after {
        content: "";
        position: absolute;
        left: 4px;
        right: 4px;
        top: 6px;
        border-top: 2px solid currentColor;
        box-shadow: 0 6px 0 currentColor;
      }
      .hnl-count {
        position: absolute;
        right: -8px;
        top: -8px;
        min-width: 24px;
        height: 24px;
        padding: 0 5px;
        border-radius: 999px;
        background: #1c5f74;
        color: #fff7e8;
        font: 900 12px/24px ui-sans-serif, "Segoe UI", sans-serif;
        box-shadow: 3px 3px 8px rgba(80, 64, 42, .18), -2px -2px 6px rgba(255, 255, 255, .64);
      }
      .hnl-panel {
        position: fixed;
        right: 22px;
        bottom: 88px;
        z-index: 22;
        width: min(420px, calc(100vw - 32px));
        max-height: min(70vh, 680px);
        display: grid;
        grid-template-rows: auto auto minmax(120px, 1fr) auto;
        gap: 12px;
        padding: 16px;
        border: 1px solid rgba(58, 48, 34, .30);
        border-radius: 18px;
        background: rgba(255, 250, 240, .76);
        box-shadow: 16px 16px 34px rgba(80, 64, 42, .20), -12px -12px 28px rgba(255, 255, 255, .72);
        backdrop-filter: blur(14px) saturate(1.22);
        -webkit-backdrop-filter: blur(14px) saturate(1.22);
      }
      .hnl-panel[hidden] { display: none; }
      .hnl-panel-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
      }
      .hnl-panel h2 {
        margin: 0;
        color: #172125;
        font: 900 18px/1.2 ui-sans-serif, "Segoe UI", "Microsoft YaHei", sans-serif;
      }
      .hnl-panel button,
      .hnl-panel select {
        min-height: 34px;
        border: 1px solid rgba(23, 33, 37, .28);
        border-radius: 10px;
        background: rgba(255, 247, 232, .70);
        color: #172125;
        font: 800 12px/1 ui-sans-serif, "Segoe UI", "Microsoft YaHei", sans-serif;
        box-shadow: 4px 4px 9px rgba(80, 64, 42, .10), -4px -4px 9px rgba(255, 255, 255, .55);
        cursor: pointer;
      }
      .hnl-tools {
        display: grid;
        grid-template-columns: 1fr auto auto;
        gap: 8px;
      }
      .hnl-list {
        min-height: 120px;
        overflow: auto;
        padding-right: 4px;
        scrollbar-color: #1c5f74 rgba(255, 250, 240, .45);
      }
      .hnl-list::-webkit-scrollbar { width: 10px; }
      .hnl-list::-webkit-scrollbar-thumb {
        border: 2px solid rgba(255,250,240,.75);
        border-radius: 999px;
        background: #1c5f74;
      }
      .hnl-item {
        padding: 10px;
        margin: 0 0 8px;
        border: 1px solid rgba(58, 48, 34, .20);
        border-radius: 12px;
        background: rgba(255,255,255,.35);
      }
      .hnl-item p {
        margin: 0 0 6px;
        color: #172125;
        font: 700 13px/1.45 ui-sans-serif, "Segoe UI", "Microsoft YaHei", sans-serif;
      }
      .hnl-item small {
        display: block;
        margin-bottom: 8px;
        color: rgba(23, 33, 37, .62);
        font: 600 11px/1.35 ui-sans-serif, "Segoe UI", sans-serif;
      }
      .hnl-item-actions { display: flex; flex-wrap: wrap; gap: 6px; }
      .hnl-export {
        width: 100%;
        min-height: 94px;
        resize: vertical;
        border: 1px solid rgba(58, 48, 34, .22);
        border-radius: 12px;
        padding: 10px;
        background: rgba(255,255,255,.40);
        color: #172125;
        font: 600 12px/1.45 ui-monospace, Consolas, monospace;
      }
      .hnl-empty {
        margin: 18px 0;
        color: rgba(23, 33, 37, .62);
        font: 700 13px/1.4 ui-sans-serif, "Segoe UI", "Microsoft YaHei", sans-serif;
      }
      @media (max-width: 560px) {
        .hnl-fab { right: 14px; bottom: 14px; }
        .hnl-panel { right: 12px; bottom: 76px; }
      }
    </style>
    <div class="hnl-layer">
      <svg class="hnl-tethers" aria-hidden="true"></svg>
      <div class="hnl-stage"></div>
      <button class="hnl-fab" type="button" aria-label="Notes"><span class="hnl-fab-icon"></span><span class="hnl-count">0</span></button>
      <aside class="hnl-panel" hidden>
        <div class="hnl-panel-head">
          <h2>Notes</h2>
          <button class="hnl-close" type="button">Close</button>
        </div>
        <div class="hnl-tools">
          <select class="hnl-mode" aria-label="Export mode">
            <option value="ordered">1. Note</option>
            <option value="source">Original + Note</option>
          </select>
          <button class="hnl-copy-all" type="button">Copy</button>
          <button class="hnl-download" type="button">Download</button>
        </div>
        <div class="hnl-list"></div>
        <textarea class="hnl-export" readonly aria-label="Notes export"></textarea>
      </aside>
    </div>
  `;

  const stage = root.querySelector(".hnl-stage");
  const tetherSvg = root.querySelector(".hnl-tethers");
  const fab = root.querySelector(".hnl-fab");
  const countEl = root.querySelector(".hnl-count");
  const panel = root.querySelector(".hnl-panel");
  const closePanel = root.querySelector(".hnl-close");
  const listEl = root.querySelector(".hnl-list");
  const modeEl = root.querySelector(".hnl-mode");
  const exportEl = root.querySelector(".hnl-export");
  const copyAll = root.querySelector(".hnl-copy-all");
  const downloadBtn = root.querySelector(".hnl-download");
  let notes = loadNotes();
  let active = null;
  let saveTimer = 0;
  let selectionTimer = 0;
  let drag = null;
  let suppressClickUntil = 0;

  function cleanText(value, limit = 700) {
    return String(value || "").replace(/\s+/g, " ").trim().slice(0, limit);
  }

  function loadNotes() {
    try {
      const data = JSON.parse(localStorage.getItem(storageKey) || "[]");
      return Array.isArray(data) ? data : [];
    } catch {
      return [];
    }
  }

  function saveSoon() {
    window.clearTimeout(saveTimer);
    saveTimer = window.setTimeout(() => {
      try { localStorage.setItem(storageKey, JSON.stringify(notes)); } catch {}
      renderPanel();
      renderNotes();
    }, 80);
  }

  function copyText(text) {
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(text).catch(() => fallbackCopy(text));
    } else {
      fallbackCopy(text);
    }
  }

  function fallbackCopy(text) {
    const area = document.createElement("textarea");
    area.value = text;
    area.style.position = "fixed";
    area.style.left = "-9999px";
    document.body.appendChild(area);
    area.focus();
    area.select();
    try { document.execCommand("copy"); } catch {}
    area.remove();
  }

  function cssPath(el) {
    if (!el || el.nodeType !== 1) return "body";
    if (el === document.body) return "body";
    if (el.id) return "#" + escapeCss(el.id);
    const parts = [];
    let node = el;
    while (node && node.nodeType === 1 && node !== document.body && parts.length < 7) {
      const tag = node.localName.toLowerCase();
      let index = 1;
      let sib = node;
      while ((sib = sib.previousElementSibling)) {
        if (sib.localName.toLowerCase() === tag) index += 1;
      }
      parts.unshift(`${tag}:nth-of-type(${index})`);
      node = node.parentElement;
    }
    return parts.length ? "body > " + parts.join(" > ") : "body";
  }

  function elementForNode(node) {
    return !node ? null : (node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement);
  }

  function noteHost(node) {
    const el = elementForNode(node);
    return el?.closest("p, li, td, th, pre, code, blockquote, article, section, main, div") || document.body;
  }

  function hostForNote(note) {
    try { return document.querySelector(note.hostSelector) || document.body; }
    catch { return document.body; }
  }

  function hostPoint(host, clientX, clientY) {
    const rect = host.getBoundingClientRect();
    const width = Math.max(rect.width, 1);
    const height = Math.max(rect.height, 1);
    return {
      relX: clamp((clientX - rect.left) / width, 0, 1),
      relY: clamp((clientY - rect.top) / height, 0, 1)
    };
  }

  function notePoint(note) {
    const host = hostForNote(note);
    const rect = host.getBoundingClientRect();
    return {
      anchorX: rect.left + rect.width * (note.relX ?? .5),
      anchorY: rect.top + rect.height * (note.relY ?? .5),
      x: rect.left + rect.width * (note.relX ?? .5) + (note.dx || 0),
      y: rect.top + rect.height * (note.relY ?? .5) + (note.dy || 0)
    };
  }

  function rectsOverlap(a, b) {
    return a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
  }

  function placeEditor(editor, point) {
    const margin = 12;
    const rect = editor.getBoundingClientRect();
    const width = Math.min(rect.width || 360, window.innerWidth - margin * 2);
    const height = Math.min(rect.height || 72, window.innerHeight - margin * 2);
    const maxLeft = Math.max(margin, window.innerWidth - width - margin);
    const maxTop = Math.max(margin, window.innerHeight - height - margin);
    let left = clamp(point.x - Math.min(64, width * .18), margin, maxLeft);
    let top = clamp(point.y, margin, maxTop);
    const fabRect = fab.getBoundingClientRect();
    const fabSafe = {
      left: fabRect.left - 16,
      top: fabRect.top - 16,
      right: fabRect.right + 16,
      bottom: fabRect.bottom + 16
    };
    const proposed = { left, top, right: left + width, bottom: top + height };
    if (rectsOverlap(proposed, fabSafe)) {
      const aboveFab = fabRect.top - height - 18;
      if (aboveFab >= margin) {
        top = Math.min(top, aboveFab);
      } else {
        left = Math.min(left, Math.max(margin, fabRect.left - width - 18));
      }
    }
    editor.style.left = Math.round(left) + "px";
    editor.style.top = Math.round(top) + "px";
  }

  function sizeEditorInput(area) {
    area.style.height = "auto";
    area.style.height = clamp(area.scrollHeight, 48, 132) + "px";
  }

  function newId() {
    return "hnl-" + Math.random().toString(36).slice(2) + Date.now().toString(36);
  }

  function createNote(context) {
    const hostNode = context.host || noteHost(context.node);
    const point = hostPoint(hostNode, context.clientX, context.clientY);
    const note = {
      id: newId(),
      text: "",
      quote: cleanText(context.quote || ""),
      hostSelector: cssPath(hostNode),
      relX: point.relX,
      relY: point.relY,
      dx: 0,
      dy: 0,
      createdAt: nowIso(),
      updatedAt: nowIso()
    };
    notes.push(note);
    return note;
  }

  function finishActive() {
    if (!active) return;
    const { note, editor } = active;
    const input = editor.querySelector("textarea");
    note.text = cleanText(input.value, 4000);
    note.updatedAt = nowIso();
    editor.remove();
    if (!note.text) {
      notes = notes.filter(item => item.id !== note.id);
    }
    active = null;
    saveSoon();
    renderNotes();
  }

  function openEditor(context) {
    finishActive();
    panel.hidden = true;
    const note = context.note || createNote(context);
    const point = notePoint(note);
    const editor = document.createElement("div");
    editor.className = "hnl-editor";
    editor.dataset.noteId = note.id;
    editor.style.left = "0px";
    editor.style.top = "0px";
    editor.innerHTML = `${note.quote ? '<button class="hnl-copy-quote" type="button" aria-label="Copy selected text"></button>' : ""}<textarea aria-label="Note"></textarea>`;
    stage.appendChild(editor);
    const area = editor.querySelector("textarea");
    area.value = note.text || "";
    sizeEditorInput(area);
    placeEditor(editor, point);
    const copyQuote = editor.querySelector(".hnl-copy-quote");
    copyQuote?.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      copyText(note.quote || "");
      copyQuote.classList.add("is-copied");
      window.setTimeout(() => copyQuote.classList.remove("is-copied"), 650);
    });
    area.addEventListener("input", () => {
      note.text = area.value;
      note.updatedAt = nowIso();
      sizeEditorInput(area);
      placeEditor(editor, notePoint(note));
      saveSoon();
    });
    active = { note, editor };
    window.setTimeout(() => area.focus(), 0);
    renderNotes();
  }

  function exportText() {
    const saved = notes.filter(note => cleanText(note.text));
    if (modeEl.value === "source") {
      return saved.map(note => `Original: ${note.quote || "page anchor"}\nNote: ${cleanText(note.text, 4000)}`).join("\n\n");
    }
    return saved.map((note, index) => `${index + 1}. ${cleanText(note.text, 4000)}`).join("\n\n");
  }

  function renderPanel() {
    const saved = notes.filter(note => cleanText(note.text));
    countEl.textContent = String(saved.length);
    exportEl.value = exportText();
    if (!saved.length) {
      listEl.innerHTML = '<p class="hnl-empty">No notes yet.</p>';
      return;
    }
    listEl.innerHTML = "";
    saved.forEach((note, index) => {
      const item = document.createElement("article");
      item.className = "hnl-item";
      item.innerHTML = `
        <p>${escapeHtml(index + 1 + ". " + cleanText(note.text, 260))}</p>
        <small>${escapeHtml(note.quote || "page anchor")}</small>
        <div class="hnl-item-actions">
          <button type="button" data-copy-note="${note.id}">Copy note</button>
          <button type="button" data-copy-source="${note.id}">Copy source</button>
          <button type="button" data-edit-note="${note.id}">Edit</button>
        </div>
      `;
      listEl.appendChild(item);
    });
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
  }

  function renderNotes() {
    Array.from(stage.querySelectorAll(".hnl-note,.hnl-anchor")).forEach(el => el.remove());
    tetherSvg.innerHTML = "";
    const activeId = active?.note?.id || "";
    const saved = notes.filter(note => cleanText(note.text) && note.id !== activeId);
    for (const note of saved) {
      const point = notePoint(note);
      const anchor = document.createElement("div");
      anchor.className = "hnl-anchor";
      anchor.style.left = point.anchorX + "px";
      anchor.style.top = point.anchorY + "px";
      stage.appendChild(anchor);

      const view = document.createElement("div");
      view.className = "hnl-note";
      view.dataset.noteId = note.id;
      view.style.left = clamp(point.x, 8, window.innerWidth - 42) + "px";
      view.style.top = clamp(point.y, 8, window.innerHeight - 42) + "px";
      view.innerHTML = `${escapeHtml(cleanText(note.text, 80))}<small>${escapeHtml(note.quote || "page anchor")}</small>`;
      stage.appendChild(view);

      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("x1", String(point.anchorX));
      line.setAttribute("y1", String(point.anchorY));
      line.setAttribute("x2", String(point.x));
      line.setAttribute("y2", String(point.y));
      tetherSvg.appendChild(line);
    }
    renderPanel();
  }

  function noteById(id) {
    return notes.find(note => note.id === id);
  }

  function openSelectionNote(sourceEvent) {
    if (active) return false;
    const sel = window.getSelection();
    const quote = cleanText(sel?.toString(), 700);
    if (!quote || !sel || sel.rangeCount === 0 || sel.isCollapsed) return false;
    const range = sel.getRangeAt(0).cloneRange();
    const element = elementForNode(range.commonAncestorContainer);
    if (!element || element.closest(noteIgnoreSelector) || host.contains(element)) return false;
    const rects = Array.from(range.getClientRects()).filter(rect => rect.width > 2 && rect.height > 2);
    if (!rects.length) return false;
    const rect = rects[0];
    const hostNode = noteHost(range.commonAncestorContainer);
    const clientX = rect.left + Math.min(rect.width / 2, rect.width - 1);
    const clientY = rect.bottom + 8;
    openEditor({ quote, node: range.commonAncestorContainer, host: hostNode, clientX, clientY });
    suppressClickUntil = Date.now() + 220;
    return true;
  }

  function queueSelection(event, delay = 140) {
    window.clearTimeout(selectionTimer);
    selectionTimer = window.setTimeout(() => openSelectionNote(event), delay);
  }

  document.addEventListener("selectionchange", () => {
    if (document.activeElement?.matches?.("input, textarea, select")) return;
    queueSelection(null, 220);
  });
  document.addEventListener("mouseup", (event) => {
    if (event.defaultPrevented || elementForNode(event.target)?.closest(noteIgnoreSelector)) return;
    queueSelection(event, 80);
  }, true);
  document.addEventListener("click", (event) => {
    if (Date.now() < suppressClickUntil) {
      const activeText = active ? cleanText(active.editor.querySelector("textarea")?.value, 4000) : "";
      if (!(activeText && !host.contains(event.target))) {
        event.preventDefault();
        event.stopPropagation();
        return;
      }
    }
    if (active && !host.contains(event.target)) finishActive();
  }, true);
  document.addEventListener("dblclick", (event) => {
    if (event.defaultPrevented || elementForNode(event.target)?.closest(noteIgnoreSelector)) return;
    if (Date.now() < suppressClickUntil) return;
    const hostNode = noteHost(event.target);
    openEditor({ node: event.target, host: hostNode, clientX: event.clientX, clientY: event.clientY });
  }, true);

  root.addEventListener("click", (event) => {
    event.stopPropagation();
    const target = event.target;
    if (target.closest(".hnl-fab")) {
      panel.hidden = !panel.hidden;
      renderPanel();
      return;
    }
    if (target.closest(".hnl-close")) {
      panel.hidden = true;
      return;
    }
    if (target.closest(".hnl-copy-all")) {
      copyText(exportText());
      return;
    }
    if (target.closest(".hnl-download")) {
      const blob = new Blob([exportText()], { type: "text/plain;charset=utf-8" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "html-notes.txt";
      a.click();
      URL.revokeObjectURL(a.href);
      return;
    }
    const copyNote = target.closest("[data-copy-note]");
    if (copyNote) {
      copyText(cleanText(noteById(copyNote.dataset.copyNote)?.text, 4000));
      return;
    }
    const copySource = target.closest("[data-copy-source]");
    if (copySource) {
      const note = noteById(copySource.dataset.copySource);
      copyText(`Original: ${note?.quote || "page anchor"}\nNote: ${cleanText(note?.text, 4000)}`);
      return;
    }
    const edit = target.closest("[data-edit-note]");
    if (edit) {
      const note = noteById(edit.dataset.editNote);
      if (note) openEditor({ note });
    }
  });
  modeEl.addEventListener("change", renderPanel);

  stage.addEventListener("dblclick", (event) => {
    const view = event.target.closest(".hnl-note");
    if (!view) return;
    event.preventDefault();
    event.stopPropagation();
    const note = noteById(view.dataset.noteId);
    if (note) openEditor({ note });
  });

  function startDrag(event) {
    const view = event.target.closest(".hnl-note");
    if (!view || event.target.closest("button, textarea, input, select")) return;
    const note = noteById(view.dataset.noteId);
    if (!note) return;
    event.preventDefault();
    event.stopPropagation();
    const point = notePoint(note);
    drag = {
      note,
      startX: event.clientX,
      startY: event.clientY,
      startDx: note.dx || 0,
      startDy: note.dy || 0,
      moved: false
    };
    view.setPointerCapture?.(event.pointerId);
  }

  function moveDrag(event) {
    if (!drag) return;
    event.preventDefault();
    const deltaX = event.clientX - drag.startX;
    const deltaY = event.clientY - drag.startY;
    if (!drag.moved && Math.hypot(deltaX, deltaY) < 5) return;
    drag.note.dx = drag.startDx + deltaX;
    drag.note.dy = drag.startDy + deltaY;
    drag.note.updatedAt = nowIso();
    drag.moved = true;
    renderNotes();
  }

  function endDrag(event) {
    if (!drag) return;
    const finished = drag;
    drag = null;
    if (!finished.moved) {
      event?.preventDefault?.();
      event?.stopPropagation?.();
      suppressClickUntil = Date.now() + 180;
      openEditor({ note: finished.note });
      return;
    }
    suppressClickUntil = Date.now() + 250;
    saveSoon();
  }

  if (supportsPointer) {
    stage.addEventListener("pointerdown", startDrag);
    stage.addEventListener("pointermove", moveDrag);
    stage.addEventListener("pointerup", endDrag);
    stage.addEventListener("pointercancel", endDrag);
  } else {
    stage.addEventListener("mousedown", startDrag);
    window.addEventListener("mousemove", moveDrag);
    window.addEventListener("mouseup", endDrag);
  }

  window.addEventListener("scroll", () => window.requestAnimationFrame(renderNotes), { passive: true });
  window.addEventListener("resize", () => window.requestAnimationFrame(renderNotes));
  renderNotes();
})();
</script>
<!-- html-note-layer:end -->
"""


def strip_existing(text: str) -> str:
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), flags=re.DOTALL)
    return pattern.sub("", text)


def inject(text: str, force: bool) -> str:
    if START in text:
        if not force:
            raise ValueError("HTML already contains html-note-layer; pass --force to replace it")
        text = strip_existing(text)

    match = re.search(r"</body\s*>", text, flags=re.IGNORECASE)
    if match:
        return text[: match.start()] + RUNTIME + "\n" + text[match.start() :]
    return text.rstrip() + "\n" + RUNTIME + "\n"


def default_output(input_path: Path) -> Path:
    return input_path.with_name(input_path.stem + ".noted" + input_path.suffix)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("html", help="Existing HTML file to enhance")
    parser.add_argument("--output", help="Output HTML path; defaults to <name>.noted.html")
    parser.add_argument("--in-place", action="store_true", help="Overwrite the input HTML")
    parser.add_argument("--force", action="store_true", help="Replace an existing injected note layer")
    args = parser.parse_args(argv)

    input_path = Path(args.html).resolve()
    if not input_path.exists() or not input_path.is_file():
      print(f"ERROR: HTML file does not exist: {input_path}", file=sys.stderr)
      return 1
    if input_path.suffix.lower() not in {".html", ".htm"}:
      print(f"ERROR: expected .html or .htm file: {input_path}", file=sys.stderr)
      return 1

    output_path = input_path if args.in_place else Path(args.output).resolve() if args.output else default_output(input_path)
    if output_path == input_path and not args.in_place:
      print("ERROR: refusing to overwrite input without --in-place", file=sys.stderr)
      return 1

    try:
      original = input_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
      original = input_path.read_text(encoding="utf-8", errors="ignore")

    try:
      result = inject(original, force=args.force)
    except ValueError as exc:
      print(f"ERROR: {exc}", file=sys.stderr)
      return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result, encoding="utf-8", newline="")
    print(f"Injected note layer: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
