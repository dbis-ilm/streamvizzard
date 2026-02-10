<template>
  <div class="searchSelectList">
    <div style="display: flex;">
      <input class="formInputField small searchFilter" type="text" v-model="searchValue" placeholder="Search..."/>
      <i class="clickableIcon bi bi-x-circle searchClear" title="Clear search" @click="() => searchValue = ''"></i>
    </div>
    <div class="searchContainer" :style="maxContentHeight != null ? ('max-height: ' + maxContentHeight) : ''">
      <div class="spinnerContainer" v-if="loading"><div class="loader"></div></div>
      <div v-if="errorMessage.length > 0" class="errorContainer">{{errorMessage}}</div>

      <div class="categoryContainer" v-for="cat in categories" :key="cat.name">
        <div class="catTitle noSelect" v-if="categoriesEnabled && cat.elms.filter(_filterElm).length > 0" @click="_toggleCategory(cat)" title="Show/Hide category">
          <div class="limitedText" style="max-width: calc(100% - 1rem)">{{cat.name != null ? cat.name : 'Uncategorized'}}</div>
          <i :class="'clickableIcon bi bi-caret-' + (!cat.show ? 'down' : 'up') + '-fill'"></i>
        </div>

        <div class="listElm noSelect" :style="elm.style"
             v-for="elm in cat.elms.filter(_filterElm)" v-show="cat.show"
             :key="getDescriptor(elm)" :title="getDescriptor(elm)" @click="_onElmClicked(elm)">
          <i v-if="allowEdit"  class="clickableIcon bi bi-pencil searchListEditIcon" @click="_onElmEdit($event, elm)" :title="editTooltip" style="position: absolute; left: 0.125rem; top: 0.125rem;"></i>
          <slot :data="elm"></slot>
          <i v-if="allowDelete" @click="_onElmDelete($event, elm)" class="clickableIcon bi bi-trash searchListDeleteIcon" :title="deleteTooltip" style="position: absolute; right: 0.125rem; top: 0.125rem;"></i></div>
      </div>
    </div>
  </div>
</template>

<script>

import {safeVal} from "@/scripts/tools/Utils";

export default {
  name: "SearchSelectList",
  props: {
    descriptor: { // Example: "name" which will extract title/key/filterVal with dataArray[name]
      default: null
    },
    searchFunc: { // Function [elm, filterVal] that will be called when searching the list, default=searching all elms in obj
      default: null,
    },
    searchKeys: { // Array of custom object keys to use for filter searching, default=no keys are searched
      type: Array,
      default: null
    },
    categoryRetriever: { // If categories should be used to organize the list, null if not
      default: null,
    },
    maxContentHeight: {default: null},
    allowDelete: { default: true},
    deleteTooltip: {default: "Delete from server"},
    allowEdit: { default: false},
    editTooltip: {default: 'Edit entry'},
  },
  data() {
    return {
      loading: false,
      errorMessage: "",

      searchValue: "",

      dataArray: [],
      categories: [],
    }
  },

  computed: {
    categoriesEnabled(){
      return this.categoryRetriever != null;
    }
  },

  methods: {
    updateDataArray(dataArray, catOpenStates=null) {
      this.dataArray = dataArray;

      // If using categories, create an organization of categories > [elements]
      if(this.categoriesEnabled) {
        let categories = new Set();
        let catElmLookup = {};

        for(let elm of this.dataArray) {
          let cat = safeVal(this.categoryRetriever(elm));
          categories.add(cat);

          if(cat in catElmLookup) catElmLookup[cat].push(elm);
          else catElmLookup[cat] = [elm];
        }

        let catList = Array.from(categories).sort();

        this.categories = [];

        let catClosed = {};

        // Array of {name, show} for each category to preserve show/hide state across data updates
        if(catOpenStates != null) {
          for(let catOpenState of catOpenStates) {
            if(!catOpenState["show"]) catClosed[catOpenState["name"]] = true;
          }
        }

        for(let cat of catList) this.categories.push({"name": cat, "show": !(cat in catClosed), "elms": catElmLookup[cat]});
      } else this.categories = [{"name": null, "show": true, "elms": dataArray}]; // All elements in default cat (no name shown)
    },

    clearSearch() {
      this.searchValue = "";
    },

    _filterElm(elm) {
      let filterVal = this.searchValue.trim();

      if(filterVal.length === 0) return true;
      if(elm == null) return false;

      if(this.searchFunc != null) return this.searchFunc(elm, filterVal);
      else { // Not recursive!
        if(this.getDescriptor(elm).toLowerCase().includes(filterVal.toLowerCase())) return true;

        if(this.categoriesEnabled) {
          let cat = safeVal(this.categoryRetriever(elm));
          if(cat != null && cat.toLowerCase().includes(filterVal.toLowerCase())) return true;
        }

        if(typeof elm === 'object') return this._filterObjectKeys(elm, filterVal);
        else if(Array.isArray(elm)) return this._filterArrayElms(elm, filterVal);

        return false;
      }
    },

    _filterObjectKeys(elm, filterVal) {
      if(this.searchKeys == null) return false;

      let filterValLC = filterVal.toLowerCase();

      for(let dv of this.searchKeys) {
        let val = elm[dv];

        if(val != null && (typeof val === 'string' || val instanceof String) && val.toLowerCase().includes(filterValLC)) return true;
      }

      return false;
    },

    _filterArrayElms(array, filterVal) {
      let filterValLC = filterVal.toLowerCase();

      for(let elm of array) {
        if(elm.toLowerCase().includes(filterValLC)) return true;
      }

      return false;
    },

    _toggleCategory(cat) {
      cat["show"] = !cat["show"];
    },

    getDescriptor(elm) {
      return this.descriptor != null ? elm[this.descriptor] : elm;
    },

    _onElmClicked(elm) {
      this.$emit("onSelect", elm);
    },

    _onElmDelete(event, elm) {
      event.stopPropagation();

      this.$emit("onDelete", elm);

      return false;
    },

    _onElmEdit(event, elm) {
      event.stopPropagation();

      this.$emit("onEdit", elm);

      return false;
    }
  }
}

</script>

<style scoped>

.searchFilter {
  width: 100%;
  height: 1.5rem;
}

.searchClear {
  padding-left: 3px;
  font-size: 1.25rem;
}

.searchContainer {
  overflow-y: auto;
  scrollbar-gutter: stable;
  margin-top: 2px;
  padding-right: 10px;
}

.listElm {
  border: 1px solid var(--second-button-border-color);
  background: var(--second-button-bg-color);
  border-radius: var(--button-border-radius);
  cursor: pointer;
  margin-top: 5px;
  text-align: center;
  position: relative;
}

.window .listElm {
  background: var(--window-buton-bg-color);
  border: 1px solid var(--window-buton-border-color);
}

.catTitle {
  margin-top: 5px;
  text-align: left;
  text-decoration: underline;
  cursor: pointer;
  display: flex;
  flex-direction: row;
}

.errorContainer {
  margin-top: 10px;
  color: red;
}

.spinnerContainer {
  margin-top: 10px;
  overflow: hidden;
}

.spinnerContainer > .loader {
  height: 4rem;
  width: 4rem;
}

.loader:after {
  background: var(--second-bg-color);
}

</style>
