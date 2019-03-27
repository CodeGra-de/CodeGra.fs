import Vue from 'vue';
import axios from 'axios';
import BootstrapVue from 'bootstrap-vue';

import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap-vue/dist/bootstrap-vue.css';

import App from './App';
import store from './store';

if (!process.env.IS_WEB) Vue.use(require('vue-electron'));
Vue.http = Vue.prototype.$http = axios;
Vue.config.productionTip = false;

Vue.use(BootstrapVue);

/* eslint-disable no-new */
new Vue({
    components: { App },
    store,
    template: '<App/>',
}).$mount('#app');
