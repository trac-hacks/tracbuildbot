
if (!Date.prototype.toLocaleFormat) {
    Date.prototype.toLocaleFormat = function (format) {
        var f = {
            Y: this.getFullYear(),
            y: this.getFullYear() - (this.getFullYear() >= 2e3 ? 2e3 : 1900),
            m: this.getMonth() + 1,
            d: this.getDate(),
            H: this.getHours(),
            M: this.getMinutes(),
            S: this.getSeconds()
        }, k;
        for (k in f)
            format = format.replace('%' + k, f[k] < 10 ? "0" + f[k] : f[k]);
        return format;
    }
}

function buildbot_build(builder){
    $.ajax("/buildbot/build?builder=" + builder
    ).done(function( result, status ) {
        futu_alert("Build " + builder, status + result);
    }).fail(function( jqXHR, textStatus ){
        futu_alert("Build " + builder, jqXHR.responseText, true, "error"); 
    });
}

function gen_build_html(data) {
    var builder = $("[id='builder_" + data["builder"] + "']");
    var template = $("#build-template").text();
    var output = Mustache.render(template, data);
    builder.empty();
    builder.append(output);
}

function last_builds_request(trac_url, builders, callback) {
    $.ajax(trac_url + "/buildbot/json/lastbuilds",
        {
            dataType: "json",
            data: { builders: builders.join() },
            traditional: true
        }
    ).done(function (data) {
        callback(data);
    }).fail(function (data) {
        console.log(data);
    });
};


function load_last_builds(builders, context) {
    buildbot_sources = context.buildbot_sources;

    last_builds_request(context.trac_url, builders,
        function (builders) {
            for (builder_name in builders) {
                var builder = builders[builder_name];

                var data = {};
                if (typeof builder != "string") {
                    if (builder_name in buildbot_sources && buildbot_sources[builder_name] != '') {
                        builder['source'] = buildbot_sources[builder_name];
                    }

                    var start = new Date(builder.start);
                    var finish = new Date(builder.finish);
                    $.extend(data, context, builder, {
                        status_failed: builder["status"] == "failed",
                        start_str: start.toLocaleFormat('%Y-%m-%d %H:%M:%S'),
                        finish_str: finish.toLocaleFormat('%Y-%m-%d %H:%M:%S'),
                        duration: new Date(finish - start + start.getTimezoneOffset() * 60000).toLocaleFormat('%H:%M:%S'),
                        rev: "rev" in builder ? builder["rev"].substring(0, 7) : "",
                    });
                }
                else {
                    data = {
                        builder: builder_name,
                        request_error: builder,
                    };
                }
                gen_build_html(data);
            }
        });
};


