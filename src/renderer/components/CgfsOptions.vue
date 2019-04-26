<template>
    <b-form v-if="internalConfig" class="cgfs-options" @keyup.enter="start">
        <b-card-body>
            <cgfs-option
                v-model="internalConfig.institution"
                :option="OPTIONS.institution"
                :error="errors.institution"
            />

            <cgfs-option
                v-if="internalConfig.institution === 'custom'"
                v-model="internalConfig.customInstitution"
                :option="OPTIONS.customInstitution"
                :error="errors.customInstitution"
            />

            <cgfs-option
                v-model="internalConfig.username"
                :option="OPTIONS.username"
                :error="errors.username"
            />

            <cgfs-option
                v-model="internalConfig.password"
                :option="OPTIONS.password"
                :error="errors.password"
            />

            <div class="required-desc text-muted font-italic">
                <span class="text-primary">*</span> indicates a required field
            </div>

            <advanced-collapse :value="showAdvanced">
                <cgfs-option
                    v-model="internalConfig.mountpoint"
                    :option="OPTIONS.mountpoint"
                    :error="errors.mountpoint"
                />

                <cgfs-option v-model="internalConfig.options" :option="OPTIONS.options" />

                <cgfs-option v-model="internalConfig.verbosity" :option="OPTIONS.verbosity" />
            </advanced-collapse>

            <b-alert v-if="errors && errors.network" show variant="danger">
                {{ errors.network.message }}
            </b-alert>
        </b-card-body>

        <b-card-footer>
            <b-button variant="outline-primary" v-b-modal.help-modal>
                Help
            </b-button>

            <b-button class="start-button" variant="primary" @click="start">
                Start
            </b-button>
        </b-card-footer>

        <b-modal
            lazy
            hide-footer
            id="help-modal"
            size="xl"
            title="CodeGrade Filesystem Documentation"
        >
            <webview src="https://fs-docs.codegra.de/" />
        </b-modal>
    </b-form>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/times';

import { isEqual } from '@/utils';
import OPTIONS from '@/options';

import CgfsLogo from '@/components/CgfsLogo';
import CgfsOption from '@/components/CgfsOption';
import HelpPopover from '@/components/HelpPopover';
import AdvancedCollapse from '@/components/AdvancedCollapse';

export default {
    name: 'cgfs-options',

    data() {
        return {
            console,
            OPTIONS,
            showAdvanced: false,
            internalConfig: null,
            errors: {},
        };
    },

    computed: {
        ...mapGetters('Config', ['config']),
    },

    watch: {
        config: {
            handler(config) {
                this.internalConfig = Object.assign({}, config);
                this.internalConfig.options = Object.assign({}, config.options);
            },
            immediate: true,
        },
    },

    mounted() {
        this.showAdvanced =
            this.config.mountpoint !== OPTIONS.mountpoint.default ||
            this.config.verbosity !== OPTIONS.verbosity.default ||
            !isEqual(this.config.options, OPTIONS.options.default);
    },

    methods: {
        ...mapActions('Config', ['writeConfig']),

        start() {
            const { username, password } = this.internalConfig;

            this.writeConfig(this.internalConfig)
                .then(() =>
                    this.$http.post(`${this.getInstitutionURL()}/login`, { username, password }),
                )
                .then(
                    response => {
                        this.errors = {};
                        this.$emit('start', response.data.access_token);
                    },
                    err => {
                        if (err.request) {
                            if (err.response && err.response.data) {
                                this.errors = {
                                    password: new Error(err.response.data.message),
                                };
                            } else {
                                this.errors = {
                                    network: new Error(err.message),
                                };
                            }
                        } else {
                            this.errors = err;
                        }
                    },
                );
        },

        getInstitutionURL() {
            if (this.internalConfig.institution === 'custom') {
                return `https://${this.internalConfig.customInstitution}.codegra.de/api/v1/`;
            } else {
                return this.internalConfig.institution;
            }
        },
    },

    components: {
        CgfsLogo,
        CgfsOption,
        HelpPopover,
        AdvancedCollapse,
        Icon,
    },
};
</script>

<style lang="scss" scoped>
.cgfs-options {
    display: flex;
    flex-direction: column;
}

.card-body {
    overflow: auto;
}

.cgfs-option:last-child {
    margin-bottom: 0;
}

.required-desc {
    float: right;
}

.alert {
    margin-top: 1rem;
    margin-bottom: 0;
}

.start-button {
    float: right;
}
</style>

<style lang="scss">
@import '@/_mixins.scss';

.cgfs-options {
    .col-form-label,
    .required-desc,
    .advanced-collapse {
        user-select: none;
        cursor: default;
    }

    .modal-dialog {
        height: calc(100vh - 2 * #{$spacer});
        width: calc(100vw - 2 * #{$spacer});
        max-width: initial;
        margin: $spacer;
    }

    .modal-content {
        height: 100%;
    }

    .modal-body {
        position: relative;
        display: flex;
        flex-direction: column;
        padding: 0;
    }

    webview {
        flex: 1 1 auto;
    }
}
</style>
