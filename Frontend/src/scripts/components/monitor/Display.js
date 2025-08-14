import Rete from "rete";
import DisplayTemplate from "@/components/features/monitor/displays/DisplayTemplate";

export class Display extends Rete.Control {
    constructor(node, dataType = null, tooltip = "") {
        super("display_" + node.id);

        this.component = DisplayTemplate;
        this.props = {tooltip: tooltip, node: node, ctrl: this, initialDataType: dataType};
    }

    onDisplayChanged(node) {
        node.component.sendMetaDataUpdate(node);
    }

    onSocketsChanged(node) {
        let socketOutCount = node.outputs.size;

        if(this.vueContext.displaySocket >= socketOutCount) {
            this.vueContext.displaySocket = socketOutCount - 1;
            this.vueContext.reset();

            this.onDisplayChanged(node);

            node.component.editor.trigger("onNodeDSChanged", this.vueContext);
        }

        node.component.editor.trigger("onNodeSocketsChanged", node);
    }

    setData(data) {
        if(data == null) {
            this.vueContext.onValueUpdated(null);
            return;
        }

        this.vueContext.handleDisplayModeUpdate(data.dType);

        this.vueContext.handleDataStructure(data.struc);

        //Set real value if we are in correct state
        if(data.dMode === this.vueContext.displayMode && data.dSocket === this.vueContext.displaySocket)
            this.vueContext.onValueUpdated(data.data);
    }

    getDisplayData() {
        return {
            dataType: this.vueContext.dataType != null ? this.vueContext.dataType.name : null,
            socket: this.vueContext.displaySocket,
            mode: this.vueContext.displayMode,
            inspect: this.vueContext.dataInspect,
            settings: this.vueContext.settings
        };
    }

    setDisplayData(data) {
        this.vueContext.switchDisplaySocket(data.socket);
        this.vueContext.handleDisplayModeUpdate(data.dataType);

        if(!data.dataType) return;

        this.vueContext.switchDisplayMode(data.mode);

        if(data.settings == null) {
            console.error("Settings are null for " + data);
            data.settings = this.vueContext.getDefaultSettings();
        }

        this.vueContext.setSettings(data.settings);

        this.vueContext.switchDataInspect(data.inspect);
    }

    reset() {
        //Full Reset
        this.vueContext.reset(true);
    }
}
