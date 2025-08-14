<template>
  <modal :name="modalName" :classes="'modal'" transition="pop-out" :width="250" height="auto" :shiftX="xShift" @before-open="_beforeOpen">
    <div style="padding:10px;">
      <div class="limitedText"><b>{{ title }}</b></div>

      <div style="margin-top: 10px;" v-html="content" class="limitedText"></div>

      <div class="footerButtons">
        <ButtonSec :label="cancelLabel" @click="_closeModal"/>
        <ButtonSec :label="confirmLabel" @click="_confirmModal"/>
      </div>
    </div>
  </modal>
</template>

<script>

import ButtonSec from "@/components/interface/elements/base/ButtonSec.vue";
import {safeVal} from "@/scripts/tools/Utils";

export default {
  name: "NotificationModal",
  components: {ButtonSec},
  props: ["modalName", "xShift"],
  data() {
    return {
      title: "Confirmation Modal",
      content: "Do you confirm the modal?",
      confirmLabel: "Confirm",
      cancelLabel: "Cancel",
      confirmAction: null,
      cancelAction: null,
    };
  },

  methods: {
    _closeModal() {
      if(this.cancelAction != null) this.cancelAction();
    },

    _confirmModal() {
      if(this.confirmAction != null) this.confirmAction();
    },

    _beforeOpen (event) {
      let params = event.params;

      if(safeVal(params) == null) return;

      this.title = safeVal(params.title, this.title);
      this.content = safeVal(params.content, this.content);
      this.confirmLabel = safeVal(params.confirmLabel, this.confirmLabel);
      this.cancelLabel = safeVal(params.cancelLabel, this.cancelLabel);

      this.confirmAction = safeVal(params.confirmAction, this.confirmAction);
      this.cancelAction = safeVal(params.cancelAction, this.cancelAction);
    },
  }

}

</script>


<style scoped>

.footerButtons {
  display:inline-block;
  margin-top:10px;
}

.footerButtons > * {
  min-width: 85px;
  display:inline-block;
  margin: 0 2px;
}

</style>