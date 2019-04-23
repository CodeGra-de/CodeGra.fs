<template>
    <div class="advanced-collapse">
        <div class="collapse-trigger text-muted" v-b-toggle.advanced-collapse>
            <icon name="caret-right" />
            Advanced
        </div>

        <b-collapse id="advanced-collapse" :visible="value" @input="$emit('input', $event)">
            <div class="collapse-area">
                <slot />
            </div>
        </b-collapse>
    </div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/caret-right';

export default {
    name: 'advanced-collapse',

    props: {
        value: {
            type: Boolean,
            default: false,
        },
    },

    components: {
        Icon,
    },
};
</script>

<style lang="scss" scoped>
.collapse-trigger {
    display: inline-block;
    user-select: none;
    cursor: pointer;
}

.collapse-area {
    padding-top: 0.5rem;
}

.fa-icon {
    height: 1rem;
    width: 1rem;
    transform: translateY(-2px) rotate(0);
    transition: transform 300ms;

    .collapse-trigger:not(.collapsed) & {
        transform: translateY(-2px) rotate(90deg);
    }
}
</style>
