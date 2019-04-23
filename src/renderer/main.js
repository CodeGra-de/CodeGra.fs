import Vue from 'vue';
import axios from 'axios';
import BootstrapVue from 'bootstrap-vue';

import './main.scss';

import App from './App';
import store from './store';

if (!process.env.IS_WEB) Vue.use(require('vue-electron'));
Vue.http = Vue.prototype.$http = axios;
Vue.config.productionTip = false;

Vue.use(BootstrapVue);

Vue.prototype.$devMode = process.env.NODE_ENV === 'development';

const htmlEscapes = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
    '`': '&#96;',
};
Vue.prototype.$htmlEscape = function htmlEscape(input) {
    return input && input.replace(/[&<>"'`]/g, match => htmlEscapes[match]);
};

/* eslint-disable no-new */
new Vue({
    components: { App },
    store,
    template: '<App/>',
}).$mount('#app');
