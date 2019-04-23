<template>
    <b-form-group
        class="cgfs-option"
        :state="!error"
        :invalid-feedback="error && error.message"
        @keydown.native="$emit('keydown', $event)"
    >
        <template slot="label">
            {{ option.label }}

            <span v-if="option.required" class="text-muted">
                *
            </span>

            <help-popover v-if="option.help" :help="option.help" />
        </template>

        <b-form-input
            v-if="option.type in { text: 0, password: 0 }"
            v-model="internal"
            :type="option.type"
        />

        <b-form-select
            v-else-if="option.type === 'select'"
            v-model="internal"
            :options="option.options"
        />

        <b-form-file
            v-else-if="option.type === 'directory'"
            v-model="internal"
            :placeholder="value"
            directory
        />

        <b-input-group v-else-if="option.type === 'checkbox'">
            <b-form-checkbox
                v-for="suboption in option.options"
                :key="suboption.key"
                v-model="internal[suboption.key]"
                class="form-control"
            >
                {{ suboption.label }}

                <help-popover v-if="suboption.help" :help="suboption.help" />
            </b-form-checkbox>
        </b-input-group>

        <b-input-group v-else-if="option.type === 'radio'">
            <b-form-radio
                v-for="suboption in option.options"
                :key="suboption.value"
                v-model="internal"
                :value="suboption.value"
                class="form-control"
            >
                {{ suboption.label }}

                <help-popover v-if="suboption.help" :help="suboption.help" />
            </b-form-radio>
        </b-input-group>
    </b-form-group>
</template>

<script>
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
        internal(newValue) {
            if (this.option.type === 'directory') {
                this.$emit('input', newValue.path);
            } else {
                this.$emit('input', newValue);
            }
        },
    },

    data() {
        let internal = this.value || '';

        if (!internal && this.option.type === 'checkbox') {
            internal = {};
        }

        return { internal };
    },

    mounted() {
        this.$emit('input', this.internal);
    },

    components: {
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

.input-group {
    @media (max-width: #{$options-width + 2 * $spacer}) {
        flex-direction: column;

        .form-control {
            width: 100%;

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
}

.form-control.custom-control {
    padding-left: $input-padding-x + $custom-control-gutter + $custom-control-indicator-size;

    label {
        display: block;
    }
}
</style>
