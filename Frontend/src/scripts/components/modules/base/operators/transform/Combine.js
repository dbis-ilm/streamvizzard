import {Component} from "@/scripts/components/Component";
import {Display} from "@/scripts/components/monitor/Display";
import {anySocket} from "@/scripts/components/modules";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";

export default class _Combine extends Component {
    constructor(pathIdentifier){
        super("Combine", "Combine", pathIdentifier);
    }

    builder(node) {
        node.ins = new NumControl(node, "ins", false, 1,"Inputs", "", 0);
        node.outCount = new NumControl(node, "outCount", false, 1, "Outputs", "", 0);

        return this.onBuilderInitialized(node,
            new Display(node),
            [{name: anySocket.name, socket: anySocket}],
            [{name: anySocket.name, socket: anySocket}],
            [node.ins, node.outCount]);
    }

    onControlValueChanged(ctrl, node, oldVal) {
        super.onControlValueChanged(ctrl, node, oldVal);

        this.updateSockets(node, node.ins.getValue(), node.outCount.getValue(), anySocket, anySocket).then();
    }

    getData(node) {
        return {
            ins: node.ins.getValue(),
            outs: node.outCount.getValue()
        };
    }

    async setData(node, data) {
        node.ins.setValue(data.ins);
        node.outCount.setValue(data.outs);

        await this.updateSockets(node, node.ins.getValue(), node.outCount.getValue(), anySocket, anySocket).then();
    }
}
