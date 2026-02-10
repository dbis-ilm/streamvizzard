import SvConnection from "@/scripts/pipeline/SvConnection";
import {SvInstance} from "@/scripts/StreamVizzard";

export class PickedConnection extends  SvConnection {
    /** @param {SvSocket} rootSocket **/
    constructor(rootSocket) {
        super(0);

        /** @type SvSocket **/
        this.rootSocket = rootSocket;
    }

    getEndpoints() {
        let rootPoints = this.rootSocket.getPosition();
        let mouseX = SvInstance.editor.mouseX;
        let mouseY = SvInstance.editor.mouseY;

        if(this.rootSocket.input) return [mouseX, mouseY, rootPoints.x, rootPoints.y];
        else return [rootPoints.x, rootPoints.y, mouseX, mouseY];
    }
}