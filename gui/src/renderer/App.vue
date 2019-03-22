<template>
<div id="app" class="container-fluid">
    <img class="logo"
         src="~@/assets/codegrade-fs.png"
         alt="CodeGrade Filesystem"/>

    <cgfs-options v-if="config == null"
                  :options="options"
                  @start="start"/>
    <cgfs-log v-else
              :config="config"
              @stop="stop"/>
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
        const options = [
            {
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
                ],
                help: 'Choose your institution.',
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
                default: path.join(os.homedir(), 'Desktop', 'CodeGrade'),
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

        if (process.env.NODE_ENV === 'development') {
            options[0].options.unshift({
                text: 'Development (localhost:8080)',
                value: 'http://localhost:8080/api/v1/',
            });
        }

        return {
            options,
            config: null,
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

        document.addEventListener('click', event => {
            if (!event.target.closest('.popover-body') && popoverVisible) {
                this.$root.$emit('bv::hide::popover');
            }
        }, true);
    },

    methods: {
        start(config) {
            this.config = config;
        },

        stop() {
            this.config = null;
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
    max-width: 512px;
    margin: 0 auto 1rem;
    font-weight: 300;
}

.cgfs-log,
.cgfs-options {
    flex: 1 1 auto;
}
</style>
