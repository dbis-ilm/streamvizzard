<template>
  <div class="context-menu"
       ref="menu"
       v-if="visible"
       v-bind:style="style"
       @mouseleave="timeoutHide()"
       @mouseover="cancelHide()"
       @contextmenu.prevent="">
    <Search ref="search" v-if="searchBar" v-model="filter" @search="onSearch"></Search>
    <Item v-for="item in filtered"
          :key="item.title"
          :item="item"
          :args="args"
          :delay="delay / 2"/>
    <Item v-if="searchElementStripped" :item="{'title': '...'}" :delay="0" class="strippedItem"></Item>
  </div>
</template>

<script>
import hideMixin from './debounceHide'
import Item from './Item.vue';
import Search from './Search.vue';
import { fitViewport } from '../utils';
import {EditorInputManager} from "@/scripts/services/EditorInputManager";

export default {
  props: { searchBar: Boolean, searchKeep: Function },
  mixins: [hideMixin('hide')],
  data() {
    return {
      x: 0,
      y: 0,
      visible: false,
      args: {},
      filter: '',
      items: [],

      initial: false,
      maxSearchElements: 9,
      searchElementStripped: false
    }
  },
  computed: {
    style() {
      return {
        top: this.y+'px',
        left: this.x+'px'
      }
    },
    filtered() {
      if(!this.filter) return this.items;
      const regex = new RegExp(this.filter, 'i');

      let leafs = 0;

      return this.extractLeafs(this.items)
        .filter(({ title }) => {
          let match = this.searchKeep(title) || title.match(regex);

          if(match) leafs += 1;
          this.searchElementStripped = leafs > this.maxSearchElements;

          return match && leafs <= this.maxSearchElements;
        });
    }
  },
  methods: {
    extractLeafs(items) {
      if(!items) return [];
      let leafs = [];
      items.map(item => {
        if(!item.subitems) leafs.push(item)

        leafs.push(...this.extractLeafs(item.subitems))
      })

      return leafs;
    },
    onSearch(e) {
      this.filter = e;
    },
    show(x, y, args = {}) {
      this.initial = false;
      this.visible = true;
      this.x = x;
      this.y = y;
      this.args = args;

      this.cancelHide();

      EditorInputManager.onInputSelected(this.$el);
    },
    hide() {
      this.visible = false;

      EditorInputManager.onInputDeselected(this.$el);
    },
    additem(title, onClick, path = []) {
      let items = this.items;
      for(let level of path) {
        let exist = items.find(i => i.title === level);

        if(!exist) {
          exist = { title: level, subitems: [] };
          items.push(exist)
        }

        items = exist.subitems || (exist.subitems = []);
      }

      items.push({ title, onClick });
    },
  },
  updated() {
    if(this.$refs.menu && !this.initial) {
      this.initial = true;
      [this.x, this.y] = fitViewport([this.x, this.y], this.$refs.menu)
    }
  },
  mounted() {
    this.$root.$on('show', this.show);
    this.$root.$on('hide', this.hide);
    this.$root.$on('additem', this.additem);
  },
  components: {
    Item,
    Search
  }
}
</script>


<style scoped>

.context-menu {
  left: 0;
  top: 0;
  position: fixed;
  padding: 10px;
  width: 140px;
  margin-top: -20px;
  margin-left: -60px;
}

.strippedItem {
  pointer-events: none;
}

</style>

<style>
.contextMenuItem {
  color: #fff;
  padding: 4px;
  background-color: var(--main-font-color);
  cursor: pointer;
  width: 100%;
  position: relative;

  -webkit-user-select: none; /* Safari */
  -ms-user-select: none; /* IE 10 and IE 11 */
  user-select: none; /* Standard syntax */
}

.contextMenuItem:first-child {
  border-top-left-radius: 4pt;
  border-top-right-radius: 4pt;
}

.contextMenuItem:last-child {
  border-bottom-left-radius: 4pt;
  border-bottom-right-radius: 4pt;
}

.contextMenuItem:hover {
  background-color: var(--main-hover-color);
}

</style>
