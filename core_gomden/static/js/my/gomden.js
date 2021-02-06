"use strict";

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

var DEFAULT_GOMDEN_CONFIG = {};

var Gomden = function () {
    function Gomden(config) {
        _classCallCheck(this, Gomden);

        if (!config) {
            config = {};
        }
        this.config = $.extend({}, DEFAULT_GOMDEN_CONFIG, config);
    }

    _createClass(Gomden, [{
        key: "launch",
        value: function launch() {
            this.loadPage();
        }
    }, {
        key: "loadPage",
        value: function loadPage() {
            var revision = this.config.revision;
            var url = this.config.getPageUrl;
            if (revision > 0) {
                url += "/" + revision;
            }

            var THIS = this;

            $.get(url).success(function (data) {
                THIS.loadPageSuccess(data);
            }).fail(function (data) {
                THIS.loadPageFailure(data);
            });
        }
    }, {
        key: "loadPageFailure",
        value: function loadPageFailure(data) {
            var html = void 0;

            if (this.config.revision === 0) {
                html = "\n                <span class='gomden-title-page-name'>Missing page:" + this.config.pageName + "</span><br><br>\n                <h1># This page does not exist</h1><br>\n                Click the edit button (above) to create this page.\n                ";
            } else {
                html = "Either the page does not exist, or the revision number for the page does not exist";
            }
            $("#gomden-container").html(html);
        }
    }, {
        key: "loadPageSuccess",
        value: function loadPageSuccess(data) {
            console.log(data);
            var html = this.wikipageToHtml(data.page.content);
            var withTitle = "<span class='gomden-title-page-name'>Viewing page:" + data.page.pagename + "</span><br><br>" + html;
            $("#gomden-container").html(withTitle);
            $("#gomden-container .gomden-page-link").each(function (i, value) {
                var pagename = $(value).text().slice(5);
                if (!data.existingPagenames.includes(pagename)) {
                    $(value).addClass("gomden-missing-page-link");
                }
            });

            $("#gomden-container").append("\n            <br>\n            <hr>\n            <p class=\"gomden-content-license\"><br>The contents of this wiki page are licensed under the <a href=\"https://creativecommons.org/licenses/by-sa/3.0/\">CC BY-SA 3.0 License</a>.</p>\n            ");
        }
    }, {
        key: "escapeHtml",
        value: function escapeHtml(text) {
            return $("<div>").text(text).html();
        }
    }, {
        key: "applyHeaders",
        value: function applyHeaders(escaped) {
            return escaped.replace(/^# (.*)$/mg, "<h1 class='gomden-header'># $1</h1>").replace(/^## (.*)$/mg, "<h2 class='gomden-header'>## $1</h2>").replace(/^### (.*)$/mg, "<h3 class='gomden-header'>### $1</h3>").replace(/^#### (.*)$/mg, "<h4 class='gomden-header'>#### $1</h4>");
        }
    }, {
        key: "applyLinks",
        value: function applyLinks(withExternalLinks) {
            return withExternalLinks.replace(/page:([0-9a-z-]{3,100})/mg, "<a class=\"gomden-page-link\" href='" + this.config.viewPageUrl + "$1'>page:$1</a>");
        }
    }, {
        key: "wikipageToHtml",
        value: function wikipageToHtml(content) {
            var escaped = this.escapeHtml(content);
            var withHeaders = this.applyHeaders(escaped);
            var withExternalLinks = this.applyExternalLinks(withHeaders);
            var withLinks = this.applyLinks(withExternalLinks);
            return withLinks.replace(/\n/g, "<br />");
        }

        // From: https://www.codespeedy.com/replace-url-with-clickable-link-javascript/

    }, {
        key: "applyExternalLinks",
        value: function applyExternalLinks(withHeaders) {
            var exp_match = /(\b(https?|):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
            return withHeaders.replace(exp_match, "<a href='$1'>$1</a>");
        }
    }, {
        key: "launchEdit",
        value: function launchEdit() {
            if (this.config.allowEdit) {
                this.loadEditPage();
            } else {
                this.loadNoEditPage();
            }
        }
    }, {
        key: "loadNoEditPage",
        value: function loadNoEditPage() {
            $("#gomden-container").html("\n            <p><a class=\"gomden-page-link\" href=\"" + this.config.viewPageUrl + this.config.pageName + "\">page:" + this.config.pageName + "</a> is owned by @" + this.config.ownerUsername + ", and has disabled other users from editing this page.</p>\n        ");
        }
    }, {
        key: "loadEditPage",
        value: function loadEditPage() {
            var url = this.config.getPageUrl;
            var THIS = this;

            $.get(url).success(function (data) {
                THIS.loadEditPageSuccess(data);
            }).fail(function (data) {
                THIS.loadEditPageFailure(data);
            });
        }

        // Yes, this is janky

    }, {
        key: "loadEditPageSuccess",
        value: function loadEditPageSuccess(data) {
            $("#gomden-container").html("\n            <form action=\"" + this.config.savePageUrl + "\" method=\"post\">\n            <textarea id=\"gomden-editor\" name=\"textedit\" rows=\"15\" style=\"width: 100%\"></textarea>\n            <div><br><button class=\"btn btn-primary\" type=\"submit\">Save</button></div>\n            <p><br>By saving this wiki page, you agree to release your contribution under the <a href=\"https://creativecommons.org/licenses/by-sa/3.0/\">CC BY-SA 3.0 License</a>.</p>\n            <input type=\"hidden\" name=\"csrf_token\" value=\"" + CSRF_TOKEN + "\"/>\n            </form>\n        ");
            $("#gomden-editor").val(data.page.content);
        }

        // Yes, this is janky

    }, {
        key: "loadEditPageFailure",
        value: function loadEditPageFailure(data) {
            $("#gomden-container").html("\n            <form action=\"" + this.config.savePageUrl + "\" method=\"post\">\n            <textarea id=\"gomden-editor\" name=\"textedit\" rows=\"15\" style=\"width: 100%\"></textarea>\n            <div><br><button class=\"btn btn-primary\" type=\"submit\">Save</button></div>\n            <p><br>By saving this wiki page, you agree to release your contribution under the <a href=\"https://creativecommons.org/licenses/by-sa/3.0/\">CC BY-SA 3.0 License</a>.</p>\n            <input type=\"hidden\" name=\"csrf_token\" value=\"" + CSRF_TOKEN + "\"/>\n            </form>\n        ");
            var content = "# This page does not exist\nClick the edit button (above) to create this page.\n";
            $("#gomden-editor").val(content);
        }
    }, {
        key: "launchPermissions",
        value: function launchPermissions() {
            var inside = void 0;

            if (this.config.userid === 0) {
                inside = "\n                <p>You are not logged in. You may not change the permissions for this page.</p>\n                <div>\n                  <input type=\"checkbox\" id=\"allowEdits\" name=\"allowEdits\" disabled>\n                  <label for=\"allowEdits\" class=\"gomden-disabled-text\">Allow edits</label>\n                </div>\n                ";
            } else if (this.config.userid === this.config.ownerUserid) {
                inside = "\n            <div>\n              <input type=\"checkbox\" id=\"allowEdits\" name=\"allowEdits\">\n              <label for=\"allowEdits\">Allow edits</label>\n            </div>\n            <button class=\"btn btn-primary\" type=\"submit\">Save permissions</button>\n            <input type=\"hidden\" name=\"csrf_token\" value=\"" + CSRF_TOKEN + "\"/>";
            } else {
                inside = "\n                <p>You are logged in as @" + this.config.username + ". You may not change the permissions for this page.</p>\n                <div>\n                  <input type=\"checkbox\" id=\"allowEdits\" name=\"allowEdits\" disabled>\n                  <label for=\"allowEdits\" class=\"gomden-disabled-text\">Allow edits</label>\n                </div>\n                ";
            }

            $("#gomden-container").html("\n            <form action=\"" + this.config.savePermissionsUrl + "\" method=\"post\">\n            <p><a class=\"gomden-page-link\" href=\"" + this.config.viewPageUrl + this.config.pageName + "\">page:" + this.config.pageName + "</a> is owned by @" + this.config.ownerUsername + ".</p>\n            " + inside + "\n            </form>\n        ");

            $("#allowEdits").prop("checked", this.config.allowEdits);
        }
    }, {
        key: "launchHistory",
        value: function launchHistory() {
            $("#gomden-container").append("\n            <span class='gomden-title-page-name'>History for page:" + this.config.pageName + "</span><br><br>\n        ");

            var THIS = this;

            this.config.history.forEach(function (h) {
                var record = "\n                <p><a href=\"" + THIS.config.viewPageUrl + THIS.config.pageName + "/" + h.revision + "\">Version " + h.revision + "</a>, by @" + h.username + "</p>\n            ";
                $("#gomden-container").append(record);
            });
        }
    }]);

    return Gomden;
}();