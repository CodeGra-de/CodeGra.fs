<template>
    <b-form v-if="internalConfig" class="cgfs-options" @keyup.ctrl.enter="start">
        <cgfs-option
            v-model="internalConfig.institution"
            :option="options.institution"
            :error="errors.institution"
        />

        <cgfs-option
            v-if="internalConfig.institution === 'custom'"
            v-model="internalConfig.customInstitution"
            :option="options.customInstitution"
            :error="errors.customInstitution"
        />

        <cgfs-option
            v-model="internalConfig.username"
            :option="options.username"
            :error="errors.username"
        />

        <cgfs-option
            v-model="internalConfig.password"
            :option="options.password"
            :error="errors.password"
        />

        <cgfs-option
            v-model="internalConfig.mountpoint"
            :option="options.mountpoint"
            :error="errors.mountpoint"
        />

        <div class="required-desc text-muted font-italic">
            * indicates a required field
        </div>

        <advanced-collapse>
            <cgfs-option v-model="internalConfig.options" :option="options.options" />

            <cgfs-option v-model="internalConfig.verbosity" :option="options.verbosity" />
        </advanced-collapse>

        <b-button class="start-button" variant="primary" @click="start">
            Start
        </b-button>
    </b-form>
</template>

<script>
import os from 'os';
import path from 'path';

import { mapActions, mapGetters } from 'vuex';

import CgfsOption from '@/components/CgfsOption';
import HelpPopover from '@/components/HelpPopover';
import AdvancedCollapse from '@/components/AdvancedCollapse';

export default {
    name: 'cgfs-options',

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
            internalConfig: null,
            errors: {},
        };
    },

    computed: {
        ...mapGetters('Config', ['config']),
    },

    watch: {
        config() {
            this.internalConfig = Object.assign({}, this.config);
        },
    },

    mounted() {
        this.initConfig(this.options);
    },

    methods: {
        ...mapActions('Config', ['initConfig', 'writeConfig']),

        start() {
            this.writeConfig({
                config: this.internalConfig,
                options: this.options,
            }).then(
                () => {
                    this.errors = {};
                    this.$emit('start');
                },
                err => {
                    this.errors = err;
                },
            );
        },
    },

    components: {
        CgfsOption,
        HelpPopover,
        AdvancedCollapse,
    },
};
</script>

<style lang="css" scoped>
.cgfs-options {
    width: 100%;
    max-width: 550px;
    margin: 0 auto;
}

.required-desc {
    float: right;
    cursor: default;
}

.start-button {
    float: right;
    margin-bottom: 1rem;
}
</style>

<style lang="css">
.form-control.custom-control {
    padding-left: 2rem;
}

.form-control.custom-control label {
    display: block;
}
</style>
