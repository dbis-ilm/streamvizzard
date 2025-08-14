export const SV_VERSION = "0.9.5";

export function isDockerExecution() {
    return process.env.VUE_APP_DOCKER === 'true'
}