<template>
    <span :id="compId" class="help-popover text-muted" @click.prevent.stop>
        <b-popover triggers="click" placement="left" :target="compId">
            <div class="help-popover-content">
                <slot>{{ help }}</slot>
            </div>
        </b-popover>

        <span title="Click to show help">
            <icon name="info-circle" scale="0.875" />
        </span>
    </span>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/info-circle';

import { uniq } from '@/utils';

export default {
    name: 'help-popover',

    props: {
        help: {
            type: String,
            default: '',
        },
    },

    data() {
        return {
            compId: `help-popover-${uniq()}`,
        };
    },

    components: {
        Icon,
    },
};
</script>

<style lang="scss">
.help-popover {
    cursor: help;
    transform: translateY(-0.125rem);
}

.help-popover-content {
    text-align: justify;
    hyphens: auto;
}
</style>
