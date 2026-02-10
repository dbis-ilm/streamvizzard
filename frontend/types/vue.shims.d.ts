import Vue from 'vue'

// Type declaration so that the IDE detects the property

declare module 'vue/types/vue' {
    interface Vue {
        $streamvizzard: StreamVizzard;
    }
}