<template>
    <div class="cgfs-log">
        <div ref="output" class="output">
            <b-alert v-for="(event, i) in events" :key="i" :variant="event.variant" show>{{
                event.event
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

export default {
    name: 'cgfs-log',

    props: {
        args: {
            type: Array,
            required: true,
        },
    },

    data() {
        return {
            proc: null,
            events: [],
        };
    },

    methods: {
        start() {
            const proc = childProcess.spawn('cgfs', this.args);

            proc.stdout.setEncoding('utf-8');
            proc.stderr.setEncoding('utf-8');

            proc.stdout.on('data', this.addEvents);
            proc.stderr.on('data', this.addEvents);

            proc.on('close', () => {
                this.addEvents('INFO: The process has been killed.');
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
            const events = data
                .split('\n')
                .map(event => event)
                .filter(event => event.trim());

            for (const event of events) {
                if (event.slice(0, 4) === 'INFO') {
                    this.events.push({
                        event,
                        variant: 'info',
                    });
                } else if (event.slice(0, 7) === 'WARNING') {
                    this.events.push({
                        event,
                        variant: 'warning',
                    });
                } else if (event.slice(0, 5) === 'DEBUG') {
                    const variant = event.match(/error/i) ? 'danger' : 'secondary';
                    this.events.push({
                        event,
                        variant,
                    });
                } else if (this.events.length) {
                    this.events[this.events.length - 1].event += `\n${event}`;
                    this.events = this.events;
                } else {
                    this.events.push({
                        event,
                        variant: 'primary',
                    });
                }
            }

            this.$nextTick(() => {
                const out = this.$refs.output;
                if (out) {
                    out.scrollTop = out.scrollHeight;
                }
            });
        },
    },

    mounted() {
        this.start();
    },

    destroyed() {
        this.stop();
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
