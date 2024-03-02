import {Component} from "@/scripts/components/Component";
import {STRING_DT, strSocket} from "@/scripts/components/modules/base";
import {Display} from "@/scripts/components/monitor/Display";
import {anySocket} from "@/scripts/components/modules";
import {StringControl} from "@/scripts/components/modules/base/controls/StringCtrl";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";

export default class _StringSplit extends Component {
    constructor(pathIdentifier){
        super("StringSplit", "String Split", pathIdentifier);
    }

    builder(node) {
        node.mode = new NumControl(node, "mode", false, 0,"Mode", "0=Outputs, 1=Array", 0, 1);

        node.outs = new NumControl(node, "outs", false, 1,"Outputs", "", 0);
        node.delimiter = new StringControl(node, "delimiter", false, ",","Delim", "");

        return this.onBuilderInitialized(node,
            new Display(node, STRING_DT.name),
            [{name: strSocket.name, socket: strSocket}],
            [{name: strSocket.name, socket: strSocket}],
            [node.delimiter, node.mode, node.outs]);
    }

    onControlValueChanged(ctrl, node, oldVal) {
        super.onControlValueChanged(ctrl, node, oldVal);

        if(node.mode.getValue() === 0)
            this.updateSockets(node, 1, node.outs.getValue(), strSocket, strSocket).then();
        else this.updateSockets(node, 1, 1, strSocket, anySocket).then();

        this.updateDisplay(node);
    }

    updateDisplay(node) {
        node.outs.vueContext.$el.style.display = node.mode.getValue() === 1 ? "None" : "Block";
    }

    getData(node) {
        return {
            delimiter: node.delimiter.getValue(),
            mode: node.mode.getValue(),
            outs: node.outs.getValue()
        };
    }

    async setData(node, data) {
        node.delimiter.setValue(data.delimiter);
        node.mode.setValue(data.mode);
        node.outs.setValue(data.outs);

        if(node.mode.getValue() === 0)
            await this.updateSockets(node, 1, node.outs.getValue(), strSocket, strSocket).then();
        else await this.updateSockets(node, 1, 1, strSocket, anySocket).then();
    }
}
