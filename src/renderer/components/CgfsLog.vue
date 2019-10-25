<template>
    <div class="cgfs-log">
        <b-card-header>
            <help-popover class="options-list-trigger">
                <table class="options-list">
                    <tr>
                        <td>Revision mode</td>
                        <td>{{ readableBool(config.options.revision) }}</td>
                    </tr>
                    <tr>
                        <td>Assigned to me</td>
                        <td>{{ readableBool(config.options.assigned) }}</td>
                    </tr>
                    <tr>
                        <td>Latest submissions only</td>
                        <td>{{ readableBool(config.options.latest) }}</td>
                    </tr>
                    <tr>
                        <td>ASCII only filenames</td>
                        <td>{{ readableBool(config.options.asciiOnly) }}</td>
                    </tr>
                    <tr>
                        <td>ISO8061 timestamps</td>
                        <td>{{ readableBool(config.options.isoTimestamps) }}</td>
                    </tr>
                </table>
            </help-popover>

            Mounted at:

            <code class="mountpoint" @click="openPath(displayMountpoint)">
                {{ hyphenatedMountpoint
                }}<icon name="share-square" :scale="0.9" class="text-primary" />
            </code>
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
import { ipcRenderer, shell } from 'electron';
import { mapGetters } from 'vuex';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/share-square';

import { downloadFile, uniq } from '@/utils';
import createCircularBuffer from '@/utils/CircularBuffer';
import HelpPopover from '@/components/HelpPopover';

const MAX_EVENTS = 2 ** 15;
const MAX_VISIBLE = 2 ** 10;

// Circular buffer. We define this outside of the component because if it were
// reactive, performance would drop by insane amounts because Vue makes the
// entire thing reactive recursively.
const events = createCircularBuffer(MAX_EVENTS);

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
            initialTitle: document.title,
            proc: null,
            restarting: false,
            eventSize: 0,
            following: true,
            previousY: 0,
            MAX_VISIBLE,
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

        hyphenatedMountpoint() {
            return this.displayMountpoint.replace(/([\\/._-])/g, '\u00AD$1\u00AD');
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

            if (conf.options.asciiOnly) {
                args.push('--ascii-only');
            }

            if (conf.options.isoTimestamps) {
                args.push('--use-iso-timestamps');
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
                document.title = `${this.initialTitle} - ${this.displayMountpoint}`;
            } else {
                document.title = this.initialTitle;
            }
        },
    },

    methods: {
        readableBool(opt) {
            return opt ? 'Enabled' : 'Disabled';
        },

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

            if (process.platform === 'darwin' && event.message.match(/^[^\n]*\/\.DS_Store:/)) {
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

            events.push({
                message: html,
                variant,
                original,
                id: uniq(),
            });

            // Reset to 0 first to force Vue update.
            this.eventSize = 0;
            this.eventSize = events.fill;
            this.scrollToLastEvent();

            if (
                original &&
                original.notify &&
                (original.notify === 'critical' || this.config.verbosity !== 'quiet')
            ) {
                ipcRenderer.send('cgfs-notify', message);
            }
        },

        scrollToLastEvent(behavior = 'auto') {
            const out = this.$refs.output;

            if (out && this.following) {
                this.$nextTick(async () => {
                    out.scrollTo({
                        top: out.scrollHeight,
                        behavior,
                    });
                });
            }
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
            const log = JSON.stringify(events.toList());
            const filename = `cgfs-log-${new Date().toISOString()}.json`;
            downloadFile(log, filename, 'application/json');
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
        events.reset();
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

.card-header,
.options-list {
    cursor: default;
    user-select: none;
}

.mountpoint {
    cursor: pointer;
    border-radius: $border-radius;
    padding: 3px 5px;
    transition: background-color 250ms ease-out;
    -webkit-hyphenate-character: '';

    &:hover {
        background-color: rgba(0, 0, 0, 0.05);
    }

    .fa-icon {
        margin-left: 0.5rem;
        transform: translateY(-1px);
    }
}

.card-header {
    position: relative;
    padding-right: 0.25rem + 2 * $card-spacer-x;
}

.options-list-trigger {
    position: absolute;
    top: $card-spacer-y;
    right: $card-spacer-x;
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
