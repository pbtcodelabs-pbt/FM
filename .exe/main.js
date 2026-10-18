// صدام فروٹ منڈی — کمپیوٹر (ونڈوز) ایڈیشن
// یہ وہی لائیو ایپ کھولتا ہے جو موبائل پر چلتی ہے، اس لیے ڈیٹا اور اپڈیٹس دونوں جگہ ایک جیسے رہتے ہیں
const { app, BrowserWindow, Menu, shell, session } = require('electron');
const path = require('path');

const APP_URL = 'https://fm-saddam-mandi.web.app/';
const ICON = path.join(__dirname, 'build', 'icon.png');

// گوگل سائن اِن (ڈرائیو بیک اپ) "Electron" والے براؤزر کو روک دیتا ہے — عام Chrome کی شناخت دیں
const CHROME_UA = `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${process.versions.chrome} Safari/537.36`;

// واٹس ایپ، فون، ای میل وغیرہ کے لنک کمپیوٹر کے اپنے براؤزر/ایپ میں کھلیں
const EXTERNAL = /^(mailto:|tel:|sms:|whatsapp:|https?:\/\/(wa\.me|api\.whatsapp\.com|web\.whatsapp\.com|chat\.whatsapp\.com|play\.google\.com|www\.youtube\.com|youtube\.com|maps\.google\.com|www\.google\.com\/maps))/i;

let win = null;

if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (win) { if (win.isMinimized()) win.restore(); win.show(); win.focus(); }
  });
  app.whenReady().then(start);
}

app.on('window-all-closed', () => app.quit());

function start() {
  app.userAgentFallback = CHROME_UA;
  session.defaultSession.setUserAgent(CHROME_UA);
  // کیمرہ (اسکین)، نوٹیفکیشن، کلپ بورڈ وغیرہ کی اجازت
  session.defaultSession.setPermissionRequestHandler((wc, permission, cb) => cb(true));

  Menu.setApplicationMenu(Menu.buildFromTemplate([
    { label: 'ایپ', submenu: [
      { role: 'reload', label: 'ری فریش (F5)', accelerator: 'F5' },
      { role: 'forceReload', label: 'مکمل ری فریش', accelerator: 'Ctrl+F5' },
      { type: 'separator' },
      { role: 'togglefullscreen', label: 'پوری اسکرین (F11)', accelerator: 'F11' },
      { type: 'separator' },
      { role: 'quit', label: 'بند کریں' }
    ]},
    { label: 'سائز', submenu: [
      { role: 'zoomIn', label: 'بڑا کریں (Ctrl +)', accelerator: 'CommandOrControl+=' },
      { role: 'zoomOut', label: 'چھوٹا کریں (Ctrl -)' },
      { role: 'resetZoom', label: 'اصل سائز (Ctrl 0)' }
    ]},
    { label: 'مدد', submenu: [
      { role: 'toggleDevTools', label: 'ڈویلپر ٹولز', accelerator: 'Ctrl+Shift+I' }
    ]}
  ]));

  win = new BrowserWindow({
    width: 1366,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    show: false,
    title: 'صدام فروٹ منڈی',
    icon: ICON,
    backgroundColor: '#0f766e',
    autoHideMenuBar: true,
    webPreferences: { contextIsolation: true, nodeIntegration: false, spellcheck: false }
  });
  win.maximize();
  win.once('ready-to-show', () => win.show());
  setupContents(win.webContents);

  // انٹرنیٹ نہ ہو اور ایپ پہلے کبھی نہ کھلی ہو تو صاف اردو پیغام اور "دوبارہ کوشش" کا بٹن
  win.webContents.on('did-fail-load', (e, code, desc, url, isMainFrame) => {
    if (!isMainFrame || code === -3) return; // -3 = لوڈ خود روکا گیا، غلطی نہیں
    win.loadFile(path.join(__dirname, 'offline.html'));
  });

  win.loadURL(APP_URL);
}

function setupContents(wc) {
  wc.setWindowOpenHandler(({ url }) => {
    if (EXTERNAL.test(url)) { shell.openExternal(url); return { action: 'deny' }; }
    // پرنٹ/رپورٹ والی کھڑکیاں اور گوگل سائن اِن ایپ کے اندر ہی کھلیں
    return {
      action: 'allow',
      overrideBrowserWindowOptions: {
        width: 1000, height: 760, icon: ICON, autoHideMenuBar: true,
        webPreferences: { contextIsolation: true, nodeIntegration: false }
      }
    };
  });
  wc.on('did-create-window', (child) => setupContents(child.webContents));
  wc.on('will-navigate', (e, url) => {
    if (EXTERNAL.test(url)) { e.preventDefault(); shell.openExternal(url); }
  });
}
