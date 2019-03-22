<template>
<div class="cgfs-log">
    <div class="output">
        <b-alert v-for="event in events"
                 :variant="eventVariant(event)"
                 show>
            {{ event.line }}
        </b-alert>
    </div>

    <div class="control">
        <b-button variant="primary"
                class="stop-button"
                @click="stop">
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
                this.proc = null;
            });

            proc.stdout.on('data', data => {
                this.addEvent(data, 'stdout');
            });

            proc.stderr.on('data', data => {
                this.addEvent(data, 'stderr');
            });

            this.proc = proc;
        },

        stop() {
            if (this.proc != null) {
                this.proc.kill();
            } else {
                this.$emit('stop');
            }
        },

        addEvent(data, src) {
            const events = data.split('\n')
                .map(line => ({ line: line.trim(), src }))
                .filter(event => event.line);

            this.events.push(...events);
        },

        eventVariant(event) {
            return event.src === 'stdout' ? 'info' : 'danger';
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
    word-wrap: break-word;
}

.control {
    flex: 0 0 auto;
}

.stop-button {
    float: right;
}
</style>
