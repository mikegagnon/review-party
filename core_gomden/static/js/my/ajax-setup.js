"use strict";

$.ajaxSetup({
    beforeSend: function beforeSend(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", CSRF_TOKEN);
        }
    }
});