<template>
  <div class="createOpMenu"
       @mouseleave="timeoutHide()"
       @mouseover="cancelHide()"
       @contextmenu.prevent=""
       :style="'left: ' + menu.posX + 'px; top: ' + menu.posY + 'px;'">
    <div class="header"><div class="headerContent noSelect">Create Operator</div></div>

    <div class="searchBox">
      <input ref="searchField" class="searchField" v-model="filter" placeholder="Search" @keydown="onSearchInput"/>
    </div>

    <div class="content" ref="content">
      <CreateOpEntry v-for="item in items" v-show="!item.filtered"
                     :key="item.title"
                     :layer="0"
                     :item="item"
                     :delay="delay / 2"/>
      <div class="noMatchInfo noSelect" v-show="noMatch">No operator matches!</div>
    </div>

    <div :class="['infoBox', attachHoverLeft && 'attachLeft']" v-if="hoverItem != null" ref="infoBox">
      <div class="infoBoxTitle limitedText"><i :class="['arrow bi bi-caret-right-fill', attachHoverLeft && 'attachLeft']"></i>{{ hoverItem.title }}</div>
      <div class="infoBoxContent">{{ hoverItem.description }}</div>
    </div>
  </div>
</template>

<script>

import {ContextMenu} from "@/scripts/editor/ContextMenu";
import CreateOpCmEntry from "@/components/editor/contextMenu/CreateOpCMEntry.vue";
import CMTemplate from "@/components/editor/contextMenu/CMTemplate.vue";

export default {
  components: {CreateOpEntry: CreateOpCmEntry},
  props: { menu: ContextMenu, delay: Number },
  mixins: [CMTemplate],

  data() {
    return {
      items: [],
      hoverItem: null,
      attachHoverLeft: false,
      noMatch: false,
      filter: "",
    }
  },

  provide() {
    return {
      onOpenSubs: this.onOpenSubItems,
      onOpSelected: this.onOpSelected,
      onItemHovered: this.onHoverItem
    }
  },

  watch: {
    filter() {
      let filterVal = this.filter.trim().toLowerCase();

      let match = false;

      for(let item of this.items) {
        if(!this.filterItems(item, filterVal)) match = true;
      }

      this.noMatch = !match;
    },
  },

  methods: {
    onOpSelected(item) {
      // When an operator was selected to add

      if(item.onClick) {
        item.onClick();

        this.hide();
      }
    },

    hide() {
      this.$streamvizzard.editor.closeContextMenu(this.menu);
    },

    filterItems(item, searchVal) {
      if(searchVal.length === 0) item.filtered = false;
      else if(item.subitems == null) item.filtered = !item.title.toLowerCase().includes(searchVal); // Leaf

      if(item.subitems != null) {
        let hasMatch = false;

        for(let subItem of item.subitems) {
          if(!this.filterItems(subItem, searchVal)) hasMatch = true;
        }

        item.filtered = !hasMatch;
      }

      item.showSubItems = !item.filtered && searchVal.length !== 0;

      return item.filtered;
    },

    onSearchInput(input) {
      // If enter is pressed, check if there is only one remaining entry and select this

      if(input.keyCode === 13 || input.key === "Enter") {

        const traverseChildren = (elm, activeLeafs) => {
          if(elm.filtered || !elm.showSubItems) return false;

          if(elm.subitems == null) { // Leaf
            activeLeafs.push(elm);

            return;
          }

          for(let subItem of elm.subitems) {
            traverseChildren(subItem, activeLeafs);
          }
        };

        let activeLeafs = [];
        for(let item of this.items) traverseChildren(item, activeLeafs);

        if(activeLeafs.length !== 1) return;

        this.onOpSelected(activeLeafs[0]);
      }
    },

    onHoverItem(item) {
      this.hoverItem = item;
      this.attachHoverLeft = false;

      if(item == null) return;

      this.$nextTick(() => {
        this.attachHoverLeft = !this.$streamvizzard.editor.isFullyVisible(this.$refs.infoBox).fullyVisible;
      });
    },

    onOpenSubItems(item) {
      // Scroll item into view

      let container = this.$refs.content;
      let target = item.$el;

      const containerRect = container.getBoundingClientRect();
      const targetRect = target.getBoundingClientRect();
      const containerContentTop = containerRect.top + container.clientTop;

      const targetTop = targetRect.top - containerContentTop + container.scrollTop;
      const targetBottom = targetTop + targetRect.height;
      const visibleTop = container.scrollTop;
      const visibleBottom = visibleTop + container.clientHeight;

      let newScrollTop = container.scrollTop;
      let needsScroll = false;

      if (targetTop < visibleTop) {
        newScrollTop = targetTop;
        needsScroll = true;
      } else if (targetBottom > visibleBottom) {
        newScrollTop = targetBottom - container.clientHeight;
        needsScroll = true;
      }

      if (needsScroll) container.scrollTo({ top: newScrollTop, behavior: 'smooth' });
    },

    addItem(title, onClick, path = [], description) {
      let items = this.items;

      for(let level of path) {
        let exist = items.find(i => i.title === level);

        if(!exist) {
          exist = { title: level, subitems: [], filtered: false, showSubItems: false };
          items.push(exist)
        }

        items = exist.subitems || (exist.subitems = []);
      }

      items.push({ title, onClick, description, filtered: false, showSubItems: false });
    },
  },

  mounted() {
    for(let item of this.menu.items) this.addItem(...item);

    this.$refs.searchField.focus();
  },
}

</script>

<style scoped>

.createOpMenu {
  color: white;
  left: 0;
  top: 0;
  position: fixed;
  min-width: 250px;

  margin-top: -45px;
  margin-left: -125px;

  background-color: var(--main-font-color);
  border-radius: 4px;

  display: flex;
  flex-direction: column;
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

.searchBox {
  padding: 2px 4px;
}

.searchField {
  width: 100%;
  box-sizing: border-box;
  text-align: center;
  color: var(--main-font-color);
}

.searchField:focus {
  outline: none;
  background: var(--input-active-color) !important;
}

.content {
  flex: 1;
  padding: 0 4px 2px 4px;
  max-height: 450px;
  overflow-y: auto;
  overflow-x: hidden;
}

.noMatchInfo {
  cursor: default;
}

.infoBox {
  position: absolute;
  left: 100%;
  top: 0;

  width: 220px;

  margin-left: -3px;
  padding: 4px 4px 4px 5px;
  background-color: var(--main-font-color);
  border-radius: 0 4px 4px 0;
}

.infoBox.attachLeft {
  left: 0;
  transform: translateX(-100%);
  margin-left: 3px;
  border-radius: 4px 0 0 4px;
}

.infoBoxTitle {
  position: relative;
  font-weight: bold;
  padding-bottom: 4px;
  padding-left: 14px;
  padding-right: 14px;
}

.infoBoxTitle .arrow {
  left: -4px;
  position: absolute;
}

.infoBoxTitle .arrow.attachLeft {
  right: -4px;
  left: unset;
  transform: rotate(180deg);
}

.infoBoxContent {
  font-weight: lighter;
  font-size: 0.85rem;
  padding-top: 4px;
  padding-bottom: 4px;
  border-top: 1px solid white;
}

</style>
