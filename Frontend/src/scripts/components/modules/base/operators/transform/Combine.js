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

        return this.onBuilderInitialized(node,
            new Display(node),
            [{name: anySocket.name, socket: anySocket}],
            [{name: anySocket.name, socket: anySocket}],
            [node.ins]);
    }

    onControlValueChanged(ctrl, node, oldVal) {
        super.onControlValueChanged(ctrl, node, oldVal);

        this.updateSockets(node, node.ins.getValue(), 1, anySocket, anySocket).then();
    }

    async setData(node, data) {
        await super.setData(node, data);

        await this.updateSockets(node, node.ins.getValue(), 1, anySocket, anySocket).then();
    }
}
