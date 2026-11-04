DRApp.controller("Unums", "Base", {
    // This Unum, who it reads and who it accepts
    home: function() {
        var unum = DRApp.rest("GET", "api/unum");
        var routes = DRApp.rest("GET", "api/model/route")["routes"];
        var seen = {};
        var followed = [];
        for (var route = 0; route < routes.length; route++) {
            if (routes[route].url && routes[route].holder != unum.unum && !seen[routes[route].holder]) {
                seen[routes[route].holder] = true;
                followed.push(routes[route]);
            }
        }
        this.it = {unum: unum, followed: followed, accepted: DRApp.rest("GET", "api/accept")["accepted"]};
        DRApp.render(this.it);
    },
    join: function() {
        this.it = {url: "", looked: null, apps: []};
        DRApp.render(this.it);
    },
    // Who the Unum at the url says it is, to confirm its fingerprint before joining it
    look: function() {
        var url = $('#url').val();
        var looked = DRApp.rest("POST", "api/lookup", {url: url});
        var apps = Object.keys(looked.apps).filter(function(app) { return app != "unifist-unum"; });
        this.it = {url: url, looked: looked, apps: apps};
        DRApp.render(this.it);
    },
    join_save: function() {
        var body = {url: this.it.url, fingerprint: this.it.looked.fingerprint};
        if ($('#follow').prop('checked')) {
            var follow = {url: body.url, fingerprint: body.fingerprint};
            if ($('#app').length) {
                follow.app = $('#app').val();
            }
            DRApp.rest("POST", "api/follow", follow);
        }
        if ($('#accept').prop('checked')) {
            DRApp.rest("POST", "api/accept", body);
        }
        DRApp.go("home");
    },
    unfollow: function(unum) {
        if (confirm("Stop reading " + unum + "?")) {
            DRApp.rest("DELETE", "api/follow/" + encodeURIComponent(unum));
            this.home();
        }
    },
    revoke: function(unum) {
        if (confirm("Stop letting " + unum + " read this Unum?")) {
            DRApp.rest("DELETE", "api/accept/" + encodeURIComponent(unum));
            this.home();
        }
    }
});

DRApp.template("Join", DRApp.load("join"), null, DRApp.partials);

DRApp.route("home", "/", "Home", "Unums", "home");
DRApp.route("join", "/join", "Join", "Unums", "join");

DRApp.models = DRApp.rest("GET", "api/model")["models"];

DRApp.attach();
