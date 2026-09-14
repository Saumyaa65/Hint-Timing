# Hint Frontend — Full-featured (Vite + React)

This frontend is the full-featured version of the Hint Generation UI. It ships with:

- Vite + React (dev server & build)
- React Router based navigation
- Monaco Editor integration (bundled + CDN fallback)
- Tailwind CSS configured (PostCSS + autoprefixer)
- Sample pages: problem list, problem detail (both `Full` and `Normal` variants present)

What I changed and added
- Added `vite.config.js` with React plugin and Monaco plugin so the editor can be bundled.
- Added `tailwind.config.js` and `postcss.config.js` so Tailwind utilities are available if you switch CSS to use them.
- Updated `index.html` to load the `main_full.jsx` entry so the full UI renders by default.
- Made `MonacoEditor.jsx` robust: it initializes when `window.monaco` is available and falls back to a textarea; there is also a CDN loader script in `index.html` for convenience.
- Added `react-router-dom` in `package.json` and included `monaco-editor` + dev plugins in devDependencies.

Quick start (PowerShell)

```powershell
cd \\\wsl.localhost\Ubuntu\home\mohnish\srip\Hint_Generation\frontend
npm install
npm run dev
```

Dev notes
- Default API URL: `http://localhost:8000/api` (See `src/services/apiClient.js`). Change it to point to your backend as needed.
- Monaco:
	- If `monaco-editor` is installed via npm it will be bundled by Vite (#recommended for production-like behavior).
	- If not installed, `index.html` contains a CDN loader which attempts to attach Monaco to `window.monaco` at runtime (good for quick testing but not ideal for production).
- Tailwind:
	- Tailwind is configured and ready. To use it, import the Tailwind directives in your main CSS file (e.g., `@tailwind base; @tailwind components; @tailwind utilities;`) and convert styles to utilities as needed.

Recommended next steps
- Run the app locally (see Quick start above).
- Verify the full UI by visiting the dev server URL printed by Vite (usually `http://localhost:5173`).
- If you want a single canonical set of pages (you currently have `ProblemList.jsx` and `ProblemListFull.jsx` etc.), tell me whether you want me to:
	1. Consolidate to use the `Full` set everywhere (recommended), or
	2. Consolidate to use the `Normal` set, or
	3. Merge the best parts of both into one single, polished set.

If you want me to fully consolidate the app and remove duplicate files, reply with `Consolidate: Full`, `Consolidate: Normal`, or `Consolidate: Merge` and I'll proceed with a precise plan and apply the changes.

If anything fails while running `npm install` or `npm run dev`, copy/paste the terminal output here and I'll diagnose and fix it.

Happy to continue — tell me if you want consolidation now or prefer to run locally first.
