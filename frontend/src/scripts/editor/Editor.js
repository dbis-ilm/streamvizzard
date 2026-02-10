import {MainContextMenu, OperatorContextMenu} from "@/scripts/editor/ContextMenu";
import {SvInstance} from "@/scripts/StreamVizzard";
import {getOperatorBoundingBox, safeVal, valueOr} from "@/scripts/tools/Utils";
import {ViewConnector} from "@/scripts/tools/ViewConnector";
import {PickedConnection} from "@/scripts/editor/PickedConnection";
import SnappingLine from "@/scripts/editor/SnappingLine";
import EditorNotification from "@/scripts/editor/EditorNotification";

/** @typedef {import('./Editor').default} SvEditor */

/** At which max distance the grid snapping takes place and adjust the position. */
const SNAPPING_THRESHOLD = 4;

export default class Editor {
    constructor() {
        /** @type {SvOperator} **/
        this.selectedOperator = null;

        /** @type {PickedConnection|null} Connection that is currently being created [dragged] **/
        this.pickedConnection = null;

        /** @type ContextMenu **/
        this.contextMenu = null;

        this.shiftX = 0;
        this.shiftY = 0;

        this.scale = 1;

        this.mouseX = 0;
        this.mouseY = 0;

        /** @type {Array<SnappingLine>} */
        this.snappingLines = []; // Visual helper lines to simplify op/pin snapping
        this.enableSnapping = true;

        /** @type {Array<EditorNotification>} */
        this.notifications = [];

        /** If the mouse is currently over the editor or its elements (and not blocked by interface) */
        this.mouseOver = false;

        this.viewConnector = new ViewConnector();
    }

    initialize() {
        SvInstance.registerWatcher(() => [this.scale],
            () => {
            document.documentElement.style.setProperty("--editor-scale-fac", Math.max(1, 1 / this.scale).toString());
        });
    }

    /** @param {SvOperator} operator **/
    selectOperator(operator) {
        if(this.selectedOperator === operator) return;

        this.selectedOperator = operator;

        if(this.selectedOperator != null) operator.promoteOrder();
    }

    // ----------------------------------------------- Picked Connection -----------------------------------------------

    /** @param {SvSocket} socket **/
    pickSocketConnection(socket) {
        // Start creating a new connection [dragging]
        this.pickedConnection = new PickedConnection(socket);

        // If socket is an input, remove previous connection
        if(socket.input) socket.clearConnections();
    }

    /** @param {SvSocket|null} targetSocket **/
    unpickSocketConnection(targetSocket) {
        if(this.pickedConnection == null) return;

        // If we have a valid target (not same op and not same socket type) -> Create connection!
        if(targetSocket != null) {
            let inputSock = targetSocket.input ? targetSocket : this.pickedConnection.rootSocket;
            let outputSock = targetSocket.input ? this.pickedConnection.rootSocket : targetSocket;

            let conValidation = SvInstance.pipeline.validateConnection(inputSock, outputSock);

            if(conValidation != null) {
                let pos = targetSocket.getPosition();
                let size = targetSocket.getSize() / this.scale;

                this.createNotification(new EditorNotification(conValidation, pos.x, pos.y - size / 2));
            } else SvInstance.pipeline.createConnection(inputSock, outputSock);
        }

        this.pickedConnection = null;
    }

    // ------------------------------------------------ Snapping Lines -------------------------------------------------

    /** @param {ReroutePin} currentPin
     * @returns {Object|null} snappedPos */
    calculatePinSnapping(currentPin) {
        return this._calculateSnapping(currentPin.x, currentPin.y, (function* (){
            // Candidate: Other Reroute Pins

            for(let con of SvInstance.pipeline.connections) {
                for(let pin of con.reroutes) {
                    if(pin === currentPin) continue;

                    yield {cord: currentPin.y, snapCord: pin.y, horizontal: true};
                    yield {cord: currentPin.x, snapCord: pin.x, horizontal: false};
                }
            }

            // Candidate: Operator Sockets

            for(let op of SvInstance.pipeline.operators) {
                for(let sock of op.getAllSockets()) {
                    let pos = sock.getPosition();

                    yield {cord: currentPin.y, snapCord: pos.y, horizontal: true};
                    yield {cord: currentPin.x, snapCord: pos.x, horizontal: false};
                }
            }
        })());
    }

    /** @param {SvOperator} currentOp
     * @returns {Object|null} snappedPos */
    calculateOperatorSnapping(currentOp) {
        return this._calculateSnapping(currentOp.posX, currentOp.posY, (function*() {
            // --- Match operator bounds ---

            // Candidate: Other operators

            for(let op of SvInstance.pipeline.operators) {
                if(op === currentOp) continue;

                yield {cord: currentOp.posY, snapCord: op.posY, horizontal: true}; // Upper border
                yield {cord: currentOp.posX, snapCord: op.posX, horizontal: false}; // Left border
            }

            // --- Match operator sockets ---

            for(let sock of currentOp.getAllSockets()) {
                let pos = sock.getPosition();
                let offset = {x: pos.x - currentOp.posX, y: currentOp.posY - pos.y};

                // Candidate: Reroute Pins [only vertical]

                for(let con of SvInstance.pipeline.connections) {
                    for(let pin of con.reroutes) {
                        yield {cord: pos.y, snapCord: pin.y, horizontal: true, snapOffset: offset.y};
                    }
                }

                // Candidate: Other Sockets [only vertical]

                for(let op of SvInstance.pipeline.operators) {
                    if(op === currentOp) continue;

                    for(let otherSock of op.getAllSockets()) {
                        if(sock.input === otherSock.input) continue; // Only match pairs of input-output

                        let otherPos = otherSock.getPosition();

                        yield {cord: pos.y, snapCord: otherPos.y, horizontal: true, snapOffset: offset.y};
                    }
                }
            }
        }()));
    }

    /** @param {Group} group
     * @returns {Object|null} snappedPos */
    calculateGroupSnapping(group) {
        return this._calculateSnapping(group.x, group.y, (function*() {
            // Check candidates for each operator of this group

            for(let gOp of Object.values(group.operators)) {
                let groupOffset = {x: group.x - gOp.posX, y: group.y - gOp.posY};

                // --- Match operator bounds ---

                // Candidate: Other operators (that do not belong to the group)

                for(let op of SvInstance.pipeline.operators) {
                    if(op.id in group.operators) continue;

                    yield {cord: gOp.posY, snapCord: op.posY, horizontal: true, snapOffset: groupOffset.y}; // Upper border
                    yield {cord: gOp.posX, snapCord: op.posX, horizontal: false, snapOffset: groupOffset.x}; // Left border
                }

                // --- Match operator sockets (with connection to outside the group) ---

                for(let sock of gOp.getAllSockets()) {
                    // Only include sockets with connections to operators outside the group

                    let conOutside = false;

                    for(let con of sock.connections) {
                        if((sock.input && !(con.output.operator.id in group.operators)) ||
                            (!sock.input && !(con.input.operator.id in group.operators))) {
                            conOutside = true;
                            break;
                        }
                    }

                    if(!conOutside) continue;

                    let pos = sock.getPosition();
                    let offset = {x: gOp.posX - pos.x + groupOffset.x, y: gOp.posY - pos.y + groupOffset.y};

                    // Candidate: Reroute Pins (outside group)

                    for(let con of SvInstance.pipeline.connections) {
                        if(con.input.operator.id in group.operators && con.output.operator.id in group.operators) continue;

                        for(let pin of con.reroutes) {
                            yield {cord: pos.y, snapCord: pin.y, horizontal: true, snapOffset: offset.y};
                            yield {cord: pos.x, snapCord: pin.x, horizontal: false, snapOffset: offset.x};
                        }
                    }

                    // Candidate: Other Sockets (only vertical, only outside group)

                    for(let op of SvInstance.pipeline.operators) {
                        if(op.id in group.operators) continue;

                        for(let otherSock of op.getAllSockets()) {
                            if(sock.input === otherSock.input) continue; // Only match pairs of input-output

                            let otherPos = otherSock.getPosition();

                            yield {cord: pos.y, snapCord: otherPos.y, horizontal: true, snapOffset: offset.y};
                        }
                    }
                }
            }
        }()));
    }

    _calculateSnapping(origX, origY, candidates) {
        this.clearSnappingLines();

        if(!this.enableSnapping) return null;

        let maxDist = SNAPPING_THRESHOLD / Math.min(1, this.scale); // Max distance for which we still include other candidates

        let closestDistH = null;
        let closestDistV = null;

        // The position for the rendered snapping lines
        let snapLineX = origX;
        let snapLineY = origY;

        // The actual snap position given back to the calling obj (to snap the obj to)
        let snappedX = origX;
        let snappedY = origY;

        let calcSnap = (candidate) =>  {
            let cord = candidate.cord;
            let snapCord = candidate.snapCord;
            let horizontal = candidate.horizontal;

            // Offset for the returned snap position if our testing-cord is not the actual cord we want to snap the obj to
            let snapOffset = valueOr(candidate.snapOffset, 0);

            let snapDist = Math.abs(cord - snapCord);

            if(snapDist < maxDist) {
                if(horizontal && (closestDistH == null || snapDist < closestDistH)) {
                    closestDistH = snapDist;
                    snapLineY = snapCord;
                    snappedY = snapCord + snapOffset;
                }

                else if(!horizontal && (closestDistV == null || snapDist < closestDistV)) {
                    closestDistV = snapDist;
                    snapLineX = snapCord;
                    snappedX = snapCord + snapOffset;
                }
            }
        };

        for(let candidate of candidates) calcSnap(candidate);

        // Only add a snapping line for the closest snapping pos

        if(closestDistV != null) this.snappingLines.push(new SnappingLine(snapLineX, snapLineY, false));
        if(closestDistH != null) this.snappingLines.push(new SnappingLine(snapLineX, snapLineY, true));

        let snapped = closestDistH != null || closestDistV != null;

        return snapped ? {x: snappedX, y: snappedY} : null;
    }

    clearSnappingLines() {
        this.snappingLines = [];
    }

    // -------------------------------------------------- Notifications ------------------------------------------------

    /** @param {EditorNotification} notification */
    createNotification(notification) {
        this.notifications.push(notification);
    }

    /** @param {EditorNotification} notification */
    removeNotification(notification) {
        let idx =this.notifications.indexOf(notification);
        if(idx > -1) this.notifications.splice(idx, 1);
    }

    // ---------------------------------------------------- Viewport ---------------------------------------------------

    /** @returns {DOMRect} */
    getContainerRect() {
        return this.viewConnector.request("dimensions").container;
    }

    /** @returns {DOMRect} */
    getViewRect() {
        return this.viewConnector.request("dimensions").view;
    }

    /** @param {{x: number, y: number}} objPos Transforms the given position into editor coordinates **/
    getEditorPos(objPos) {
        let view = this.getViewRect();

        return {
            x: (objPos.x - view.left) / this.scale,
            y: (objPos.y - view.top) / this.scale
        }
    }

    fitOperators() {
        if(SvInstance.pipeline.operators.length === 0) return;

        let container = this.getContainerRect();

        const bbox = getOperatorBoundingBox(SvInstance.pipeline.operators);

        const [x, y] = [bbox.centerX, bbox.centerY];
        const [w, h] = [container.width, container.height];

        const [kw, kh] = [w / bbox.width, h / bbox.height];
        const k = Math.min(kh * 0.9, kw * 0.9, 1);

        this.shiftX = container.width / 2 - x * k;
        this.shiftY = container.height / 2 - y * k;
        this.scale = k;
    }

    // ------------------------------------------------- Context Menus -------------------------------------------------

    /** @param {number} posX
     * @param {number} posY
     * @param {Object} [options]
     * @param {number|null} [options.forceId]
     * @param {Object|null} [options.forcePos]
     * @param {Function|null} [options.preCreatedCb]
     * @param {Function|null} [options.postCreatedCb] */
    openMainContextMenu(posX, posY, {
        forceId = null, forcePos = null,
        preCreatedCb = null, postCreatedCb = null} = {}) {

        this.contextMenu = new MainContextMenu(posX, posY, {forceId, forcePos, preCreatedCb, postCreatedCb});
    }

    /** @param {Number} posX
     * @param {Number} posY
     * @param {SvOperator} operator **/
    openOperatorContextMenu(posX, posY, operator) {
        this.contextMenu = new OperatorContextMenu(posX, posY, operator);
    }

    /** @param {ContextMenu|null} menu **/
    closeContextMenu(menu=null) {
        if(this.contextMenu === menu || menu == null) this.contextMenu = null;
    }

    // ----------------------------------------------------- Storage ---------------------------------------------------

    exportSaveData() {
        return {
            "enableSnapping": this.enableSnapping,
        }
    }

    importSaveData(data) {
        this.enableSnapping = safeVal(data["enableSnapping"], this.enableSnapping);
    }
}