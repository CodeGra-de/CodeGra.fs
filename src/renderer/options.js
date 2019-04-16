import os from 'os';
import path from 'path';

const OPTIONS = {
    institution: {
        label: 'Institution',
        required: true,
        type: 'select',
        default: '',
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
                text: 'Other',
                value: 'custom',
            },
        ],
        help: 'Choose your institution.',
    },
    customInstitution: {
        label: 'Custom CodeGrade URL',
        required: false,
        type: 'text',
        default: '',
        help: 'URL to the CodeGrade API. Should start with "https://" and end in "/api/v1/".',
    },
    username: {
        label: 'Username',
        required: true,
        type: 'text',
        default: '',
        help:
            "Your CodeGrade username. If you don't know your username, you can find it on the profile page.",
    },
    password: {
        label: 'Password',
        required: true,
        type: 'password',
        default: '',
        help:
            "Your CodeGrade password. If you don't have a password, you can set one on the profile page.",
    },
    mountpoint: {
        label: 'Location',
        required: true,
        type: 'directory',
        default: path.join(os.homedir(), 'Desktop'),
        help:
            'Location of the CodeGrade Filesystem folder. This should be a directory that has no children called "CodeGrade".',
    },
    options: {
        label: 'Options',
        required: false,
        type: 'checkbox',
        default: {
            revision: false,
            assigned: true,
            latest: true,
        },
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
        default: 'normal',
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
};

if (process.env.NODE_ENV === 'development') {
    OPTIONS.institution.options.unshift({
        text: 'Development (localhost:5000)',
        value: 'http://localhost:5000/api/v1/',
    });
}

export default OPTIONS;
