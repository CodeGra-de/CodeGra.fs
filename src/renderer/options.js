import os from 'os';
import path from 'path';

const OPTIONS = {
    institution: {
        label: 'Institution',
        required: true,
        type: 'select',
        default: 'default',
        options: [
            {
                text: 'Choose your institution',
                value: 'default',
                disabled: true,
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
        placeholder: 'Institution',
        prepend: 'https://',
        append: '.codegra.de',
        help: 'Subdomain of your institution.',
    },
    username: {
        label: 'Username',
        required: true,
        type: 'text',
        default: '',
        placeholder: 'Username',
        help:
            "Your CodeGrade username. If you don't know your username, you can find it on the profile page.",
    },
    password: {
        label: 'Password',
        required: true,
        type: 'password',
        default: '',
        placeholder: 'Password',
        help:
            "Your CodeGrade password. If you don't have a password, you can set one on the profile page.",
    },
    mountpoint: {
        label: 'Location',
        required: true,
        type: 'directory',
        default: path.join(os.homedir(), 'Desktop'),
        help:
            'Location of the CodeGrade Filesystem folder. This should be a directory that does not contain a directory named "CodeGrade".',
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
                label: 'Revision mode',
                help:
                    'Enter revision mode. In revision mode the teacher can add, edit, and delete student files. The student will be able to see the edits made by the teacher. When this option is turned off, files cannot be changed or deleted. New files can still be added, but they will **NOT** be synced with the CodeGrade server and will be lost once the filesystem shuts down..',
            },
            {
                key: 'assigned',
                label: 'Assigned to me',
                help:
                    'Only show submissions that are assigned to you. This only has effect if submissions are assigned and you are one of the assignees.',
            },
            {
                key: 'latest',
                label: 'Latest submissions only',
                help:
                    'Show only the most recent submissions of each student, rather than all their submissions.',
            },
        ],
    },
    verbosity: {
        label: 'Notifications',
        required: false,
        type: 'radio',
        default: 'normal',
        options: [
            {
                label: 'Critical only',
                value: 'quiet',
                help: 'Hide most notifications. Errors and warnings will still be shown.',
            },
            {
                label: 'All',
                value: 'normal',
                help: 'Show notifications for errors and warnings.',
            },
            {
                label: 'Debug',
                value: 'verbose',
                help:
                    'Show notifications for errors and warnings, and log all messages. This option should generally not be selected.',
            },
        ],
    },
};

export default OPTIONS;

export function updateInstitutions(institutions) {
    if (process.env.NODE_ENV === 'development') {
        institutions.unshift({
            text: 'Development (localhost:5000)',
            value: 'http://localhost:5000/api/v1',
        });
    }

    OPTIONS.institution.options.splice(1, 0, ...institutions);
}
