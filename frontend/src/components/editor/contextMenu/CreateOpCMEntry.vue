<template>
  <div class="createOpMenuItem noSelect" :class="[hasSubitems && 'hasSubitems', layer === 0 && 'root']"
       @click="onClick($event)"
       @mouseover="onHover(true)"
       @mouseleave="onHover(false)">
    {{hasSubitems ? (showSubs ? "▾" : "▴") : ""}} {{item.title}}
    <div class="subitems" v-show="hasSubitems && showSubs">
      <CreateOpEntry v-for="subitem in item.subitems" v-show="!subitem.filtered"
            :key="subitem.title + layer"
            :item="subitem"
            :layer="layer + 1"
            :delay="delay"/>
    </div>
  </div>
</template>

<script>
export default {
  name: "CreateOpEntry",
  props: { delay: Number, item: Object, layer: Number},
  inject: ['onOpenSubs', 'onOpSelected', 'onItemHovered'],

  computed: {
    hasSubitems() {
      return this.item.subitems != null;
    },

    showSubs() {
      return this.item.showSubItems;
    }
  },

  methods: {
    onHover(hover) {
      if(this.hasSubitems) return; // Only for leaf items

      this.onItemHovered(hover ? this.item : null);
    },

    hideSubItems() {
      this.item.showSubItems = false;

      function hideChildren(item) {
        if(item.subitems == null) return;

        for(let subitem of item.subitems) {
          subitem.showSubItems = false;

          hideChildren(subitem);
        }
      }

      hideChildren(this.item);
    },

    onClick(e) {
      e.stopPropagation();

      if(this.item.showSubItems) this.hideSubItems();
      else {
        this.item.showSubItems = true;

        this.$nextTick(() => { // We change content size and need update first
          this.onOpenSubs(this);
        });
      }

      // Leaf element -> Add operator
      this.onOpSelected(this.item);
    }
  },
}
</script>

<style scoped>

.createOpMenuItem {
  padding: 1px 4px 1px 4px;
  cursor: pointer;
  width: 100%;
  text-align: left;
  font-weight: lighter;
  font-size: 0.85rem;
  color: var(--main-border-color);
}

.createOpMenuItem :not(.root) {
  padding-left: 8px;
}

.createOpMenuItem .subitems {
  border-left: 1px solid var(--main-border-color);
  margin-left: 6px;
}

.createOpMenuItem.hasSubitems {
  font-size: 1rem;
  color: white;
  padding-top: 3px;
  padding-bottom: 3px;
}

</style>
