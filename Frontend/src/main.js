import 'regenerator-runtime'
import Vue from 'vue'
import Main from './components/Main.vue'
import VueAce from "@aminoeditor/vue-ace";
import vSelect from "vue-select";
import VModal from 'vue-js-modal';
import VueSlider from 'vue-slider-component'
import autoBlur from './scripts/directives/autoBlurInputDirective';

Vue.config.productionTip = false;

Vue.component("v-select", vSelect);
Vue.use(require('@hscmap/vue-menu'));

//Register tags to not shown as error in editor
Vue.component('hsc-menu-item', null);
Vue.component('hsc-menu-bar-item', null);
Vue.component('hsc-menu-bar', null);
Vue.component('hsc-menu-separator', null);
Vue.component('hsc-menu-style-black', null);
Vue.component('modal', null);

Vue.use(VueAce);
Vue.use(VModal);

Vue.component("vue-slider", VueSlider);

Vue.directive('auto-blur', autoBlur);

import "@fontsource/noto-sans";

require('jquery');
require("jquery-ui/ui/widgets/resizable");
require("jquery-ui/themes/base/all.css");
require('bootstrap-icons/font/bootstrap-icons.css');

export let system= Main;

export function initializeSystem(ref) {system = ref;}

new Vue({
  render: h => h(Main),
}).$mount('#app')
