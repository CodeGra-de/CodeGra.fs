<template>
    <div class="cgfs-log">
        <b-card-header>
            Mounted at:

            <code class="mountpoint" @click="openPath(displayMountpoint)">
                {{ displayMountpoint
                }}<icon name="share-square" :scale="0.9" class="text-primary" />
            </code>

            <help-popover class="options-list-trigger">
                <table class="options-list">
                    <tr>
                        <td>Revision mode</td>
                        <td>{{ config.options.revision ? 'Enabled' : 'Disabled' }}</td>
                    </tr>
                    <tr>
                        <td>Assigned to me</td>
                        <td>{{ config.options.assigned ? 'Enabled' : 'Disabled' }}</td>
                    </tr>
                    <tr>
                        <td>Latest submissions only</td>
                        <td>{{ config.options.latest ? 'Enabled' : 'Disabled' }}</td>
                    </tr>
                </table>
            </help-popover>
        </b-card-header>

        <b-card-body ref="output" @scroll="onScroll">
            <div
                v-for="i in Math.min(this.eventSize, MAX_VISIBLE)"
                :key="events.get(curStart + i - 1).id"
                :class="`alert alert-${events.get(curStart + i - 1).variant}`"
                v-html="events.get(curStart + i - 1).message"
                @click.capture="openLink"
            />
        </b-card-body>

        <b-card-footer>
            <div class="btn-container">
                <b-dropdown
                    split
                    :variant="running ? 'outline-danger' : 'outline-primary'"
                    :split-variant="running ? 'danger' : 'primary'"
                    @click="running ? stop() : $emit('stop')"
                >
                    <template slot="button-content" v-if="running">
                        Stop
                    </template>
                    <template slot="button-content" v-else>
                        Back
                    </template>

                    <b-dropdown-item @click="restart">
                        Restart
                    </b-dropdown-item>
                </b-dropdown>
            </div>

            <div class="btn-container">
                <b-button variant="outline-primary" @click="exportLog">
                    Export log
                </b-button>
            </div>

            <div class="btn-container">
                <b-button
                    :variant="following ? 'success' : 'outline-primary'"
                    @click="toggleFollowing"
                >
                    {{ following ? 'Following' : 'Follow' }} log
                </b-button>
            </div>
        </b-card-footer>
    </div>
</template>

<script>
import childProcess from 'child_process';
import readline from 'readline';
import path from 'path';

// eslint-disable-next-line
import { shell } from 'electron';
import { mapGetters } from 'vuex';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/share-square';

import { downloadFile, mod, uniq } from '@/utils';
import HelpPopover from '@/components/HelpPopover';

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
            restarting: false,
            eventSize: 0,
            following: true,
            previousY: 0,
            MAX_VISIBLE,
            sep: path.sep,
        };
    },

    computed: {
        ...mapGetters('Config', ['config', 'institutionURL']),

        events() {
            return events;
        },

        curStart() {
            return Math.max(0, this.eventSize - MAX_VISIBLE);
        },

        running() {
            return this.proc !== null || this.restarting;
        },

        displayMountpoint() {
            return `${this.config.mountpoint}${path.sep}CodeGrade${path.sep}`;
        },

        args() {
            const conf = this.config;
            const args = ['--gui', '--jwt'];

            args.push('--url', this.institutionURL);

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
    },

    watch: {
        running(newValue) {
            if (newValue) {
                document.title = `CodeGrade Filesystem - ${this.displayMountpoint}`;
            } else {
                document.title = 'CodeGrade Filesystem';
            }
        },
    },

    methods: {
        start() {
            this.addEvent('Starting...', 'info');

            const proc = childProcess.spawn('cgfs', this.args);

            proc.stderr.setEncoding('utf-8');
            const rl = readline.createInterface({
                input: proc.stderr,
            });
            rl.on('line', this.addFSEvent);

            proc.on('error', err => {
                this.addEvent(
                    `The CodeGrade Filesystem could not be started: ${err.message}`,
                    'danger',
                );
                this.proc = null;
            });

            proc.on('close', () => {
                rl.close();
                this.addEvent('Stopped.', 'info');
                this.proc = null;
            });

            proc.stdin.write(`${this.jwtToken}`);
            proc.stdin.end();

            this.proc = proc;
            this.restarting = false;
        },

        restart() {
            if (this.running) {
                this.restarting = true;
                this.proc.on('close', () => {
                    this.addEvent('Restarting...', 'info');
                    this.start();
                });
                this.stop(true);
            } else {
                this.start();
            }
        },

        stop() {
            if (this.proc != null) {
                this.addEvent('Stopping...', 'info');
                this.proc.kill();
                this.proc = null;
            }
        },

        addFSEvent(event) {
            try {
                event = JSON.parse(event);
            } catch (e) {
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
            const html = this.$htmlEscape(message).replace(
                /(https?:\/\/\S+?)([.,]?(\s|$))/g,
                (_, url, trailing) =>
                    `<a target="_blank" href="${url}">${url}</a>${trailing || ''}`,
            );

            events.add({
                message: html,
                variant,
                original,
                id: uniq(),
            });

            // Reset to 0 first to force Vue update.
            this.eventSize = 0;
            this.eventSize = events.size;
            this.scrollToLastEvent();

            if (
                original &&
                (original.notify === 'critical' ||
                    (original.notify === 'normal' && this.config.verbosity !== 'quiet'))
            ) {
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
            const filename = `cgfs-log-${new Date().toISOString()}.json`;
            downloadFile(JSON.stringify(log), filename, 'application/json');
        },

        openLink(event) {
            if (event.target.closest('[target="_blank"]')) {
                event.preventDefault();
                shell.openExternal(event.target.href);
            }
        },

        openPath(path) {
            shell.openItem(path);
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
        HelpPopover,
        Icon,
    },
};
</script>

<style lang="scss" scoped>
@import '@/_mixins.scss';

.cgfs-log {
    display: flex;
    flex-direction: column;
    min-height: 20rem;
    position: relative;
}

.card-body {
    flex: 1 1 auto;
    overflow: auto;
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

.mountpoint {
    cursor: pointer;
    border-radius: $border-radius;
    padding: 3px 5px;
    transition: background-color 250ms ease-out;

    &:hover {
        background-color: rgba(0, 0, 0, 0.05);
    }

    .fa-icon {
        margin-left: 0.5rem;
        transform: translateY(-1px);
    }
}

.options-list-trigger {
    float: right;
}

.options-list {
    margin-bottom: 0;
    padding-left: 1rem;

    td:first-child {
        padding-right: 0.75rem;
        font-weight: bold;
    }
}
</style>
