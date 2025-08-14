import {Component} from "@/scripts/components/Component";
import {STRING_DT} from "@/scripts/components/modules/base";
import {Display} from "@/scripts/components/monitor/Display";
import {anySocket} from "@/scripts/components/modules";
import {CodeControl} from "@/scripts/components/modules/base/controls/CodeCtrl";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";

export default class _UDO extends Component {
    constructor(pathIdentifier){
        super("UDO", "User Defined Operator", pathIdentifier);
    }

    builder(node) {
        node.inCount = new NumControl(node, "inputs", false, 1,"Inputs", "", 0);
        node.outCount = new NumControl(node, "outputs", false, 1, "Outputs", "", 0);
        node.code = new CodeControl(node, 'code', false, CodeControl.CodeType.UDO,
        "class UserDefinedOperator:\n" +
            "    def onStart(self):\n" +
            "        ...\n\n" +
            "    def execute(self, tupleIn: Tuple) -> tuple:\n" +
            "        return tupleIn.data\n\n" +
            "    def onDestroy(self):\n" +
            "        ...");

        return this.onBuilderInitialized(node,
            new Display(node, STRING_DT.name),
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
