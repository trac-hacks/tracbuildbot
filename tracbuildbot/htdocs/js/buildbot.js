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

function gen_build_html(data, bb_url, build_button) {
    content = ' \
        <div class="project-header" style="width: 100%;"> \
        ' + data['builder'];

    if (build_button) {
        content += ' \
        <input style="margin-left: 10px;" type="button" name="build" value="Build" \
        onclick="\
$.get(\'/buildbot/build?builder=' + data['builder'] + '\')\
.done(function( result ) { futu_alert(\'Build ' + data['builder'] + '\', result); })\
.fail(function( result ) { futu_alert(\'Build ' + data['builder'] + '\', result, true, "error"); });\
"/>';
    }

    content += ' </div> \
    <div class="inner-build"> ';

    if ('status' in data) {
        content += ' \
        <div class="build-info">Last build \
            <a href="http://' + bb_url + '/builders/' + data['builder'] + '/builds/' + data['num'] + '">' + data['num'] + '</a>: \
            <span class="' + data['status'] + '_build">' + data['status'] + '</span> \
        </div>';

        if (data['status'] == 'failed') {
            content += '<div class="build-info">' + data['error'];
            if ('error_log' in data) {
                content += ' <a href="' + data['error_log'] + '">Log</a>';
            }
            content += '</div> ';
        }

        content += " <br/>";

        content += '<div class="build-info">Started at ' + 
            data['start'].toLocaleFormat('%Y-%m-%d %H:%M:%S') + '</div> ';

        if ('finish' in data && data['finish'] != null) {
            var duration = Math.floor((data['finish'] - data['start']) / 1000);
            var h = Math.floor(duration / 3600);
            var m = Math.floor((duration % 3600) / 60);
            if (m < 10) { m = '0' + m.toString(); }
            var s = (duration % 60);
            if (s < 10) { s = '0' + s.toString(); }
            content += ' <div class="build-info">Finished at ' +
                data['finish'].toLocaleFormat('%Y-%m-%d %H:%M:%S') +
                ' (duration ' + h + ':' + m + ':' + s + ')</div>';
        }

        if ('rev' in data && data['rev'] != "" && 'source' in data) {
            content += ' <div class="build-info">Revision: \
                            <a href="' + trac_url + '/browser/' + data['source'] + '/?rev=' + data['rev'] + '"> \
                                ' + data['rev'].substring(0,7) + '</a> \
                            <a href="' + trac_url + '/changeset/' + data['rev'] + '/' + data['source'] + '" \
                                ><img src="' + trac_url + '/chrome/common/changeset.png"/></a> \
                        </div> ';
        }

    }
    else {
        content += ' <span>Build history is empty</span> ';
    }

    content += '</div>';
    return content

}

function build_request(buildbot_url, builder, num, callback) {
    $.getJSON("http://" + buildbot_url + "/json/builders/" + builder + "/builds/" + num + "?filter=1", function (data) {
        var build = {};

        build["builder"] = data["builderName"];
        build["start"] = new Date(data["times"][0] * 1000);
        build["num"] = data['number'];

        if (data["times"][1] != null) {
            build["finish"] = new Date(data["times"][1] * 1000);
        }

        try {
            var rev = "";
            data["properties"].forEach(function (prop) {
                if (prop[0] == "got_revision" && prop[1] != null) {
                    rev = prop[1];
                }
            });
            build["rev"] = rev;
        } catch (e) { };

        var status = "running";
        if ("text" in data) {
            if (data["text"][0] == "failed") {
                status = "failed";
            }
            else if (data["text"][1] == "successful") {
                status = "successful";
            }
            else {
                status = "unknown";
            }
        }
        build["status"] = status;

        if (status == 'failed') {
            build["error"] = data['text'];
        }

        try {
            data['steps'].forEach(function (step) {
                if ("results" in step && step["results"][0] != 0 && step["results"][0] != 3) {
                    build["error_log"] = step['logs'][0][1];
                }
            });
        } catch (e) { };

        callback(build);
    }).fail(function () {
    });
};


function load_last_build(builder) {
    build_request(buildbot_url, builder, -1,
        function (data) {
            if (builder in buildbot_sources && buildbot_sources[builder] != '') {
                data['source'] = buildbot_sources[builder];
            }
            var element = document.getElementById("builder_" + builder);
            var content = gen_build_html(data, buildbot_url, build_permisson);
            element.innerHTML = content;
        });
};


