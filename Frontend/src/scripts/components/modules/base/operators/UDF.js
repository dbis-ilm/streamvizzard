import {Component} from "@/scripts/components/Component";
import {anySocket} from "@/scripts/components/modules";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";
import {CodeControl} from "@/scripts/components/modules/base/controls/CodeCtrl";
import {Display} from "@/scripts/components/monitor/Display";

export default class _UDF extends Component {
    constructor(pathIdentifier){
        super("UDF", "User Defined Function", pathIdentifier);
    }

    builder(node) {
        node.inCount = new NumControl(node, "inputs", false, 1,"Inputs", "", 0);
        node.outCount = new NumControl(node, "outputs", false, 1, "Outputs", "", 0);
        node.code = new CodeControl(node, 'code', false, CodeControl.CodeType.UDF, "return input");

        return this.onBuilderInitialized(node,
            new Display(node),
            [{name: anySocket.name, socket: anySocket}],
            [{name: anySocket.name, socket: anySocket}],
            [node.inCount, node.outCount, node.code]);
    }

    onControlValueChanged(ctrl, node, oldVal) {
        // First update sockets & connections (which triggers connection removed)
        if(ctrl === node.inCount || ctrl === node.outCount) this.updateSockets(node, node.inCount.getValue(), node.outCount.getValue(), anySocket, anySocket).then();

        // Then, send update info to server
        super.onControlValueChanged(ctrl, node, oldVal);
    }

    async setData(node, data) {
        await super.setData(node, data);

        await this.updateSockets(node, node.inCount.getValue(), node.outCount.getValue(), anySocket, anySocket).then();
    }
}
