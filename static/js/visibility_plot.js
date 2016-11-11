create_visibility_plot = function(request_number, site_to_color, site_code_to_name, scheduled_block, data){

    var airmass_data = data['airmass_data']

    if($.isEmptyObject(airmass_data)){
        return;
    }

    var container = document.getElementById(request_number + '-visibility-plot');
    var plot_sites = new vis.DataSet();
    var dataset = new vis.DataSet();
    var i = 0;
    for (var site in airmass_data){
        var airmasses = airmass_data[site]['airmasses'];
        var airmass_times = airmass_data[site]['times'];

        var p = 0;
        var last_time = new Date(airmass_times[0] + 'Z')
        var current_time = last_time
        plot_sites.add({
            id: i,
            content: site_code_to_name[site],
            options: {
                drawPoints: {
                    enabled: true,
                    size: 9,
                    style: 'circle',
                    styles: 'stroke:' +  site_to_color[site] + '; fill: ' + site_to_color[site] + ';visibility: hidden;'
                },
                excludeFromLegend: false,
            },
            style: 'stroke: ' + site_to_color[site] + ';',
        });
        for (p = 0; p < airmass_times.length; p++){
            current_time = new Date(airmass_times[p] + 'Z')
            if (Math.floor(((current_time - last_time)/1000.0)/60.0) > 16.0){
                //another group is used for the case when the horizon is split in the >24 hour period, so we
                //have separate time groups that are above the airmass threshold
                i++;
                plot_sites.add({
                    id: i,
                    content: site_code_to_name[site],
                    options: {
                        drawPoints: {
                            enabled: true,
                            size: 7,
                            style: 'circle',
                            styles: 'stroke:' +  site_to_color[site] + '; fill: ' + site_to_color[site] + ';visibility: hidden;'
                        },
                        excludeFromLegend: true,
                    },
                    style: 'stroke: ' + site_to_color[site] + ';',
                });
            }
            last_time = current_time
            dataset.add([{x: airmass_times[p] + 'Z', y: -airmasses[p],
                          group: i,
                          label: {content: "Site: " + site_code_to_name[site] + "<br>Time: " + airmass_times[p] + "<br>Airmass: " + airmasses[p].toFixed(2), className:'graphtt'}},])
        }
        i++;
    }
    //Now add a group for the airmass limit line
    plot_sites.add({
        id: i,
        content: 'limit',
        options: {
            drawPoints: { enabled: false},
            excludeFromLegend: false,
        },
        style: 'stroke: black;',
    });

    var am_limit = 3.0
    var minTime = new Date(dataset.min('x')['x']);
    minTime.setMinutes(minTime.getMinutes() - 30);
    var maxTime = new Date(dataset.max('x')['x']);
    maxTime.setMinutes(maxTime.getMinutes() + 30);

    if( 'airmass_limit' in data){
        var limitMin = new Date(dataset.min('x')['x']);
        limitMin.setDate(limitMin.getDate() - 30);
        var limitMax = new Date(dataset.max('x')['x']);
        limitMax.setDate(limitMax.getDate() + 30);
        dataset.add([{x: limitMin, y: -1 * data['airmass_limit'], group: i},
                 {x: limitMax, y: -1 * data['airmass_limit'], group: i}]);
        am_limit = data['airmass_limit']
    }
    var options = {
        dataAxis: {
            left: {range:{min: -1.1*am_limit, max: -1},
                format: function(value){ return Math.abs(value).toPrecision(2);},
                title:{text: 'Airmass'}
            },
            // magic number to line up with the telescope state graph below it
            width: '107px'
        },
        orientation: 'top',
        legend: {enabled: true,
            left: {visible: true,
                position:'bottom-right'
            }
        },
        min: minTime,
        max: maxTime,
        zoomKey: 'ctrlKey',
        moment: function(date){
            return vis.moment(date).utc();
        }
    };
    var visibility_graph = new vis.Graph2d(container, dataset, plot_sites, options);

    visibility_graph.on('changed', function(){
        $('#' + request_number + "-visibility-plot").find('.vis-point').each(function() {
            $(this).attr('title', $(this).next().text());
            $(this).attr('data-original-title', $(this).next().text());
            $(this).attr('data-html', "true");
            var label = $(this).next();
            $(this).appendTo($(this).parent());
            label.appendTo($(this).parent());
        });
        $('#' + request_number + "-visibility-plot").find('.vis-point').tooltip({'container': 'body', 'placement': 'top'});
        $('#' + request_number + "-visibility-plot").find('.vis-legend svg path').each(function() {
            $(this).appendTo($(this).parent());
        });
    });

    $('#' + request_number + '-visibility-zoom-in' + ', #' + request_number + '-visibility-zoom-out').click(function(){
        var range = visibility_graph.getWindow();
        var interval = range.end - range.start;
        var percentage = parseFloat($(this).data('percentage'));

        visibility_graph.setWindow({
            start: range.start.valueOf() - interval * percentage,
            end:   range.end.valueOf()   + interval * percentage
        });
    });

    data['plot'] = visibility_graph;
}