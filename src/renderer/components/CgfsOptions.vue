<template>
    <b-form class="cgfs-options" @keyup.ctrl.enter="start">
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
import path from 'path';

import { mapActions, mapGetters } from 'vuex';

import CgfsOption from '@/components/CgfsOption';
import HelpPopover from '@/components/HelpPopover';
import AdvancedCollapse from '@/components/AdvancedCollapse';

export default {
    name: 'cgfs-options',

    props: {
        options: {
            type: Object,
            required: true,
        },
    },

    data() {
        return {
            internalConfig: null,
            errors: {},
        };
    },

    computed: {
        ...mapGetters('Config', ['config']),

        cgfsArgs() {
            const conf = this.internalConfig;
            const args = ['--password', conf.password];

            if (conf.institution === 'custom') {
                args.push('--url', conf.customInstitution);
            } else {
                args.push('--url', conf.institution);
            }

            switch (conf.verbosity) {
                case 'verbose':
                    args.push('--verbose');
                    break;
                case 'quiet':
                    args.push('--quiet');
                    break;
                default:
                    break;
            }

            if (conf.options.assigned) {
                args.push('--assigned-to-me');
            }

            if (!conf.options.latest) {
                args.push('--all-submissions');
            }

            if (!conf.options.revision) {
                args.push('--fixed');
            }

            args.push(conf.username);
            args.push(path.join(conf.mountpoint, 'CodeGrade'));

            return args;
        },
    },

    watch: {
        config(newConfig) {
            if (!newConfig.password) {
                const password = this.internalConfig ? this.internalConfig.pasword : '';
                this.internalConfig = Object.assign({}, this.config, { password });
            } else {
                this.internalConfig = Object.assign({}, this.config);
            }
        },
    },

    mounted() {
        this.initConfig(this.options);
    },

    methods: {
        ...mapActions('Config', ['initConfig', 'writeConfig']),

        start() {
            const args = this.cgfsArgs;

            this.writeConfig({
                config: this.internalConfig,
                options: this.options,
            }).then(
                () => {
                    this.errors = {};
                    this.$emit('start', args);
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
