<template>
<div class="cgfs-options">
    <cgfs-option v-if="config != null"
                 v-for="option in options"
                 :key="option.label"
                 v-model="config[option.label]"
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
            <li v-for="error in errors">
                {{ error }}
            </li>
        </ul>
    </b-alert>
</div>
</template>

<script>
import {
    ensureDirectory,
    readConfig,
    writeConfig,
} from '@/utils/config';

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
            config: null,
            errors: [],
        };
    },

    mounted() {
        readConfig().then(this.setConfig);
    },

    methods: {
        setConfig(config) {
            // eslint-disable-next-line
            for (const option of this.options) {
                if (config[option.label] == null) {
                    config[option.label] = option.default || '';
                }
            }

            if (process.env.NODE_ENV === 'development') {
                // Always use the localhost:8080 route.
                config[this.options[0].label] = this.options[0].options[0].value;
            }

            this.config = config;
        },

        ensureOptionValid(option) {
            if (option.required && !this.config[option.label]) {
                return new Error(`"${option.label}" is required.`);
            }

            return null;
        },

        ensureConfigValid() {
            const errors = this.options
                .map(this.ensureOptionValid)
                .filter(err => err);

            if (errors.length) {
                return Promise.reject(errors);
            } else {
                return ensureDirectory(this.config['Mount point'], true);
            }
        },

        start() {
            this.ensureConfigValid().then(
                () => writeConfig(this.config),
            ).then(
                () => this.$emit('start', this.config),
            ).catch(
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
