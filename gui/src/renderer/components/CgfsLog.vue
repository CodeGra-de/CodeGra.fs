<template>
<div class="cgfs-log">
    <div ref="output" class="output">
        <b-alert v-for="event in events"
                 :variant="event.variant"
                 show>{{ event.event }}</b-alert>
    </div>

    <div class="control">
        <b-button variant="primary"
                class="stop-button"
                @click="stop(true)">
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
        config: {
            type: Object,
            required: true,
        },
    },

    data() {
        return {
            proc: null,
            events: [],
        };
    },

    computed: {
        cgfsArgs() {
            const conf = this.config;
            const args = [
                '--url', conf.Institution,
                '--password', conf.Password,
            ];

            switch (conf.Verbosity) {
                case 'verbose':
                    args.push('--verbose');
                    break;
                case 'quiet':
                    args.push('--quiet');
                    break;
                default:
            }

            if (conf.Options.Assigned) {
                args.push('--assigned-to-me');
            }

            if (!conf.Options.Latest) {
                args.push('--all-submissions');
            }

            if (!conf.Options.Revision) {
                args.push('--fixed');
            }

            args.push(conf.Username);
            args.push(conf['Mount point']);

            return args;
        },
    },

    methods: {
        start() {
            const proc = childProcess.spawn(
                'cgfs',
                this.cgfsArgs,
            );

            proc.stdout.setEncoding('utf-8');
            proc.stderr.setEncoding('utf-8');

            proc.on('close', () => {
                this.addEvents('The process has been killed.');
                this.proc = null;
            });

            proc.stdout.on('data', this.addEvents);
            proc.stderr.on('data', this.addEvents);

            this.proc = proc;
        },

        stop(goBack) {
            if (this.proc != null) {
                this.proc.kill();
            }

            if (goBack) {
                this.$emit('stop');
            }
        },

        addEvents(data) {
            const events = data.split('\n')
                .map(event => event)
                .filter(event => event.trim());

            for (const event of events) {
                if (event.match(/error/i)) {
                    this.events.push({
                        event,
                        variant: 'danger',
                    });
                } else if (event.slice(0, 4) === 'INFO') {
                    this.events.push({
                        event,
                        variant: 'success',
                    });
                } else if (event.slice(0, 5) === 'DEBUG') {
                    this.events.push({
                        event,
                        variant: 'info',
                    });
                } else {
                    this.events[this.events.length - 1].event += `\n${event}`;
                }
            }

            this.$nextTick(() => {
                const out = this.$refs.output;
                out.scrollTop = out.scrollHeight;
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
