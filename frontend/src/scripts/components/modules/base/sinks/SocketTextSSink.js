import {Component} from "@/scripts/components/Component";
import {StringControl} from "@/scripts/components/modules/base/controls/StringCtrl";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";
import {anySocket} from "@/scripts/components/modules";

export default class _SocketTextSink extends Component {
    constructor(pathIdentifier){
        super("SocketTextSSink", "Socket Text Server Sink", pathIdentifier);
    }

    builder(node) {
        node.ip = new StringControl(node, 'ip', false, '127.0.0.1', "Host");
        node.port = new NumControl(node, 'port', false, 9000, "Port","The port used for the socket connection", 0);
        node.encoding = new StringControl(node, 'encoding', false, "utf-8", "Encoding", "The encoding used to translate the received bytes to text");

        return this.onBuilderInitialized(node,
            null,
            [{name: "Data", socket: anySocket}],
            [],
            [node.ip, node.port, node.encoding]);
    }
}
