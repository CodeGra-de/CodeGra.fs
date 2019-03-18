<template>
<div id="app" class="container">
    <img class="logo"
         src="~@/assets/codegrade-fs.png"
         alt="CodeGrade Filesystem"/>

    <cgfs-options v-if="!running"
                  @mount="mount"/>
    <!-- <cgfs-log v-else/> -->
</div>
</template>

<script>
import CgfsOptions from '@/components/CgfsOptions';
// import CgfsLog from '@/components/CgfsLog';

export default {
    name: 'codegrade-fs',

    data() {
        return {
            running: false,
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

        document.addEventListener('click', event => {
            if (!event.target.closest('.popover-body') && popoverVisible) {
                this.$root.$emit('bv::hide::popover');
            }
        }, true);
    },

    methods: {
        mount(config) {
            console.log(config);
        },
    },

    components: {
        CgfsOptions,
    },
};
</script>

<style lang="css" scoped>
#app {
    max-width: 512px;
    margin: 1.5rem auto;
}

.logo {
    width: 100%;
    margin-bottom: 1.5rem;
    font-weight: 300;
}
</style>
