<template>
<b-form-group class="cgfs-option"
              @keydown.native="$emit('keydown', $event)">
    <template slot="label">
        {{ option.label }}

        <span v-if="option.required"
              class="text-muted">
            *
        </span>

        <help-popover v-if="option.help"
                      :help="option.help"/>
    </template>

    <b-form-input v-if="option.type in { text: 0, password: 0 }"
                  v-model="internal"
                  :type="option.type"/>

    <b-form-select v-else-if="option.type === 'select'"
                   v-model="internal"
                   :options="option.options"/>

    <b-form-file v-else-if="option.type === 'directory'"
                 v-model="internal"
                 :placeholder="internal"
                 directory/>

    <b-input-group v-else-if="option.type === 'checkbox'">
        <b-form-checkbox v-for="suboption in option.options"
                         v-model="internal[suboption.label]"
                         class="form-control">
            {{ suboption.label }}

            <help-popover v-if="suboption.help"
                          :help="suboption.help"/>
        </b-form-checkbox>
    </b-input-group>

    <b-input-group v-else-if="option.type === 'radio'">
        <b-form-radio v-for="suboption in option.options"
                      v-model="internal"
                      :value="suboption.value"
                      class="form-control">
            {{ suboption.label }}

            <help-popover v-if="suboption.help"
                          :help="suboption.help"/>
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
        let internal = this.value || this.option.default || '';

        if (this.option.type === 'checkbox') {
            if (!internal) {
                internal = {};
            }

            for (const option of this.option.options) {
                if (internal[option.label] == null) {
                    internal[option.label] = option.default;
                }
            }
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

<style lang="css" scoped>
.help-popover {
    float: right;
}
</style>
