<template>
    <div class="cgfs-log">
        <div ref="output" class="output">
            <b-alert v-for="(event, i) in events" :key="i" :variant="event.variant" show>{{
                event.message
            }}</b-alert>
        </div>

        <div class="control">
            <b-button variant="primary" class="stop-button" @click="stop(!proc)">
                <span v-if="proc">Stop</span>
                <span v-else>Back</span>
            </b-button>
        </div>
    </div>
</template>

<script>
import childProcess from 'child_process';

const MAX_EVENTS = 1000;

export default {
    name: 'cgfs-log',

    props: {
        args: {
            type: Array,
            required: true,
        },

        password: {
            type: String,
            required: true,
        },
    },

    data() {
        return {
            proc: null,
            events: [],
            incompleteEvent: '',
        };
    },

    methods: {
        start() {
            const proc = childProcess.spawn('cgfs', this.args);

            proc.stdin.write(`${this.password}`);
            proc.stdin.end();
            this.$emit('clear-password');

            proc.stdout.setEncoding('utf-8');
            proc.stderr.setEncoding('utf-8');

            proc.stdout.on('data', this.addEvents);
            proc.stderr.on('data', this.addEvents);

            proc.on('close', () => {
                this.addEvent('The CodeGrade Filesystem has shut down.');
                this.scrollToLastEvent(true);
                this.proc = null;
            });

            this.proc = proc;
        },

        stop(goBack) {
            if (this.proc != null) {
                this.proc.kill();
                this.proc = null;
            }

            if (goBack) {
                this.$emit('stop');
            }
        },

        addEvents(data) {
            if (this.incompleteEvent) {
                data = this.incompleteEvent + data;
            }

            const events = data.split('\n');

            events.forEach((event, i) => {
                try {
                    event = JSON.parse(event);
                } catch (e) {
                    if (i === events.length - 1) {
                        this.incompleteEvent = event;
                    } else {
                        this.addEvent(`Could not parse event: ${event}`, 'warning');
                    }
                    return;
                }

                const variant = {
                    DEBUG: 'secondary',
                    INFO: 'info',
                    WARNING: 'warning',
                    ERROR: 'danger',
                    CRITICAL: 'danger',
                }[event.levelname];

                const message = event.msg;

                this.addEvent(message, variant);
            });

            this.scrollToLastEvent();
        },

        addEvent(message, variant = 'info') {
            this.events.push({ message, variant });
            this.events = this.events.slice(-MAX_EVENTS);
        },

        scrollToLastEvent(force = false) {
            const out = this.$refs.output;

            // Only scroll when at the bottom.
            if (!out || (!force && out.scrollTop + out.clientHeight < out.scrollHeight)) {
                return;
            }

            this.$nextTick(() => {
                out.scrollTop = out.scrollHeight;
            });
        },
    },

    mounted() {
        this.start();

        window.addEventListener('beforeunload', this.stop);
    },

    destroyed() {
        this.stop();

        window.removeEventListener('beforeunload', this.stop);
    },
};
</script>

<style lang="css" scoped>
.cgfs-log {
    width: 100%;
    max-width: 1024px;
    display: flex;
    flex-direction: column;
    margin: 0 auto;
}

.output {
    flex: 1 1 auto;
    overflow-y: auto;
    margin-right: -15px;
    margin-bottom: 1rem;
}

.output .alert {
    margin-right: 15px;
    white-space: pre-wrap;
    word-wrap: break-word;
}

.control {
    flex: 0 0 auto;
}

.stop-button {
    float: right;
}
</style>
