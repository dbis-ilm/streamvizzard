<template>
  <div class="objectMenu"
       @mouseleave="timeoutHide()"
       @mouseover="cancelHide()"
       @contextmenu.prevent=""
       :style="'left: ' + menu.posX + 'px; top: ' + menu.posY + 'px;'">
    <div class="header"><div class="headerContent noSelect">{{ menu.headerTitle }}</div></div>

    <div class="content" ref="content">
      <div v-for="item in items" :key="item.title" class="menuItem noSelect"
           @click="onItemSelect(item)"
      >{{item.title}}</div>
    </div>
  </div>
</template>

<script>

import {ContextMenu} from "@/scripts/editor/ContextMenu";
import CMTemplate from "@/components/editor/contextMenu/CMTemplate.vue";

export default {
  props: { menu: ContextMenu, delay: Number },
  mixins: [CMTemplate],

  data() {
    return {
      items: [],
    }
  },

  methods: {
    hide() {
      this.$streamvizzard.editor.closeContextMenu(this.menu);
    },

    onItemSelect(item) {
      item.onClick();

      this.hide();
    },

    addItem(title, onClick, path = [], description) {
      let items = this.items;

      for(let level of path) {
        let exist = items.find(i => i.title === level);

        if(!exist) {
          exist = { title: level, subitems: []};
          items.push(exist)
        }

        items = exist.subitems || (exist.subitems = []);
      }

      items.push({ title, onClick, description});
    },
  },

  mounted() {
    for(let item of this.menu.items) this.addItem(...item);
  },
}

</script>

<style scoped>

.objectMenu {
  color: white;
  left: 0;
  top: 0;
  position: fixed;
  width: 140px;

  margin-top: -20px;
  margin-left: -70px;

  background-color: var(--main-font-color);
  border-radius: 4px;
}

.header {
  padding: 4px;
  color: var(--main-font-color);
  font-weight: bold;
  pointer-events: none;
}

.header .headerContent {
  background: white;
  margin: -1px;
  padding: 1px;
  text-align: center;
}

.menuItem {
  padding: 4px;
  cursor: pointer;
}

.menuItem:hover {
  background-color: var(--main-hover-color);
}

</style>
