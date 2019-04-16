import fs from 'then-fs';
import path from 'path';

import OPTIONS from '@/options';

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

function checkDirectory(stat, dir) {
    if (!stat.isDirectory()) {
        throw new Error(`"${dir}" exists but is not a directory.`);
    }
}

function mkdir(dir) {
    return fs.mkdir(dir, {
        recursive: true,
    });
}

function ensureDirectory(dir) {
    return fs
        .stat(dir)
        .then(stat => checkDirectory(stat, dir), () => confirmMkdir(dir).then(mkdir));
}

function ensureValidMountpoint(dir) {
    // Check that argument is a directory that:
    // 1. (on Windows) has no child named "CodeGrade".
    // 2. (on other systems) has no child named "CodeGrade" or has
    //    a child named "CodeGrade" that is an empty directory.
    const mountPoint = path.join(dir, 'CodeGrade');
    return ensureDirectory(dir).then(() =>
        fs.stat(mountPoint).then(
            () => {
                throw new Error(`"${mountPoint}" already exists!`);
            },
            () => mountPoint,
        ),
    );
}

function validateConfig(config, options) {
    const errors = Object.entries(options).reduce((res, [key, spec]) => {
        if (spec.required && !config[key]) {
            res[key] = new Error(`"${spec.label}" is required.`);
        }
        return res;
    }, {});

    if (Object.keys(errors).length) {
        return Promise.reject(errors);
    } else {
        return ensureValidMountpoint(config.mountpoint).catch(err =>
            Promise.reject({ mountpoint: err }),
        );
    }
}

function getDefaultConfig() {
    const config = {};

    for (const [key, option] of Object.entries(OPTIONS)) {
        const value = option.default;

        if (value instanceof Object) {
            config[key] = Object.assign({}, value);
        } else {
            config[key] = value;
        }
    }

    return config;
}

const getters = {
    config(state) {
        return state.config;
    },
};

const mutations = {
    SET_CONFIG(state, config) {
        state.config = Object.assign({}, config);
    },
};

const actions = {
    writeConfig({ commit }, config) {
        return validateConfig(config, OPTIONS).then(
            () => commit('SET_CONFIG', config),
        );
    },

    clearPassword({ commit, state }) {
        const config = Object.assign({}, state.config, {
            password: '',
        });

        return commit('SET_CONFIG', config);
    },
};

const state = {
    config: getDefaultConfig(),
};

export default {
    state,
    mutations,
    actions,
    getters,
    namespaced: true,
};
