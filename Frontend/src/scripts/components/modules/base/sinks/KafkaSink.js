import {Component} from "@/scripts/components/Component";
import {StringControl} from "@/scripts/components/modules/base/controls/StringCtrl";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";
import {strSocket} from "@/scripts/components/modules/base";

export default class _KafkaSink extends Component {
    constructor(pathIdentifier){
        super("KafkaSink", "Kafka Sink", pathIdentifier);
    }

    builder(node) {
        node.broker = new StringControl(node, 'broker', false, '127.0.0.1', "Broker");
        node.port = new NumControl(node, 'port', false, 9092, "Port","The port used for the kafka connection", 0);
        node.topic = new StringControl(node, 'topic', false, "my-topic", "Topic");
        node.encoding = new StringControl(node, 'encoding', false, 'utf-8', "Encoding", "Encoding used to encode the string to be send");
        node.maxRequestSize = new NumControl(node, 'maxRequestSize', false, 1048588, "Max Size", "The maximum data size the be sent (bytes)");

        return this.onBuilderInitialized(node,
            null,
            [{name: strSocket.name, socket: strSocket}],
            [],
            [node.broker, node.port, node.topic, node.encoding, node.maxRequestSize]);
    }
}
