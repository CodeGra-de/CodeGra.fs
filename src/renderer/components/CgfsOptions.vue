<template>
    <b-form v-if="internalConfig" class="cgfs-options" @keyup.enter="start">
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

        <advanced-collapse>
            <cgfs-option
                v-model="internalConfig.mountpoint"
                :option="OPTIONS.mountpoint"
                :error="errors.mountpoint"
            />

            <cgfs-option v-model="internalConfig.options" :option="OPTIONS.options" />

            <cgfs-option v-model="internalConfig.verbosity" :option="OPTIONS.verbosity" />
        </advanced-collapse>

        <b-button class="start-button" variant="primary" @click="start">
            Start
        </b-button>
    </b-form>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';

import OPTIONS from '@/options';

import CgfsOption from '@/components/CgfsOption';
import HelpPopover from '@/components/HelpPopover';
import AdvancedCollapse from '@/components/AdvancedCollapse';

export default {
    name: 'cgfs-options',

    data() {
        return {
            OPTIONS,
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
                        this.errors = err;
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
