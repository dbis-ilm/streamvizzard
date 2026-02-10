import {Definition} from "@/scripts/pipeline/operators/Definition";
import {StringParam} from "@/scripts/pipeline/operators/modules/base/params/StringParam";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {strSocket} from "@/scripts/pipeline/operators/modules/base";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _KafkaSink extends Definition {
    constructor(pathIdentifier){
        super("KafkaSink", "Kafka Sink", pathIdentifier);
    }

    build(operator) {
        let broker = new StringParam("broker", "127.0.0.1", "Broker");
        let port = new NumberParam("port", 9092, 0, null, "Port","The port used for the kafka connection");
        let topic = new StringParam("topic", "my-topic", "Topic");
        let encoding = new StringParam("encoding", "utf-8", "Encoding", "Encoding used to encode the string to be send");
        let maxRequestSize = new NumberParam("maxRequestSize", 1048588, 0, null,
            "Max Size", "The maximum data size (bytes) to include in a batch.)");
        let linger = new NumberParam("linger", 5, 0, null, "Linger","Max. wait time (ms) until sending the batch.");

        this._construct(operator,
            [new SocketDef(strSocket)],
            [],
            [broker, port, topic, encoding, maxRequestSize, linger]);
    }
}
