<template>
    <b-form v-if="internalConfig" class="cgfs-options" @keyup.enter="start">
        <b-card>
            <cgfs-logo/>

            <hr>

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
                * indicates a required field
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

            <div slot="footer">
                <b-button class="start-button" variant="primary" @click="start">
                    Start
                </b-button>
            </div>
        </b-card>
    </b-form>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';

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
            handler() {
                this.internalConfig = Object.assign({}, this.config);
                this.internalConfig.options = Object.assign({}, this.config.options);
            },
            immediate: true,
        },
    },

    mounted() {
        this.showAdvanced = (
            this.config.mountpoint !== OPTIONS.mountpoint.default ||
            this.config.verbosity !== OPTIONS.verbosity.default ||
            !isEqual(this.config.options, OPTIONS.options.default)
        );
    },

    methods: {
        ...mapActions('Config', ['writeConfig', 'clearPassword']),

        start() {
            this
                .writeConfig(this.internalConfig)
                .then(
                    () => this.$http.post(
                        `${this.getInstitutionURL()}/login`,
                        {
                            username: this.internalConfig.username,
                            password: this.internalConfig.password,
                        },
                    ),
                )
                .then(response => {
                    if (!this.$devMode) {
                        return this.clearPassword().then(() => response);
                    }
                    return response;
                })
                .then(
                    response => {
                        this.errors = {};
                        this.$emit('start', response.data.access_token);
                    },
                    err => {
                        if (err.response && err.response.data) {
                            this.errors = {
                                password: new Error(err.response.data.message),
                            };
                        } else {
                            this.errors = err;
                        }
                    },
                );
        },

        getInstitutionURL() {
            if (this.internalConfig.institution === 'custom') {
                return this.internalConfig.customInstitution;
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
    },
};
</script>

<style lang="scss" scoped>
.cgfs-option:last-child {
    margin-bottom: 0;
}

.required-desc {
    float: right;
    cursor: default;
}

.start-button {
    float: right;
}
</style>
