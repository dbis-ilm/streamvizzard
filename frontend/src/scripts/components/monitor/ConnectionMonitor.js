import {clamp, remap} from "@/scripts/tools/Utils";
import $ from "jquery";
import {EVENTS, registerEvent} from "@/scripts/tools/EventHandler";
import {PipelineService, PIPELINE_STATUS} from "@/scripts/services/pipelineState/PipelineService";

// ---------------------- INTERFACE ----------------------

export function initializeConnectionMonitor(editor) {
    // Register visual element for connection
    editor.on("renderconnection", ({el, connection}) => {
        connection.$el = el.querySelector('.main-path');
    })

    registerEvent(EVENTS.CONNECTION_CREATED, addConnectionMonitor);
    registerEvent(EVENTS.CONNECTION_REMOVED, removeConnectionMonitor);
    registerEvent(EVENTS.CONNECTION_DATA_UPDATED, onConnectionDataUpdate);

    registerEvent(EVENTS.PIPELINE_STATUS_CHANGED, (status) => status === PIPELINE_STATUS.STARTING ? reset() : null);

    registerEvent(EVENTS.PIPELINE_STATUS_CHANGED, (status) => status === PIPELINE_STATUS.STARTED ? setupMonitorAnimation() : null);
    registerEvent(EVENTS.PIPELINE_STATUS_CHANGED, (status) => status === PIPELINE_STATUS.STOPPED ? stopMonitorAnimation() : null);

    //Recalculate minMax every few seconds in case max or min are not valid anymore
    window.setInterval(() => {
        if(PipelineService.isPipelineStarted()) calculateMinMax();
    }, 2500);
}

export function resetConnectionMonitor() {
    reset();
}

// -------------------------------------------------------

let monitorLineThickness = [7, 28];
let monitorTPGlobals = [Number.MAX_VALUE, -1]
let monitorTotalGlobals = [Number.MAX_VALUE, -1]

function onConnectionDataUpdate(entry) {
    const conID = entry.id;
    const throughput = entry.tp;
    const total = entry.total;

    const connection = PipelineService.getConnectionByID(conID);

    if(connection != null) {
        if(connection.total !== total) { //If there were new tuples produced we increase tick to play animation
            connection.lastTick = Date.now();
            connection.forward = connection.total < total;
        }

        connection.total = total;
        connection.throughput = throughput;

        updateConnectionStyle(connection);

        updateMinMax(connection);
    }
}

function addConnectionMonitor(con) {
    con.throughput = 0;
    con.total = 0;
    con.lastTick = 0;

    con.animationOffset = 0;
    con.animationSpeed = 0;

    //Create Hover Tooltip
    let jqueryEl = $(con.$el);
    jqueryEl.addClass("connectionPath");
    con.$el.setAttribute("data-id", con.id);
    jqueryEl.css("pointer-events", "none");
    jqueryEl.css("stroke-linecap", "round");

    let pick = jqueryEl.closest("svg").find("#pick");
    pick.append("<title class='conHoverTitle' data-id='" + con.id + "'></title>");
    pick.css("pointer-events", "all");

    // Visual hover for connections
    pick.attr("onmouseover", "this.parentElement.classList.add('hovered');");
    pick.attr("onmouseleave", "this.parentElement.classList.remove('hovered');");

    con.hover = function(show) {
        if(show) con.$el.parentElement.classList.add('hovered');
        else con.$el.parentElement.classList.remove('hovered');
    };

    //Update html to trigger rebind of native title hover
    jqueryEl.closest("svg").prop('outerHTML', jqueryEl.closest("svg").prop('outerHTML'));

    //Update ref since we recreated HTML element
    con.$el = $('.connectionPath[data-id="' + con.id + '"]')[0];

    con.hoverTitle = $('.conHoverTitle[data-id="' + con.id + '"]');

    con.$el.style.strokeDasharray = 48 + "," + 64

    updateConnectionStyle(con);
}

function removeConnectionMonitor() {

}

function resetMinMax() {
    monitorTPGlobals[0] = Number.MAX_VALUE;
    monitorTPGlobals[1] = -1;

    monitorTotalGlobals[0] = Number.MAX_VALUE;
    monitorTotalGlobals[1] = -1;
}

function reset() {
    resetMinMax();

    for(let k of PipelineService.getAllConnections()) {
        k.throughput = 0;
        k.total = 0;
        k.lastTick = 0;

        updateConnectionStyle(k);
    }
}

function updateMinMax(con) {
    let minMaxChanged = false;

    // Check if current value is greater than max
    if(con.total > monitorTotalGlobals[1]) {
        monitorTotalGlobals[1] = con.total * 1.25;

        minMaxChanged = true;
    }

    //Check if current value is smaller than min
    if(con.total < monitorTotalGlobals[0]) {
        monitorTotalGlobals[0] = con.total * 0.8;

        minMaxChanged = true;
    }

    if(con.throughput > monitorTPGlobals[1]) {
        monitorTPGlobals[1] = con.throughput  * 1.25;

        //Will be updated through scheduled updated since this changes frequently
        //minMaxChanged = true;
    }

    if(con.throughput < monitorTPGlobals[0]) {
        monitorTPGlobals[0] = con.throughput  * 0.8;

        //Will be updated through scheduled updated since this changes frequently
        //minMaxChanged = true;
    }

    if(minMaxChanged) {
        for(let k of PipelineService.getAllConnections())  updateConnectionStyle(k);
    }
}

function calculateMinMax() {
    resetMinMax();

    for(let k of PipelineService.getAllConnections()) {
        if(k.total > monitorTotalGlobals[1]) monitorTotalGlobals[1] = k.total * 1.25;
        if(k.total < monitorTotalGlobals[0]) monitorTotalGlobals[0] = k.total * 0.8;

        if(k.throughput > monitorTPGlobals[1]) monitorTPGlobals[1] = k.throughput * 1.25;
        if(k.throughput < monitorTPGlobals[0]) monitorTPGlobals[0] = k.throughput * 0.8;
    }

    for(let k of PipelineService.getAllConnections())  updateConnectionStyle(k);
}

function updateConnectionStyle(connection) {
    connection.hoverTitle.html("Connection ID: " + connection.id + "\nThroughput: " + connection.throughput.toFixed(2) + " tuples / s\nTotal tuples: " + connection.total);

    // -------------- Value Calculation --------------

    let totalClamped = clamp(connection.total, monitorTotalGlobals[0], monitorTotalGlobals[1]);
    let tpClamped = clamp(connection.throughput, monitorTPGlobals[0], monitorTPGlobals[1]);

    // Linear scale
    let val = remap(totalClamped, monitorTotalGlobals[0], monitorTotalGlobals[1], monitorLineThickness[0], monitorLineThickness[1]);

    if(monitorTotalGlobals[1] === -1 && connection.total === 0) val = monitorLineThickness[0]; //Initial State when no max is set

    // -------------- Line Width  --------------

    connection.$el.style.strokeWidth = val;

    // -------------- Animation --------------

    let totalDif = monitorTPGlobals[1] - monitorTPGlobals[0];
    if (totalDif === 0) connection.animationSpeed = 0;
    else connection.animationSpeed = (tpClamped - monitorTPGlobals[0]) / totalDif; // [0, 1]
}

resetMinMax();

// ---------------------------- Animated Connections ----------------------------

const monitorAnimationSpeed = [2, 20]; //How fast the dots are moving
const monitorAnimationRate = 33; //In which ms interval the dots are moved (30fps)

const monitorConAnimationTickDuration = 500; // How many ms the animation will be played before a new tuple must arrive

let monitorAnimator = null;

function setupMonitorAnimation() {
    monitorAnimator = setInterval( function() {
        let now = Date.now();

        let minSpeed = monitorAnimationSpeed[0];
        let maxSpeed = monitorAnimationSpeed[1] - minSpeed;

        //Perform the animation of each connection if it's "active"
        for(let connection of PipelineService.getAllConnections()) {
            //If we did not receive a recent tick, we don't animate this connection
            if(now >= connection.lastTick + monitorConAnimationTickDuration) continue;

            let current = connection.animationOffset - (connection.forward ? 1 : -1) * (minSpeed + maxSpeed * connection.animationSpeed);

            if(!Number.isFinite(current)) current = 0;
            else current = Math.round(current);

            connection.animationOffset = current;

            connection.$el.style.strokeDashoffset = current;
        }
    }, monitorAnimationRate);
}

function stopMonitorAnimation() {
    if(monitorAnimator != null) clearInterval(monitorAnimator);
    monitorAnimator = null;
}
