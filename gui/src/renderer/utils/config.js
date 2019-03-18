import fs from 'fs';
import path from 'path';

import xdg from 'xdg-basedir';

function ensureDirectory(dir) {
    try {
        fs.accessSync(dir);
    } catch (e) {
        try {
            fs.mkdirSync(dir);
        } catch (e) {
            return null;
        }
    }

    return dir;
}

function getConfigPath() {
    if (xdg.data == null) {
        return null;
    }

    const configDir = path.join(xdg.data, 'codegrade-fs');

    if (!ensureDirectory(configDir)) {
        return null;
    }

    return path.join(configDir, 'config.json');
}

export function readConfig() {
    const configPath = getConfigPath();

    if (configPath == null) {
        return {};
    }

    try {
        const data = fs.readFileSync(configPath);
        return JSON.parse(data);
    } catch (e) {
        return {};
    }
}

export function writeConfig(config) {
    const configPath = getConfigPath();

    if (configPath == null) {
        console.warn('Could not write configuration');
        return;
    }

    config = Object.assign({}, config);
    delete config.Password;

    try {
        const data = JSON.stringify(config);
        fs.writeFileSync(configPath, data);
    } catch (e) {
        // Do nothing
    }
}
