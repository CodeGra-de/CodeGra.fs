<template>
    <div id="app" class="container-fluid">
        <img class="logo" src="~@/assets/codegrade-fs.png" alt="CodeGrade Filesystem" />

        <cgfs-options v-if="args == null" :options="options" @start="start" />
        <cgfs-log
            v-else
            :args="args"
            :password="password"
            @clear-password="password = ''"
            @stop="stop"
        />
    </div>
</template>

<script>
import os from 'os';
import path from 'path';

import CgfsLog from '@/components/CgfsLog';
import CgfsOptions from '@/components/CgfsOptions';

export default {
    name: 'codegrade-fs',

    data() {
        const options = {
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
                default: path.join(os.homedir(), 'Desktop'),
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
                        default: false,
                        // TODO: Fix help
                        help:
                            'Enter "revision" mode, in which the teacher can add/edit/delete student files. The student will be able to see the edits made by the teacher. When this option is turned off, files cannot be changed or deleted. New files can still be added, however they will **NOT** be synced with the CodeGrade server.',
                    },
                    {
                        key: 'assigned',
                        label: 'Assigned to me',
                        default: true,
                        help:
                            'Only show submissions that are assigned to you. This only has effect if submissions are assigned and you are one of the assignees.',
                    },
                    {
                        key: 'latest',
                        label: 'Latest only',
                        default: true,
                        help:
                            'Show only the most recent submissions of each student, rather than all submissions.',
                    },
                ],
                default: {},
            },
            verbosity: {
                label: 'Verbosity',
                required: false,
                type: 'radio',
                options: [
                    {
                        label: 'Quiet',
                        value: 'quiet',
                    },
                    {
                        label: 'Normal',
                        value: 'normal',
                    },
                    {
                        label: 'Verbose',
                        value: 'verbose',
                    },
                ],
                default: 'quiet',
            },
        };

        if (process.env.NODE_ENV === 'development') {
            options.institution.options.unshift({
                text: 'Development (localhost:8080)',
                value: 'http://localhost:8080/api/v1/',
            });
        }

        return {
            options,
            args: null,
            password: '',
        };
    },

    mounted() {
        let popoverVisible = false;

        this.$root.$on('bv::popover::shown', () => {
            popoverVisible = true;
        });

        this.$root.$on('bv::popover::hidden', () => {
            popoverVisible = false;
        });

        document.addEventListener(
            'click',
            event => {
                if (!event.target.closest('.popover-body') && popoverVisible) {
                    this.$root.$emit('bv::hide::popover');
                }
            },
            true,
        );
    },

    methods: {
        start({ args, password }) {
            this.args = args;
            this.password = password;
        },

        stop() {
            this.args = null;
            this.password = '';
        },
    },

    components: {
        CgfsLog,
        CgfsOptions,
    },
};
</script>

<style lang="css" scoped>
#app {
    display: flex;
    flex-direction: column;
    height: 100vh;
    padding: 15px;
}

.logo {
    flex: 0 0 auto;
    width: 100%;
    max-width: 550px;
    margin: 0 auto 1rem;
    font-weight: 300;
}

.cgfs-log,
.cgfs-options {
    flex: 1 1 auto;
}
</style>
