<template>
    <div id="app" class="container-fluid">
        <cgfs-log v-if="jwtToken" @stop="jwtToken = ''" :jwt-token="jwtToken"/>
        <cgfs-options v-else @start="jwtToken = $event" />
    </div>
</template>

<script>
import CgfsLog from '@/components/CgfsLog';
import CgfsOptions from '@/components/CgfsOptions';

export default {
    name: 'codegrade-fs',

    data() {
        return {
            console,
            jwtToken: '',
        };
    },

    mounted() {
        let popoverVisible = false;

        this.$root.$on('bv::popover::shown', () => {
            popoverVisible = true;
        });

        this.$root.$on('bv::popover::hidden', () => {
            popoverVisible = false;
        });

        document.addEventListener(
            'click',
            event => {
                if (!event.target.closest('.popover-body') && popoverVisible) {
                    this.$root.$emit('bv::hide::popover');
                }
            },
            true,
        );
    },

    components: {
        CgfsLog,
        CgfsOptions,
    },
};
</script>

<style lang="scss" scoped>
@import "@/_mixins.scss";

#app {
    display: flex;
    flex-direction: column;
    height: 100vh;
}

.cgfs-log,
.cgfs-options {
    flex: 1 1 auto;
    width: 100%;
    margin: $spacer auto;
}

.cgfs-options {
    max-width: $options-width;
}

.cgfs-log {
    max-width: $log-width;
}
</style>
