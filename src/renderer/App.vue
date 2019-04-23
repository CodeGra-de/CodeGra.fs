<template>
    <div id="app" class="container-fluid">
        <img class="logo" src="~@/assets/codegrade-fs.png" alt="CodeGrade Filesystem" />

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

<style lang="css" scoped>
#app {
    display: flex;
    flex-direction: column;
    height: 100vh;
    padding: 15px;
}

.logo {
    flex: 0 0 auto;
    width: 100%;
    max-width: 550px;
    margin: 0 auto 1rem;
    font-weight: 300;
}

.cgfs-log,
.cgfs-options {
    flex: 1 1 auto;
    margin: 0 auto;
}
</style>
