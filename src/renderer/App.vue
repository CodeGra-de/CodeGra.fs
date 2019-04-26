<template>
    <div id="app" :class="jwtToken ? 'log' : 'options'">
        <b-card no-body>
            <div class="logo">
                <img src="~@/assets/codegrade-fs.png"
                     alt="CodeGrade Filesystem" />
            </div>

            <hr style="margin: 0;" />

            <div v-if="newerVersionAvailable">
                <b-card-body>
                    <b-alert show variant="info" class="version-info">
                        A newer version of the CodeGrade Filesystem is available. Please consider upgrading.
                        You can download the new version at
                        <a target="_blank" href="https://codegra.de/codegra_fs/latest" @click="downloadNewVersion">codegra.de</a>.
                    </b-alert>
                </b-card-body>

                <hr style="margin: 0;" />
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

        this.$http.get('https://codegra.de/.cgfs.json').then(
            ({ data }) => {
                this.newestVersion = data.version;
                updateInstitutions(data.institutions);
            },
        );
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

.logo {
    flex: 0 0 auto;
    margin: 0 auto;
    padding: 1rem;

    img {
        max-height: 8rem;
        max-width: 100%;
    }
}

.version-info {
    margin: 0;
}

.cgfs-log,
.cgfs-options {
    flex: 1 1 100vh;
    width: 100%;
}
</style>
