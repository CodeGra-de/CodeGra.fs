import fs from 'then-fs';
import os from 'os';
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

    options(state) {
        return state.options;
    },
};

const mutations = {
    SET_CONFIG(state, config) {
        state.config = Object.assign({}, config);
    },
};

const actions = {
    writeConfig({ commit, state }, { config }) {
        return validateConfig(config, state.options).then(() => commit('SET_CONFIG', config));
    },

    clearPassword({ commit, state }) {
        const config = Object.assign({}, state.config, {
            password: '',
        });

        return commit('SET_CONFIG', config);
    },
};

const state = {
    config: {
        institution: '',
        username: '',
        password: '',
        mountpoint: path.join(os.homedir(), 'Desktop'),
        options: {
            revision: false,
            assigned: true,
            latest: true,
        },
        verbosity: 'normal',
    },
    options: {
        institution: {
            label: 'Institution',
            required: true,
            type: 'select',
            options: [
                {
                    text: 'Amsterdam UMC (amc.codegra.de)',
                    value: 'https://amc.codegra.de/api/v1/',
                },
                {
                    text: 'Erasmus Universiteit Rotterdam (eur.codegra.de)',
                    value: 'https://eur.codegra.de/api/v1/',
                },
                {
                    text: 'Universiteit Twente (ut.codegra.de)',
                    value: 'https://ut.codegra.de/api/v1/',
                },
                {
                    text: 'Universiteit van Amsterdam (uva.codegra.de)',
                    value: 'https://uva.codegra.de/api/v1/',
                },
                {
                    text: 'Custom',
                    value: 'custom',
                },
            ],
            help: 'Choose your institution.',
        },
        customInstitution: {
            label: 'Custom CodeGrade URL',
            required: false,
            type: 'text',
            help:
                'URL to the CodeGrade API. Should start with "https://" and end in "/api/v1/".',
        },
        username: {
            label: 'Username',
            required: true,
            type: 'text',
            help:
                "Your CodeGrade username. If you don't know your username, you can find it on the profile page.",
        },
        password: {
            label: 'Password',
            required: true,
            type: 'password',
            help:
                "Your CodeGrade password. If you don't have a password, you can set one on the profile page.",
        },
        mountpoint: {
            label: 'Location',
            required: true,
            type: 'directory',
            help:
                'Location of the CodeGrade Filesystem folder. This should be a directory that has no children called "CodeGrade".',
        },
        options: {
            label: 'Options',
            required: false,
            type: 'checkbox',
            options: [
                {
                    key: 'revision',
                    label: 'Revision',
                    // TODO: Fix help
                    help:
                        'Enter "revision" mode, in which the teacher can add/edit/delete student files. The student will be able to see the edits made by the teacher. When this option is turned off, files cannot be changed or deleted. New files can still be added, however they will **NOT** be synced with the CodeGrade server.',
                },
                {
                    key: 'assigned',
                    label: 'Assigned to me',
                    help:
                        'Only show submissions that are assigned to you. This only has effect if submissions are assigned and you are one of the assignees.',
                },
                {
                    key: 'latest',
                    label: 'Latest only',
                    help:
                        'Show only the most recent submissions of each student, rather than all submissions.',
                },
            ],
        },
        verbosity: {
            label: 'Verbosity',
            required: false,
            type: 'radio',
            options: [
                {
                    label: 'Quiet',
                    value: 'quiet',
                    help: 'Do not show notifications. Errors and warnings will still be logged.',
                },
                {
                    label: 'Normal',
                    value: 'normal',
                    help: 'Show notifications for errors and warnings.',
                },
                {
                    label: 'Verbose',
                    value: 'verbose',
                    help: 'Show notifications for errors and warnings, and log all messages.',
                },
            ],
        },
    },
};

if (process.env.NODE_ENV === 'development') {
    state.options.institution.options.unshift({
        text: 'Development (localhost:8080)',
        value: 'http://localhost:8080/api/v1/',
    });
}

export default {
    state,
    mutations,
    actions,
    getters,
    namespaced: true,
};
