import Vue from 'vue';
import Router from 'vue-router';

import CGFSOptions from '@/components/CgfsOptions';
// import Log from '@/components/Log';

Vue.use(Router);

export default new Router({
    routes: [
        {
            path: '/',
            name: 'options',
            component: CGFSOptions,
        },
        // {
        //     path: '/log',
        //     name: 'log',
        //     component: Log,
        // },
        {
            path: '*',
            redirect: '/',
        },
    ],
});
