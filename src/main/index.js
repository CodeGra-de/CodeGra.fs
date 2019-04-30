import path from 'path';
import { app, BrowserWindow, ipcMain, Notification } from 'electron'; // eslint-disable-line
import notifier from 'node-notifier';

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

if (!devMode && process.platform === 'darwin') {
    process.env.PATH = `/usr/local/bin:${process.env.PATH}`;
}

let mainWindow;
const winURL = devMode ? 'http://localhost:9080' : `file://${__dirname}/index.html`;

const appID = 'com.codegrade.codegrade-fs';
const title = 'CodeGrade Filesystem';
const icon = path.join(__static, 'icons', '512x512.png');

app.setAppUserModelId(appID);

function notify(event, message) {
    if (process.platform === 'darwin') {
        new Notification({
            title,
            body: message,
            icon,
        }).show();
    } else {
        notifier.notify(
            {
                title,
                message,
                appID,
                icon,
            },
            err => {
                if (err) {
                    mainWindow.flashFrame(true);
                }
            },
        );
    }
}

function createWindow() {
    /**
     * Initial window options
     */
    mainWindow = new BrowserWindow({
        title,
        width: 550,
        height: 700,
        minWidth: 550,
        minHeight: 550,
        useContentSize: true,
        icon:
            process.platform === 'win32' ? path.join(__static, 'icons', 'ms-icon-blue.ico') : icon,
        webPreferences: {
            webSecurity: !devMode,
        },
    });

    mainWindow.setMenu(null);

    mainWindow.loadURL(winURL);

    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    ipcMain.on('cgfs-notify', notify);
}

app.on('ready', createWindow);

app.on('window-all-closed', () => {
    app.quit();
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
