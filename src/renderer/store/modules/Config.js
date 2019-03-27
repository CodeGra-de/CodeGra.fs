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
    return fs.stat(dir).then(
        stat => checkDirectory(stat, dir),
        () => mkdir(path.dirname(dir))
            .then(() => fs.mkdir(dir)),
    );
}

function ensureDirectory(dir) {
    return fs.stat(dir).then(
        stat => checkDirectory(stat, dir),
        () => confirmMkdir(dir).then(mkdir),
    ).then(() => dir);
}

function ensureOptionValid(config, option) {
    if (option.required && !config[option.key]) {
        return new Error(`"${option.label}" is required.`);
    }

    return null;
}

function ensureConfigValid(config, options) {
    const errors = options
        .map(option => ensureOptionValid(config, option))
        .filter(err => err);

    if (errors.length) {
        return Promise.reject(errors);
    } else {
        return ensureDirectory(config.mountpoint);
    }
}

const getters = {
    config(state) {
        return state.config;
    },
};

const mutations = {
    SET_CONFIG(state, config) {
        state.config = Object.assign({}, config, {
            password: '',
        });
    },
};

const actions = {
    initConfig({ commit, state }, options) {
        const config = Object.assign({}, state.config);

        for (const option of options) {
            if (config[option.key] == null) {
                config[option.key] = option.default || '';
            }
        }

        if (process.env.NODE_ENV === 'development') {
            // Default to localhost:8080 route.
            config[options[0].key] = options[0].options[0].value;
        }

        return commit('SET_CONFIG', config);
    },

    writeConfig({ commit }, { config, options }) {
        return ensureConfigValid(config, options).then(
            () => commit('SET_CONFIG', config),
        );
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
