<template>
    <div id="app" :class="jwtToken ? 'log' : 'options'">
        <b-card no-body>
            <b-card-body class="logo">
                <img src="~@/assets/codegrade-fs.png" alt="CodeGrade Filesystem" />
            </b-card-body>

            <div v-if="newerVersionAvailable">
                <b-card-body class="version-info">
                    <b-alert show variant="info">
                        A newer version of the CodeGrade Filesystem is available. You can download
                        the latest version at
                        <a
                            target="_blank"
                            href="https://codegra.de/codegra_fs/latest"
                            @click="downloadNewVersion"
                        >
                            codegra.de/codegra_fs/latest</a
                        >.
                        <template v-if="jwtToken">
                            Make sure to stop the filesystem before upgrading.
                        </template>
                    </b-alert>
                </b-card-body>
            </div>

            <cgfs-log v-if="jwtToken" @stop="jwtToken = ''" :jwt-token="jwtToken" />
            <cgfs-options v-else @start="jwtToken = $event" />
        </b-card>
    </div>
</template>

<script>
// eslint-disable-next-line
import { shell } from 'electron';

import { updateInstitutions } from '@/options';

import CgfsLog from '@/components/CgfsLog';
import CgfsOptions from '@/components/CgfsOptions';

export default {
    name: 'codegrade-fs',

    data() {
        return {
            newestVersion: null,
            jwtToken: '',
        };
    },

    computed: {
        newerVersionAvailable() {
            if (this.newestVersion === null) {
                return false;
            }
            const [major, minor, patch] = __VERSION__.split('.');
            const [newMajor, newMinor, newPatch] = this.newestVersion;
            if (newMajor === major) {
                if (newMinor === minor) {
                    return newPatch > patch;
                } else {
                    return newMinor > minor;
                }
            } else {
                return newMajor > major;
            }
        },
    },

    methods: {
        downloadNewVersion(event) {
            if (event.target.closest('[target="_blank"]')) {
                event.preventDefault();
                shell.openExternal(event.target.href);
            }
        },
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

        this.$http.get('https://codegra.de/.cgfs.json').then(({ data }) => {
            this.newestVersion = data.version;
            updateInstitutions(data.institutions);
        });
    },

    components: {
        CgfsLog,
        CgfsOptions,
    },
};
</script>

<style lang="scss" scoped>
@import '@/_mixins.scss';

#app {
    display: flex;
    flex-direction: column;
    height: 100vh;
    margin: 0 auto;
    padding: $spacer;

    &.log {
        max-width: $log-width;
    }

    &.options {
        max-width: $options-width;
    }
}

.logo,
.version-info {
    border-bottom: $border-width solid $border-color;
}

.logo {
    flex: 0 0 auto;

    img {
        display: block;
        max-height: 8rem;
        max-width: 100%;
        margin: 0 auto;
    }
}

.version-info .alert {
    margin: 0;
}

.cgfs-log,
.cgfs-options {
    flex: 1 1 100vh;
    width: 100%;
}
</style>
