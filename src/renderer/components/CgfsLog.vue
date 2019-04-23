<template>
    <div class="cgfs-log">
        <div ref="output" class="output" @scroll="onScroll">
            <div
                v-for="i in Math.min(this.eventSize, MAX_VISIBLE)"
                :key="events.get(curStart + i - 1).id"
                :class="`alert alert-${events.get(curStart + i - 1).variant}`"
            >
                <!--
            -->{{ events.get(curStart + i - 1).message
                }}<!--
            --></div>
        </div>

        <div class="control">
            <div class="btn-container">
                <b-button :variant="following ? 'success' : 'primary'" @click="toggleFollowing">
                    {{ following ? 'Following' : 'Follow' }} log
                </b-button>
            </div>

            <div class="btn-container">
                <b-button variant="secondary" @click="exportLog">
                    Export log
                </b-button>
            </div>

            <div class="btn-container">
                <b-button variant="primary" @click="stop(!proc)">
                    <template v-if="proc"
                        >Stop</template
                    >
                    <template v-else
                        >Back</template
                    >
                </b-button>
            </div>
        </div>
    </div>
</template>

<script>
import childProcess from 'child_process';
import readline from 'readline';
import path from 'path';

import { mapGetters } from 'vuex';

import { downloadFile, mod, uniq } from '@/utils';

const MAX_EVENTS = 2 ** 15;
const MAX_VISIBLE = 2 ** 10;

// Circular buffer. We define this outside of the component because if it were
// reactive, performance would drop by insane amounts because Vue makes the
// entire thing reactive recursively.
const events = {
    list: Array(MAX_EVENTS),
    index: 0,
    size: 0,

    get(i) {
        const index = mod(this.index - this.size + i, MAX_EVENTS);
        return this.list[index];
    },

    add(event) {
        this.list[this.index] = event;
        this.index = (this.index + 1) % MAX_EVENTS;
        this.size = Math.min(MAX_EVENTS, this.size + 1);
    },
};

export default {
    name: 'cgfs-log',

    props: {
        jwtToken: {
            type: String,
            required: true,
        },
    },

    data() {
        return {
            proc: null,
            eventSize: 0,
            following: true,
            previousY: 0,
            MAX_VISIBLE,
        };
    },

    computed: {
        ...mapGetters('Config', ['config']),

        events() {
            return events;
        },

        curStart() {
            return Math.max(0, this.eventSize - MAX_VISIBLE);
        },
    },

    methods: {
        start() {
            this.addEvent('Starting...', 'info');

            const proc = childProcess.spawn('cgfs', this.getArgs());

            proc.stdin.write(`${this.jwtToken}`);
            proc.stdin.end();

            proc.stderr.setEncoding('utf-8');
            const rl = readline.createInterface({
                input: proc.stderr,
            });
            rl.on('line', this.addFSEvent);

            proc.on('close', () => {
                rl.close();
                this.addEvent('Stopped.', 'info');
                this.proc = null;
            });

            this.proc = proc;
        },

        getArgs() {
            const conf = this.config;
            const args = ['--gui', '--jwt'];

            if (conf.institution === 'custom') {
                args.push('--url', conf.customInstitution);
            } else {
                args.push('--url', conf.institution);
            }

            switch (conf.verbosity) {
                case 'verbose':
                    args.push('--verbose');
                    break;
                default:
                    break;
            }

            if (conf.options.assigned) {
                args.push('--assigned-to-me');
            }

            if (!conf.options.latest) {
                args.push('--all-submissions');
            }

            if (!conf.options.revision) {
                args.push('--fixed');
            }

            args.push(conf.username);
            args.push(path.join(conf.mountpoint, 'CodeGrade'));

            return args;
        },

        stop(goBack) {
            if (this.proc != null) {
                this.addEvent('Stopping...', 'info');
                this.proc.kill();
                this.proc = null;
            }

            if (goBack) {
                this.$emit('stop');
            }
        },

        addFSEvent(event) {
            try {
                event = JSON.parse(event);
            } catch (e) {
                this.addEvent(`Could not parse event: ${event}`, 'warning');
                return;
            }

            const variant = {
                DEBUG: 'secondary',
                INFO: 'info',
                WARNING: 'warning',
                ERROR: 'danger',
                CRITICAL: 'danger',
            }[event.levelname];

            this.addEvent(event.message, variant, event);
        },

        addEvent(message, variant, original) {
            events.add({
                message,
                variant,
                original,
                id: uniq(),
            });
            // Reset to 0 first to force Vue update.
            this.eventSize = 0;
            this.eventSize = events.size;
            this.scrollToLastEvent();

            if (original && original.notify) {
                // eslint-disable-next-line
                new Notification('CodeGrade Filesystem', {
                    body: message,
                });
            }
        },

        scrollToLastEvent() {
            const out = this.$refs.output;

            // Only scroll when at the bottom.
            if (!out || !this.following) {
                return;
            }

            this.$nextTick(async () => {
                out.scrollTop = out.scrollHeight;
            });
        },

        toggleFollowing() {
            this.following = !this.following;

            if (this.following) {
                this.scrollToLastEvent();
            }
        },

        onScroll(event) {
            const { scrollTop, scrollHeight, clientHeight } = event.target;

            if (scrollTop >= scrollHeight - clientHeight) {
                this.following = true;
            } else if (scrollTop < this.previousY) {
                this.following = false;
            }

            this.previousY = scrollTop;
        },

        exportLog() {
            const log = [];
            for (let i = 0; i < events.size; i++) {
                log.push(events.get(i));
            }
            downloadFile(JSON.stringify(log), 'cgfs-log.json', 'application/json');
        },
    },

    mounted() {
        events.index = 0;
        events.size = 0;
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
    position: relative;
}

.output {
    flex: 1 1 auto;
    overflow-y: auto;
    margin-right: -15px;
    margin-bottom: 1rem;
    white-space: pre-wrap;
}

.output .alert {
    margin-right: 15px;
    word-wrap: break-word;
}

.control {
    display: flex;
    flex: 0 0 auto;
    flex-direction: row;
    padding-right: 15px;
}

.control .btn-container {
    flex: 1 1 33.333%;
}

.btn-container:nth-child(2) {
    text-align: center;
}

.btn-container:last-child {
    text-align: right;
}
</style>
