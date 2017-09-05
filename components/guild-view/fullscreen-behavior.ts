
export let FullscreenBehavior = {

    properties: {
        fullscreen: {
            type: Boolean,
            value: false,
            notify: true,
            observer: 'fullscreenChanged'
        },
        fullscreenIcon: {
            type: String,
            computed: 'computeFullscreenIcon(fullscreen)'
        },
        fullscreenContent: {
            type: Object,
            value: function() {
                return this;
            }
        },
        fullscreenNotifyTarget: {
            type: Object,
            value: function() {
                return this;
            }
        }
    },

    listeners: {
        'fullscreen-canceled': 'handleFullscreenCanceled'
    },

    computeFullscreenIcon: function(fullscreen) {
        return fullscreen ? "fullscreen-exit" : "fullscreen";
    },

    toggleFullscreen: function() {
        this.fullscreen = !this.fullscreen;
    },

    fullscreenChanged: function(val, old) {
        if (old == undefined) return;
        if (val) {
            this.onFullscreen();
            this.fireFullscreenEvent("fullscreen");
        } else {
            this.onFullscreenExit();
            this.fireFullscreenEvent("fullscreen-exit");
        }
    },

    fireFullscreenEvent: function(name) {
        var event = {
            content: this.fullscreenContent,
            notifyTarget: this.fullscreenNotifyTarget
        };
        this.fire(name, event);
    },

    onFullscreen: function() {
        // To be overridden
    },

    onFullscreenExit: function() {
        // To be overridden
    },

    handleFullscreenCanceled: function(e) {
        this.fullscreen = false;
    }
}
