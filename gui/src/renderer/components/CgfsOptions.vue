<template>
<div class="cgfs-options">
    <cgfs-option v-if="internalConfig != null"
                 v-for="option in options"
                 :key="option.key"
                 v-model="internalConfig[option.key]"
                 :option="option"
                 @keydown.ctrl.enter="start"/>

    <p class="clearfix text-muted font-italic">
        <b-button variant="primary"
                  class="start-button"
                  @click="start">
            Start
        </b-button>

        * indicates a required field
    </p>

    <b-alert v-if="errors.length > 0"
             variant="danger"
             show>
        <ul class="errors">
            <li v-for="error, i in errors" :key="i">
                {{ error }}
            </li>
        </ul>
    </b-alert>
</div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';

import CgfsOption from '@/components/CgfsOption';

export default {
    name: 'cgfs-options',

    props: {
        options: {
            type: Array,
            required: true,
        },
    },

    data() {
        return {
            internalConfig: null,
            errors: [],
        };
    },

    computed: {
        ...mapGetters('Config', ['config']),

        cgfsArgs() {
            const conf = this.internalConfig;
            const args = [
                '--url', conf.institution,
                '--password', conf.password,
            ];

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
            args.push(conf.mountpoint);

            return args;
        },
    },

    watch: {
        config() {
            const password = this.internalConfig ? this.internalConfig.pasword : '';
            this.internalConfig = Object.assign({}, this.config, { password });
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
                () => this.$emit('start', this.cgfsArgs),
                err => {
                    this.errors = err instanceof Array ? err : [err];
                },
            );
        },
    },

    components: {
        CgfsOption,
    },
};
</script>

<style lang="css" scoped>
.cgfs-options {
    width: 100%;
    max-width: 512px;
    margin: 0 auto;
}

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
