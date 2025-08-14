class _Services {
    constructor() {
        this.services = {};
    }

    registerService(name, service) {
        this.services[name] = service;
    }

    initialize() {
        for(let service of Object.values(this.services))
            service.onInitialize();
    }
}

export class Service {
    constructor(serviceName) {
        Services.registerService(serviceName, this);
    }

    onInitialize() {

    }
}

export const Services = new _Services();