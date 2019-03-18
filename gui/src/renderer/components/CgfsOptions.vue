<template>
<div class="cgfs-options">
    <cgfs-option v-for="option in optionData"
                 v-model="config[option.label]"
                 :option="option"
                 :key="option.label"
                 @keydown.ctrl.enter="mount"/>

    <p class="clearfix text-muted font-italic">
        <b-button variant="primary"
                  class="mount-button"
                  @click="mount">
            Mount
        </b-button>

        * indicates a required field
    </p>

    <b-alert v-if="errors.length > 0"
             variant="danger"
             show>
        <ul class="errors">
            <li v-for="error in errors">
                {{ error }}
            </li>
        </ul>
    </b-alert>
</div>
</template>

<script>
import { readConfig, writeConfig } from '@/utils/config';
import CgfsOption from '@/components/CgfsOption';

export default {
    name: 'cgfs-options',

    data() {
        const optionData = [
            {
                label: 'Institution',
                required: true,
                type: 'select',
                options: [
                    {
                        text: 'Amsterdam UMC (amc.codegra.de)',
                        value: 'https://amc.codegra.de/api/v1',
                    },
                    {
                        text: 'Erasmus Universiteit Rotterdam (eur.codegra.de)',
                        value: 'https://eur.codegra.de/api/v1',
                    },
                    {
                        text: 'Universiteit Twente (ut.codegra.de)',
                        value: 'https://ut.codegra.de/api/v1',
                    },
                    {
                        text: 'Universiteit van Amsterdam (uva.codegra.de)',
                        value: 'https://uva.codegra.de/api/v1',
                    },
                ],
                help: 'Choose your institution from the list below.',
            },
            {
                label: 'Username',
                required: true,
                type: 'text',
                help: 'Your CodeGrade username.',
            },
            {
                label: 'Password',
                required: true,
                type: 'password',
                help: 'Your CodeGrade password.',
            },
            {
                label: 'Mount point',
                required: true,
                type: 'directory',
                help: 'Mountpoint for the file system. This should be an existing empty directory.',
            },
            {
                label: 'Options',
                required: false,
                type: 'checkbox',
                options: [
                    {
                        label: 'Revision',
                        default: false,
                        // TODO: Fix help
                        help: 'Mount the original files as read only. It is still possible to create new files, but it is not possible to alter or delete existing files. The files shown are always the student revision files. The created new files are only visible during a single session, they are **NOT** uploaded to the server.',
                    },
                    {
                        label: 'Assigned',
                        default: true,
                        help: 'Only show submissions that are assigned to you. This only has effect if submissions are assigned and you are one of the assignees.',
                    },
                    {
                        label: 'Latest',
                        default: true,
                        // TODO: Fix help
                        help: 'See all submissions not just the latest submissions of students.',
                    },
                ],
            },
            {
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
        ];

        const config = readConfig();
        for (const option of optionData) {
            if (config[option.label] == null) {
                config[option.label] = option.default || '';
            }
        }

        return {
            config,
            optionData,
            errors: [],
        };
    },

    methods: {
        mount() {
            const config = this.config;
            this.errors = [];

            for (const option of this.optionData) {
                if (option.required && !config[option.label]) {
                    this.errors.push(`Option "${option.label}" is required.`);
                }
            }

            if (this.errors.length === 0) {
                writeConfig(this.config);
                this.$emit('mount', this.config);
            }
        },
    },

    components: {
        CgfsOption,
    },
};
</script>

<style lang="css" scoped>
.clearfix::after {
    content: '';
    display: block;
    height: 0;
    clear: both;
}

.errors {
    margin-bottom: 0;
    padding-left: 1rem;
}

.mount-button {
    float: right;
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
