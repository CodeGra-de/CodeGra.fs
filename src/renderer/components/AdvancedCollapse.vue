<template>
    <div class="advanced-collapse">
        <div class="collapse-trigger text-muted" v-b-toggle.advanced-collapse>
            <icon name="caret-right" />
            Advanced
        </div>

        <b-collapse id="advanced-collapse" @input="$emit('input', $event)">
            <slot />
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

<style lang="css" scoped>
.collapse-trigger {
    display: inline-block;
    margin-bottom: 1rem;
    user-select: none;
    cursor: pointer;
}

.fa-icon {
    height: 1rem;
    width: 1rem;
    transform: rotate(0);
    transition: transform 300ms;
}

.collapse-trigger:not(.collapsed) .fa-icon {
    transform: rotate(90deg);
}
</style>
