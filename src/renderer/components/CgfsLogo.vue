<template>
    <div class="cgfs-logo">
        <img src="~@/assets/codegrade-fs.png" alt="CodeGrade Filesystem" />
    </div>
</template>

<script>
export default {
    name: 'cgfs-logo',
};
</script>

<style lang="scss" scoped>
@import '@/_mixins.scss';

img {
    display: block;
    width: 100%;
    max-width: min($options-width, $log-width) - 2 * $card-spacer-x;
    margin: 1rem auto;
}
</style>
