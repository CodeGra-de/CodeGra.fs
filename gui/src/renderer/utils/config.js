import path from 'path';

import fs from 'then-fs';
import xdg from 'xdg-basedir';

function checkDirectory(stat, dir) {
    if (!stat.isDirectory()) {
        throw new Error(`"${dir}" exists but is not a directory.`);
    }
}

function confirmMkdir(dir) {
    const msg = `
The directory "${dir}" does not exist.
Would you like to create it now?
    `;

    return new Promise((resolve, reject) => {
        if (window.confirm(msg)) {
            resolve(dir);
        } else {
            reject();
        }
    });
}

function mkdir(dir) {
    return fs.stat(dir).then(
        stat => checkDirectory(stat, dir),
        () => mkdir(path.dirname(dir))
            .then(() => fs.mkdir(dir)),
    );
}

export function ensureDirectory(dir, prompt = false) {
    return fs.stat(dir).then(
        stat => checkDirectory(stat, dir),
        () => {
            let p;

            if (prompt) {
                p = confirmMkdir(dir);
            } else {
                p = Promise.resolve(dir);
            }

            return p.then(mkdir);
        },
    ).then(() => dir);
}

export function getConfigDir() {
    return new Promise((resolve, reject) => {
        if (xdg.data == null) {
            reject(new Error('No data home detected.'));
        } else {
            resolve(path.join(xdg.data, 'codegrade-fs'));
        }
    });
}

export function getConfigPath() {
    return getConfigDir()
        .then(ensureDirectory)
        .then(dir => path.join(dir, 'config.json'));
}

export function readConfig() {
    return getConfigPath()
        .then(fs.readFile)
        .then(JSON.parse);
}

export function writeConfig(config) {
    return getConfigPath().then(configPath => {
        const copy = Object.assign({}, config);
        delete copy.Password;

        const data = JSON.stringify(copy);
        return fs.writeFile(configPath, data);
    });
}
