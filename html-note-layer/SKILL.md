---
name: html-note-layer
description: Add a non-destructive local note layer to existing HTML files. Use when the user wants any old HTML report or page to support selecting text for notes, double-clicking anywhere for notes, dragging note anchors, preserving notes in localStorage, opening a floating notes panel, and copying or exporting notes without changing the original page content layer.
version: 1.0.4
---

# HTML Note Layer

> **版本**: v1.0.4
> **用途**: 给已有 HTML 注入独立阅读笔记层，保留原页面内容和布局。
<!-- @类型: Skill 概览 -->
<!-- @目的: 把选区笔记、任意位置笔记、拖拽、锚点、悬浮笔记面板和本地保存做成可复用 HTML 增强能力 -->

Use this skill when an existing `.html` file needs local reading notes without redesigning the page or modifying its content DOM.

## Contract

- Never overwrite the source HTML unless the user explicitly asks for `--in-place`.
- Inject one isolated runtime layer that keeps controls out of the original page layout.
- Store notes in browser `localStorage`; refresh must not lose notes.
- Support two note entry modes:
  - select text, then write a note anchored to the selected text location;
  - double-click any readable page location, then write a free-position note.
- Support saved note dragging; persist the drag offset.
- Keep the original page readable: no inline widgets inside paragraphs, no layout shifts, no popup modals.
- Provide a floating button. Clicking it opens a notes panel showing all notes, export text, and copy controls.
- Provide a selection copy button near the selected text. It must be visually separate from the note editor and should copy only the selected text.
- Provide two export modes: `1. <note>` and `Original: <quote or anchor>\nNote: <note>`.

## @工作流: Inject Local HTML Note Layer
<!-- @类型: 标准操作流程(SOP) -->
<!-- @目的: 给旧 HTML 生成一个不破坏原内容层的可记笔记副本 -->
<!-- @场景: 用户提供旧 HTML，希望选中文字、双击任意位置、拖拽锚点、查看和复制所有笔记 -->
<!-- @优先级: 必须 -->
<!-- @验证点: 生成的 HTML 支持选区笔记、任意位置笔记、悬浮面板、复制、拖拽和刷新持久化 -->
<!-- @验证方式: `node scripts/smoke_note_layer.js <output.html>` 输出 NOTE_LAYER_SMOKE_OK -->

### @步骤1: Create A Noted Copy
<!-- @类型: 操作步骤 -->
<!-- @优先级: 必须 -->
<!-- @验证点: 原 HTML 不被覆盖，输出文件包含 html-note-layer runtime -->
<!-- @验证方式: 输出路径存在，且源文件内容未变 -->

- @动作: generate `<name>.noted.html` by default.
- @动作: use `--in-place` only when the user explicitly asks to overwrite the original HTML.
- @动作: if the target file already contains this note layer, use `--force` to replace the old runtime.

```bash
python scripts/inject_note_layer.py <old.html> --output <old.noted.html>
```

### @步骤2: Browser Regression
<!-- @类型: 操作步骤 -->
<!-- @优先级: 必须 -->
<!-- @验证点: 选区笔记、双击笔记、拖拽、浮动面板、导出和刷新恢复都可用 -->
<!-- @验证方式: smoke 脚本返回 NOTE_LAYER_SMOKE_OK -->

- @动作: open the injected HTML with a real browser regression script, not only static string checks.

```bash
node scripts/smoke_note_layer.js <old.noted.html>
```

### @步骤3: Deliver The Output Path
<!-- @类型: 操作步骤 -->
<!-- @优先级: 必须 -->
<!-- @验证点: 用户拿到可打开的 HTML 路径，并知道笔记保存位置 -->
<!-- @验证方式: 最终回答包含输出 HTML 路径和验证结果 -->

- @动作: return the generated HTML path.
- @动作: state that notes are saved in this browser's localStorage for that generated file.
- @动作: state that copying and exporting notes are available from the floating notes panel.

## Behavior Rules

- Single click should keep normal reading behavior; do not create notes on single click.
- Text selection opens the selection editor and a separate floating copy button.
- Double click opens a free-position note editor.
- Clicking a saved note opens it for editing; the saved note chip should be hidden while its editor is active.
- Clicking outside an editor commits a non-empty note and closes the active editor.
- Empty editors should disappear without saving.
- Saved notes should appear as movable anchors or glass-like note chips and remain after refresh.
- Saved note chips should render only while their source anchor is near the viewport; offscreen notes must not clamp into a top or bottom stack during scroll.
- Dragging a saved note should update only note-layer coordinates, never original page content.
- The note layer must be reversible by removing the injected block between `html-note-layer:start` and `html-note-layer:end`.

## Tool Notes

- `scripts/inject_note_layer.py` inserts the CSS/JS runtime before `</body>` or appends it if no body tag exists.
- The injected runtime uses Shadow DOM where available, fixed overlay positioning, stable CSS-path anchors, and localStorage.
- `scripts/smoke_note_layer.js` opens the page in Microsoft Edge headless and checks selection notes, double-click notes, dragging, panel copy controls, export text, and reload persistence.

## Failure Handling

- If a page has strict CSP that blocks inline scripts, create a copy with the blocking CSP removed or convert the runtime into a local external `.js` file next to the output HTML.
- If the page is canvas/PDF/virtual-scroll heavy and text selection has no stable DOM anchor, fall back to coordinate notes anchored to the nearest visible element or `body`.
- If localStorage is unavailable, keep the panel export usable and tell the user notes will not persist after refresh.

## Version History

- **v1.0.4** (2026-05-31) - Fixed scroll behavior so offscreen anchored notes hide instead of stacking at viewport edges.
- **v1.0.3** (2026-05-31) - Added kz-skill-creator semantic workflow, step, metadata, and action markers for strict package validation.
- **v1.0.2** (2026-05-31) - Fixed saved-note editing state, active-note rendering, compact editor layout, and floating button sizing.
- **v1.0.1** (2026-05-31) - Rewrote the instruction file in valid UTF-8 and documented selection-copy behavior.
- **v1.0.0** (2026-05-31) - Initial reusable HTML note-layer injector with selection notes, free notes, dragging, floating panel, copy/export, localStorage persistence, and browser smoke validation.
