'use strict';

const { app, BrowserWindow, shell, dialog, Menu } = require('electron');
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 8765;
const BACKEND_URL = `http://127.0.0.1:${PORT}`;
const POLL_INTERVAL_MS = 600;
const STARTUP_TIMEOUT_MS = 60_000;

let backendProcess = null;
let mainWindow = null;

// ── Backend ───────────────────────────────────────────────────────────────────

function resolveBackendExe() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend', 'backend.exe');
  }
  return null; // dev: assume `python start.py` already running
}

function startBackend() {
  const exe = resolveBackendExe();
  if (!exe) {
    console.log('[electron] Dev mode — expecting backend already on port', PORT);
    return;
  }
  if (!fs.existsSync(exe)) {
    dialog.showErrorBox(
      'Instalação incompleta',
      `Backend não encontrado:\n${exe}\n\nTente reinstalar o ZeroInsight.`
    );
    app.quit();
    return;
  }

  console.log('[electron] Starting backend:', exe);
  backendProcess = spawn(exe, [], {
    cwd: path.dirname(exe),
    windowsHide: true,
    detached: false,
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  backendProcess.stdout.on('data', (buf) =>
    process.stdout.write(`[backend] ${buf}`)
  );
  backendProcess.stderr.on('data', (buf) =>
    process.stderr.write(`[backend] ${buf}`)
  );
  backendProcess.on('close', (code) => {
    console.log('[electron] Backend exited with code', code);
    backendProcess = null;
  });
  backendProcess.on('error', (err) => {
    console.error('[electron] Failed to start backend:', err.message);
  });
}

function killBackend() {
  if (backendProcess && !backendProcess.killed) {
    console.log('[electron] Stopping backend…');
    backendProcess.kill('SIGTERM');
    backendProcess = null;
  }
}

// ── Health poll ───────────────────────────────────────────────────────────────

function waitForBackend() {
  return new Promise((resolve, reject) => {
    const deadline = Date.now() + STARTUP_TIMEOUT_MS;

    function probe() {
      const req = http.get(
        `${BACKEND_URL}/api/health`,
        { timeout: 1000 },
        (res) => {
          if (res.statusCode === 200) {
            res.resume();
            return resolve();
          }
          res.resume();
          retry();
        }
      );
      req.on('error', retry);
      req.on('timeout', () => { req.destroy(); retry(); });
    }

    function retry() {
      if (Date.now() >= deadline) {
        return reject(new Error(`Servidor não respondeu em ${STARTUP_TIMEOUT_MS / 1000}s.`));
      }
      setTimeout(probe, POLL_INTERVAL_MS);
    }

    // Give the process a moment to start before the first probe
    setTimeout(probe, 800);
  });
}

// ── Splash ────────────────────────────────────────────────────────────────────

const SPLASH_HTML = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>ZeroInsight</title>
<style>
  *, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }
  html, body {
    width:100%; height:100%; overflow:hidden;
    background:#070707;
    color:#FAFAFA;
    font-family:-apple-system,"Segoe UI",system-ui,sans-serif;
    display:flex; flex-direction:column;
    align-items:center; justify-content:center;
    gap:18px;
    user-select:none; -webkit-user-select:none;
    -webkit-app-region:drag;
  }
  .icon {
    width:60px; height:60px; border-radius:16px;
    background:#FFFFFF;
    color:#070707;
    display:flex; align-items:center; justify-content:center;
    font-size:30px;
    box-shadow:0 8px 28px rgba(0,0,0,0.5);
  }
  .name { font-size:22px; font-weight:700; letter-spacing:-0.4px; }
  .status { font-size:12px; color:#777777; margin-top:2px; }
  .ring {
    width:28px; height:28px; margin-top:6px;
    border:2.5px solid #333333;
    border-top-color:#FFFFFF;
    border-radius:50%;
    animation:spin .75s linear infinite;
  }
  @keyframes spin { to { transform:rotate(360deg); } }
</style>
</head>
<body>
  <div class="icon">⚡</div>
  <div style="text-align:center">
    <div class="name">ZeroInsight</div>
    <div class="status">Iniciando servidor…</div>
  </div>
  <div class="ring"></div>
</body>
</html>`;

function createSplash() {
  const win = new BrowserWindow({
    width: 360,
    height: 220,
    frame: false,
    resizable: false,
    center: true,
    transparent: false,
    backgroundColor: '#070707',
    alwaysOnTop: true,
    skipTaskbar: true,
    title: 'ZeroInsight',
    webPreferences: { nodeIntegration: false, contextIsolation: true },
  });
  win.loadURL(
    `data:text/html;charset=utf-8,${encodeURIComponent(SPLASH_HTML)}`
  );
  return win;
}

// ── Main window ───────────────────────────────────────────────────────────────

function createMainWindow() {
  const win = new BrowserWindow({
    width: 1300,
    height: 840,
    minWidth: 960,
    minHeight: 640,
    backgroundColor: '#070707',
    title: 'ZeroInsight',
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      devTools: !app.isPackaged,
    },
  });

  Menu.setApplicationMenu(null);

  // Open external links in the default OS browser instead of Electron
  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  win.loadURL(BACKEND_URL);
  win.once('ready-to-show', () => win.show());
  win.on('closed', () => { mainWindow = null; });

  return win;
}

// ── App lifecycle ─────────────────────────────────────────────────────────────

app.whenReady().then(async () => {
  startBackend();
  const splash = createSplash();

  try {
    await waitForBackend();
    mainWindow = createMainWindow();
    splash.destroy();
  } catch (err) {
    splash.destroy();
    await dialog.showErrorBox(
      'Falha ao iniciar o ZeroInsight',
      `O servidor não respondeu a tempo.\n\nDetalhes: ${err.message}\n\nVerifique se a instalação está completa.`
    );
    killBackend();
    app.quit();
  }
});

app.on('window-all-closed', () => {
  killBackend();
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', killBackend);

// Prevent the app from being quit while the backend is still starting
app.on('will-quit', (event) => {
  killBackend();
});
