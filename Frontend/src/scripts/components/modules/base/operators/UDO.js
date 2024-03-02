import {Component} from "@/scripts/components/Component";
import {STRING_DT} from "@/scripts/components/modules/base";
import {Display} from "@/scripts/components/monitor/Display";
import {anySocket} from "@/scripts/components/modules";
import {CodeControl} from "@/scripts/components/modules/base/controls/CodeCtrl";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";

export default class _UDO extends Component {
    constructor(pathIdentifier){
        super("UDO", "UDO", pathIdentifier);
    }

    builder(node) {
        node.inCount = new NumControl(node, "inCount", false, 1,"Inputs", "", 0);
        node.outCount = new NumControl(node, "outCount", false, 1, "Outputs", "", 0);
        node.code = new CodeControl(node, 'code', false, "class UserDefinedOperator:\n" +
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

    getData(node) {
        return {
            code: node.code.getValue(),
            inputs: node.inCount.getValue(),
            outputs: node.outCount.getValue()
        };
    }

    async setData(node, data) {
        node.code.setValue(data.code);
        node.inCount.setValue(data.inputs);
        node.outCount.setValue(data.outputs);

        await this.updateSockets(node, node.inCount.getValue(), node.outCount.getValue(), anySocket, anySocket).then();
    }
}
