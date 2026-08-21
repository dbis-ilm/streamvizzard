import {
    ConnectionContextMenu,
    GroupContextMenu,
    MainContextMenu,
    OperatorContextMenu
} from "@/scripts/editor/ContextMenu";
import {SvInstance} from "@/scripts/StreamVizzard";
import {containsPoint, getOperatorBoundingBox, intersects, safeVal, valueOr} from "@/scripts/tools/Utils";
import {ViewConnector} from "@/scripts/tools/ViewConnector";
import {PickedConnection} from "@/scripts/editor/PickedConnection";
import SnappingLine from "@/scripts/editor/SnappingLine";
import EditorNotification from "@/scripts/editor/EditorNotification";
import SvOperator from "@/scripts/pipeline/operators/SvOperator";
import {ReroutePin} from "@/scripts/pipeline/SvConnection";

/** @typedef {import('./Editor').default} SvEditor */

/** At which max distance the grid snapping takes place and adjust the position. */
const SNAPPING_THRESHOLD = 4;

export default class Editor {
    constructor() {
        /** @type {SvOperator} **/
        this.selectedOperator = null;

        /** @type {Set<SvOperator | ReroutePin>} Set of editor elms selected at once (contains selectedOp) **/
        this.focusedObjects = new Set(); // Must instantiate new set every time for reactiveness!

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

    /** @param {Array<SvOperator | ReroutePin> | SvOperator | ReroutePin | null} obj */
    selectEditorObject(obj) {
        if(obj == null) {
            this._focusObject(null);
            this.selectedOperator = null;

            return;
        }

        let objs = Array.isArray(obj) ? obj : [obj];

        for(let [idx, elm] of objs.entries()) {
            if(elm instanceof SvOperator)  {
                if(this.selectedOperator === elm) continue;

                this.selectedOperator = elm;
                this._focusObject(elm, idx === 0);
            }

            else if(elm instanceof ReroutePin) {
                if(!this.focusedObjects.has(elm)) { // Deselect current selection if new pin doesn't belong to it
                    if(idx === 0) this.selectedOperator = null;
                    this._focusObject(elm, idx === 0);
                }
            }
        }
    }

    /** @param {SvOperator | ReroutePin | null} obj
     * @param {boolean} clearPrev Clears prev selection if not yet member **/
    _focusObject(obj, clearPrev=true) {
        if(obj == null) {
            this.focusedObjects = new Set();

            return;
        }

        if(obj instanceof SvOperator) obj.promoteOrder();

        if(this.focusedObjects.has(obj)) return;

        if(clearPrev) this.focusedObjects = new Set([obj]);
        else {
            this.focusedObjects.add(obj);
            this.focusedObjects = new Set(this.focusedObjects); // Update ref by copy
        }
    }

    /** @param {SvOperator | ReroutePin} obj
     * @param {number} newX
     * @param {number} newY */
    dragEditorObject(obj, newX, newY) {
        let oldX = newX;
        let oldY = newY;

        if(obj instanceof SvOperator) {
            oldX = obj.posX;
            oldY = obj.posY;

            obj.moveTo(newX, newY);
        } else if(obj instanceof ReroutePin) {
            oldX = obj.x;
            oldY = obj.y;

            obj.con.updateReroutePin(obj, newX, newY);
        }

        let deltaX = newX - oldX;
        let deltaY = newY - oldY;

        // Perform movement of all focused objects

        for(let fo of this.focusedObjects) {
            if(fo === obj) continue;

            if(fo instanceof SvOperator) fo.moveTo(fo.posX + deltaX, fo.posY + deltaY);
            else if(fo instanceof ReroutePin) fo.con.updateReroutePin(fo, fo.x + deltaX, fo.y + deltaY);

            // Groups are not considered since this would prevent individual ops within a group to be moved
        }
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

    /**
     * @param {number} origX
     * @param {number} origY
     * @returns {Object|null} snappedPos */
    calculateSelectionSnapping(origX, origY) {
        return this._calculateSnapping(origX, origY, (function* () {
            for (let obj of SvInstance.editor.focusedObjects) {
                if(obj instanceof SvOperator) {
                    // --- Match operator bounds ---

                    // Candidate: Other operators

                    for(let op of SvInstance.pipeline.operators) {
                        if(op === obj || SvInstance.editor.focusedObjects.has(op)) continue;

                        yield {cord: obj.posY, snapCord: op.posY, horizontal: true, objX: obj.posX, objY: obj.posY}; // Upper border
                        yield {cord: obj.posX, snapCord: op.posX, horizontal: false, objX: obj.posX, objY: obj.posY}; // Left border
                    }

                    // --- Match operator sockets ---

                    for(let sock of obj.getAllSockets()) {
                        let pos = sock.getPosition();
                        let offset = {x: pos.x - obj.posX, y: obj.posY - pos.y};

                        // Candidate: Reroute Pins [only vertical]

                        for (let con of SvInstance.pipeline.connections) {
                            for (let pin of con.reroutes) {
                                if (SvInstance.editor.focusedObjects.has(pin)) continue;

                                yield {cord: pos.y, snapCord: pin.y, horizontal: true, snapOffset: offset.y, objX: obj.posX, objY: obj.posY};
                            }
                        }

                        // Candidate: Other Sockets [only vertical]

                        for (let op of SvInstance.pipeline.operators) {
                            if (op === obj || SvInstance.editor.focusedObjects.has(op)) continue;

                            for (let otherSock of op.getAllSockets()) {
                                if (sock.input === otherSock.input) continue; // Only match pairs of input-output

                                let otherPos = otherSock.getPosition();

                                yield {cord: pos.y, snapCord: otherPos.y, horizontal: true, snapOffset: offset.y, objX: obj.posX, objY: obj.posY};
                            }
                        }
                    }
                } else if(obj instanceof ReroutePin) {
                    // Candidate: Other Reroute Pins

                    for(let con of SvInstance.pipeline.connections) {
                        for(let pin of con.reroutes) {
                            if(pin === obj || SvInstance.editor.focusedObjects.has(pin)) continue;

                            yield {cord: obj.y, snapCord: pin.y, horizontal: true, objX: obj.x, objY: obj.y};
                            yield {cord: obj.x, snapCord: pin.x, horizontal: false, objX: obj.x, objY: obj.y};
                        }
                    }

                    // Candidate: Operator Sockets

                    for(let op of SvInstance.pipeline.operators) {
                        if(SvInstance.editor.focusedObjects.has(op)) continue;

                        for(let sock of op.getAllSockets()) {
                            let pos = sock.getPosition();

                            yield {cord: obj.y, snapCord: pos.y, horizontal: true, objX: obj.x, objY: obj.y};
                            yield {cord: obj.x, snapCord: pos.x, horizontal: false, objX: obj.x, objY: obj.y};
                        }
                    }
                }
            }
        })());
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

                    yield {cord: gOp.posY, snapCord: op.posY, horizontal: true, snapOffset: groupOffset.y, objX: group.x, objY: group.y}; // Upper border
                    yield {cord: gOp.posX, snapCord: op.posX, horizontal: false, snapOffset: groupOffset.x, objX: group.x, objY: group.y}; // Left border
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
                            yield {cord: pos.y, snapCord: pin.y, horizontal: true, snapOffset: offset.y, objX: group.x, objY: group.y};
                            yield {cord: pos.x, snapCord: pin.x, horizontal: false, snapOffset: offset.x, objX: group.x, objY: group.y};
                        }
                    }

                    // Candidate: Other Sockets (only vertical, only outside group)

                    for(let op of SvInstance.pipeline.operators) {
                        if(op.id in group.operators) continue;

                        for(let otherSock of op.getAllSockets()) {
                            if(sock.input === otherSock.input) continue; // Only match pairs of input-output

                            let otherPos = otherSock.getPosition();

                            yield {cord: pos.y, snapCord: otherPos.y, horizontal: true, snapOffset: offset.y, objX: group.x, objY: group.y};
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
        let snapLineX = null;
        let snapLineY = null;

        // Delta of closest match to orig candidates pos -> used to move whole selection
        let snappedDeltaX = 0;
        let snappedDeltaY = 0;

        let calcSnap = (candidate) =>  {
            let cord = candidate.cord;
            let snapCord = candidate.snapCord;
            let horizontal = candidate.horizontal;
            let objX = candidate.objX;
            let objY = candidate.objY;

            // Offset for the returned snap position if our testing-cord is not the actual cord we want to snap the obj to
            let snapOffset = valueOr(candidate.snapOffset, 0);

            let snapDist = Math.abs(cord - snapCord);

            if(snapDist < maxDist) {
                if(horizontal && (closestDistH == null || snapDist < closestDistH)) {
                    closestDistH = snapDist;
                    snapLineY = snapCord;

                    snappedDeltaY = (snapCord + snapOffset) - objY;

                    if(snapLineX == null) snapLineX = objX;
                }

                else if(!horizontal && (closestDistV == null || snapDist < closestDistV)) {
                    closestDistV = snapDist;
                    snapLineX = snapCord;

                    snappedDeltaX = (snapCord + snapOffset) - objX;

                    if(snapLineY == null) snapLineY = objY;
                }
            }
        };

        for(let candidate of candidates) calcSnap(candidate);

        // Only add a snapping line for the closest snapping pos

        if(closestDistV != null) this.snappingLines.push(new SnappingLine(snapLineX, snapLineY, false));
        if(closestDistH != null) this.snappingLines.push(new SnappingLine(snapLineX, snapLineY, true));

        let snapped = closestDistH != null || closestDistV != null;

        return snapped ? {x: origX + snappedDeltaX, y: origY + snappedDeltaY} : null;
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

    /** Returns the DOM rect of the editor container. If onlyVisible is true, accounts for the potentially
     * opened sidebars left/right to return the actual visible section of the container rect!
     * @returns {DOMRect} */
    getContainerRect(onlyVisible = false) {
        let container = this.viewConnector.request("dimensions").container;

        if(onlyVisible) {
            container.x = SvInstance.interface.opPresetBarViewRect.right;
            container.width = SvInstance.interface.sidebarViewRect.left - container.x;
        }

        return container;
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

    /** Finds intersecting editor objects for the provided view coordinates
     * @param {number} x
     * @param {number} y
     * @param {number} width
     * @param {number} height
     * @returns {{ops: Array<SvOperator>, pins: Array<ReroutePin>}} **/
    findIntersectingObjs(x, y, width, height) {
        let topLeft = this.getEditorPos({x: x, y: y});
        let botRight = this.getEditorPos({x: x + width, y: y + height});

        let intersectOps = [];

        for(let op of SvInstance.pipeline.operators) {
            if(intersects(topLeft.x, topLeft.y, botRight.x, botRight.y, op.posX, op.posY, op.posX + op.width, op.posY + op.height)) {
                intersectOps.push(op);
            }
        }

        let intersectPins = [];

        for(let con of SvInstance.pipeline.connections) {
            for(let pin of con.reroutes) {
                if(containsPoint(topLeft.x, topLeft.y, botRight.x, botRight.y, pin.x, pin.y)) intersectPins.push(pin)
            }
        }

        return {ops: intersectOps, pins: intersectPins};
    }

    fitOperators() {
        if(SvInstance.pipeline.operators.length === 0) return;

        let container = this.getContainerRect(true);

        const bbox = getOperatorBoundingBox(SvInstance.pipeline.operators);

        const [x, y] = [bbox.centerX, bbox.centerY];
        const [w, h] = [container.width, container.height];

        const [kw, kh] = [w / bbox.width, h / bbox.height];
        const k = Math.min(kh * 0.9, kw * 0.9, 1);

        this.shiftX = container.x + container.width / 2 - x * k;
        this.shiftY = container.y + container.height / 2 - y * k;
        this.scale = k;
    }

    /** Checks if elm client rect is visible within editor view (and not overlapped by sidebar).
     *  Only considers editors container and not viewport.
     *  Positive differences indicate that there is enough space for the element.
     * @param {HTMLElement} elm
     * @returns {{fullyVisible: boolean, leftDif: number, topDif: number, rightDif: number, botDif: number}} */
    isFullyVisible(elm) {
        let containerRect = this.getContainerRect(true);
        const elmRect = elm.getBoundingClientRect();

        let leftDif = elmRect.left - containerRect.left;
        let topDif = elmRect.top - containerRect.top;
        let rightDif = containerRect.right - elmRect.right;
        let botDif = containerRect.bottom - elmRect.bottom;

        let fullyVisible = leftDif > 0 && topDif > 0 && rightDif > 0 && botDif > 0;

        return {fullyVisible, leftDif, topDif, rightDif, botDif};
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

        this.selectEditorObject(null);

        this.contextMenu = new MainContextMenu(posX, posY, {forceId, forcePos, preCreatedCb, postCreatedCb});
    }

    /** @param {Number} posX
     * @param {Number} posY
     * @param {SvOperator} operator **/
    openOperatorContextMenu(posX, posY, operator) {
        this.contextMenu = new OperatorContextMenu(posX, posY, operator);
    }

    /** @param {Number} posX
     * @param {Number} posY
     * @param {Group} group **/
    openGroupContextMenu(posX, posY, group) {
        this.contextMenu = new GroupContextMenu(posX, posY, group);
    }

    /** @param {Number} posX
     * @param {Number} posY
     * @param {SvConnection} con **/
    openConnectionContextMenu(posX, posY, con) {
        this.contextMenu = new ConnectionContextMenu(posX, posY, con);
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