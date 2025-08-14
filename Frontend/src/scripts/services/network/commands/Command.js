// Super class for handling data commands from the server over the socket connection

export class Command {
    constructor(name) {
        this.name = name;
    }

    handleCommand() {}
}
