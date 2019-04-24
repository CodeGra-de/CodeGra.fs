import path from 'path';
import { app, BrowserWindow } from 'electron'; // eslint-disable-line

/**
 * Set `__static` path to static files in production
 * https://simulatedgreg.gitbooks.io/electron-vue/content/en/using-static-assets.html
 */
if (process.env.NODE_ENV !== 'development') {
    global.__static = require('path')
        .join(__dirname, '/static')
        .replace(/\\/g, '\\\\'); // eslint-disable-line
}

const devMode = process.env.NODE_ENV === 'development';

let mainWindow;
const winURL = devMode ? 'http://localhost:9080' : `file://${__dirname}/index.html`;

app.setAppUserModelId('com.codegrade.codegrade-fs');

function createWindow() {
    /**
     * Initial window options
     */
    mainWindow = new BrowserWindow({
        height: 700,
        useContentSize: true,
        width: 550,
        icon: path.join(__static, 'icons', 'icon-blue.png'),
        webPreferences: {
            webSecurity: !devMode,
        },
    });

    mainWindow.setMenu(null);

    mainWindow.loadURL(winURL);

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

app.on('ready', createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (mainWindow === null) {
        createWindow();
    }
});

/**
 * Auto Updater
 *
 * Uncomment the following code below and install `electron-updater` to
 * support auto updating. Code Signing with a valid certificate is required.
 * https://simulatedgreg.gitbooks.io/electron-vue/content/en/using-electron-builder.html#auto-updating
 */

/*
import { autoUpdater } from 'electron-updater'

autoUpdater.on('update-downloaded', () => {
  autoUpdater.quitAndInstall()
})

app.on('ready', () => {
  if (!devMode) autoUpdater.checkForUpdates()
})
 */
