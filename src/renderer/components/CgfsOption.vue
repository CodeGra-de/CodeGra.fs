<template>
    <b-form-group
        class="cgfs-option"
        :state="!error"
        :invalid-feedback="error && error.message"
        @keydown.native="$emit('keydown', $event)"
    >
        <template slot="label">
            {{ option.label }}

            <span v-if="option.required" class="text-primary">
                *
            </span>

            <help-popover v-if="option.help" :help="option.help" />
        </template>

        <b-input-group
            v-if="option.type in { text: 0, password: 0 }"
            :prepend="option.prepend"
            :append="option.append"
        >
            <b-form-input
                v-model="internal"
                :type="option.type"
                :placeholder="option.placeholder"
            />
        </b-input-group>

        <multiselect
            v-else-if="option.type === 'select'"
            v-model="internal"
            :options="option.options"
            :placeholder="option.placeholder"
            label="text"
            track-by="value"
        />

        <b-form-file
            v-else-if="option.type === 'directory'"
            v-model="internal"
            :placeholder="value"
            directory
        />

        <b-input-group v-else-if="option.type === 'checkbox'" class="check">
            <b-form-checkbox
                v-for="suboption in option.options"
                :key="suboption.key"
                v-model="internal[suboption.key]"
                class="form-control"
            >
                <help-popover v-if="suboption.help" :help="suboption.help" />

                {{ suboption.label }}
            </b-form-checkbox>
        </b-input-group>

        <b-input-group v-else-if="option.type === 'radio'" class="radio">
            <b-form-radio
                v-for="suboption in option.options"
                :key="suboption.value"
                v-model="internal"
                :value="suboption.value"
                class="form-control"
            >
                <help-popover v-if="suboption.help" :help="suboption.help" />

                {{ suboption.label }}
            </b-form-radio>
        </b-input-group>
    </b-form-group>
</template>

<script>
import Multiselect from 'vue-multiselect';
import 'vue-multiselect/dist/vue-multiselect.min.css';

import HelpPopover from '@/components/HelpPopover';

export default {
    name: 'cgfs-option',

    props: {
        value: {
            type: [Object, String],
            required: true,
        },

        option: {
            type: Object,
            required: true,
        },

        error: {
            type: Error,
            default: null,
        },
    },

    watch: {
        internal: {
            handler() {
                const val = this.external;
                this.$emit('input', val == null ? {} : val);
            },
            immediate: true,
        },
    },

    data() {
        let internal;

        switch (this.option.type) {
            case 'checkbox':
                internal = this.value || {};
                break;
            case 'select':
                internal = this.option.options.find(option => option.value === this.value);
                break;
            case 'directory':
                internal = { path: this.value };
                break;
            default:
                internal = this.value || '';
                break;
        }

        return { internal };
    },

    computed: {
        external() {
            switch (this.option.type) {
                case 'directory':
                    return this.internal.path;
                case 'select':
                    return this.internal && this.internal.value;
                default:
                    return this.internal;
            }
        },
    },

    components: {
        Multiselect,
        HelpPopover,
    },
};
</script>

<style lang="scss" scoped>
.help-popover {
    float: right;
}
</style>

<style lang="scss">
@import '@/_mixins.scss';

.input-group.check,
.input-group.radio {
    flex-direction: column;

    .custom-control {
        width: 100%;
        height: auto;

        &:first-child {
            border-bottom-left-radius: 0;
            border-top-right-radius: $border-radius;
        }

        &:not(:first-child) {
            margin-top: -1px;
            margin-left: 0;
        }

        &:last-child {
            border-top-right-radius: 0;
            border-bottom-left-radius: $border-radius;
        }
    }
}

.form-control.custom-control {
    padding-left: $input-padding-x + $custom-control-gutter + $custom-control-indicator-size;

    .custom-control-label {
        cursor: pointer;
        display: block;
    }
}
</style>
