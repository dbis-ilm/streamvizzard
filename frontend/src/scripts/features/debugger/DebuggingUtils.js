import {Mutex} from "async-mutex";

const mutex = new Mutex();

export async function synchronizeExecution(asyncFunc) {
    const release = await mutex.acquire();

    try {
        await asyncFunc();
    } finally {
        release();
    }
}
