import fs from 'then-fs';
import path from 'path';

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
    initConfig({ commit, state }, options) {
        const config = Object.assign({}, state.config);

        for (const key in options) {
            if (config[key] == null) {
                config[key] = options[key].default || '';
            }
        }

        return commit('SET_CONFIG', config);
    },

    writeConfig({ commit }, { config, options }) {
        return validateConfig(config, options).then(() => commit('SET_CONFIG', config));
    },

    clearPassword({ commit, state }) {
        const config = Object.assign({}, state.config, {
            password: '',
        });

        return commit('SET_CONFIG', config);
    },
};

export default {
    state: {
        config: {},
    },
    mutations,
    actions,
    getters,
    namespaced: true,
};
