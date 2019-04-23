<template>
    <b-card no-body class="cgfs-log">
        <cgfs-logo/>

        <hr style="margin: 0;">

        <b-card-header>
            Mounted at: <code>{{ config.mountpoint }}/CodeGrade/</code>
        </b-card-header>

        <b-card-body ref="output" @scroll="onScroll">
            <div
                v-for="i in Math.min(this.eventSize, MAX_VISIBLE)"
                :key="events.get(curStart + i - 1).id"
                :class="`alert alert-${events.get(curStart + i - 1).variant}`"
            >
                <!--
            -->{{ events.get(curStart + i - 1).message
                }}<!--
            --></div>
        </b-card-body>

        <b-card-footer>
            <div class="btn-container">
                <b-button :variant="proc ? 'danger' : 'primary'" @click="stop(!proc)">
                    <template v-if="proc"
                        >Stop</template
                    >
                    <template v-else
                        >Back</template
                    >
                </b-button>
            </div>

            <div class="btn-container">
                <b-button variant="outline-primary" @click="exportLog">
                    Export log
                </b-button>
            </div>

            <div class="btn-container">
                <b-button :variant="following ? 'success' : 'primary'" @click="toggleFollowing">
                    {{ following ? 'Following' : 'Follow' }} log
                </b-button>
            </div>
        </b-card-footer>
    </b-card>
</template>

<script>
import childProcess from 'child_process';
import readline from 'readline';
import path from 'path';

import { mapGetters } from 'vuex';

import CgfsLogo from '@/components/CgfsLogo';
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

        scrollToLastEvent(behavior = 'auto') {
            const out = this.$refs.output;

            // Only scroll when at the bottom.
            if (!out || !this.following) {
                return;
            }

            this.$nextTick(async () => {
                out.scrollTo({
                    top: out.scrollHeight,
                    behavior,
                });
            });
        },

        toggleFollowing() {
            this.following = !this.following;

            if (this.following) {
                this.scrollToLastEvent('smooth');
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

    components: {
        CgfsLogo,
    },
};
</script>

<style lang="scss" scoped>
@import "@/_mixins.scss";

.cgfs-log {
    min-height: 20rem;
    position: relative;
}

.cgfs-logo {
    padding: $card-spacer-x;
}

.card-body {
    overflow-y: auto;
    white-space: pre-wrap;
    word-wrap: break-word;
}

.card-footer {
    flex: 0 0 auto;
}

.alert:last-child {
    margin-bottom: 0;
}

.card-footer {
    display: flex;
    flex-direction: row;
}

.btn-container {
    flex: 1 1 33.333%;

    &:nth-child(2) {
        text-align: center;
    }

    &:nth-child(3) {
        text-align: right;
    }
}
</style>
