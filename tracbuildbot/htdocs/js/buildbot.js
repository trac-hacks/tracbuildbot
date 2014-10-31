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
$.ajax(\'/buildbot/build?builder=' + data['builder'] + '\')\
.done(function( result, status ) { futu_alert(\'Build ' + data['builder'] + '\', status + result); })\
.fail(function( jqXHR, textStatus ) { futu_alert(\'Build ' + data['builder'] + '\', jqXHR.responseText, true, \'error\'); });\
"/>';
    }

    content += ' </div> \
    <div class="inner-build"> ';

    if ('status' in data) {
        content += ' \
        <div class="build-info">Last build \
            <a href="' + bb_url + '/builders/' + data['builder'] + '/builds/' + data['num'] + '">' + data['num'] + '</a>: \
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

        var start = new Date(data['start'])
        content += '<div class="build-info">Started at ' +
            start.toLocaleFormat('%Y-%m-%d %H:%M:%S') + '</div> ';

        if ('finish' in data && data['finish'] != null) {
            var finish = new Date(data['finish'])
            var duration = Math.floor((finish - start) / 1000);
            var h = Math.floor(duration / 3600);
            var m = Math.floor((duration % 3600) / 60);
            if (m < 10) { m = '0' + m.toString(); }
            var s = (duration % 60);
            if (s < 10) { s = '0' + s.toString(); }
            content += ' <div class="build-info">Finished at ' +
                finish.toLocaleFormat('%Y-%m-%d %H:%M:%S')  +
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
    console.log("1")
    content += '</div>';
    return content

}

function last_builds_request(trac_url, builders, callback) {
    $.ajax(trac_url + "/buildbot/json/lastbuilds",
        {
            dataType: "json",
            data: { builders: builders.join() },
            traditional: true
        }
    ).done(function (data) {
        console.log("2")
        console.log(data)
        callback(data);
    }).fail(function () {});
};


function load_last_builds(builders) {
    last_builds_request(trac_url, builders,
        function (data) {
            console.log("3")
            var builder;
            for (builder in data) {
                console.log(builder)
                if (builder in buildbot_sources && buildbot_sources[builder] != '') {
                    data[builder]['source'] = buildbot_sources[builder];
                }
                var element = document.getElementById("builder_" + builder);
                var content = gen_build_html(data[builder], buildbot_url, build_permisson);
                element.innerHTML = content;
            }
        });
};


