create_telescope_states_plot = function(request_number, site_to_color, site_code_to_name, block, data){
    var groups = new vis.DataSet();

    var event_types = {"AVAILABLE": 'Available',
                       "NOT_OK_TO_OPEN": 'Weather',
                       "SEQUENCER_DISABLED": 'Manually Disabled',
                       "SITE_AGENT_UNRESPONSIVE": 'No Connection to Telescope',
                       "OFFLINE": 'Manually Disabled',
                       "ENCLOSURE_INTERLOCK": 'Weather',
                       "SEQUENCER_UNAVAILABLE": 'Weather'};

    var items = new vis.DataSet();

    var sorted_telescopes = Object.keys(data).sort(function keyOrder(k1, k2) {
        s1 = k1.split(".")[2]
        s2 = k2.split(".")[2]

        if (s1 < s2) return -1;
        else if (s1 > s2) return +1;
        else if (k1 < k2) return -1;
        else if (k1 > k2) return +1;
        else return 0;
    });

    if(sorted_telescopes.length == 0){
        $('#' + request_number + '-ts-loading').hide()
        $('#' + request_number + '-telescope-states-plot-title').text("Telescope Status Data Not Yet Available")
        $('#' + request_number + '-telescope-states-plot-controls').hide()
        return;
    }

    var g = 0;
    var used_telescopes = {}
    for(var telescope in sorted_telescopes){
        var site = sorted_telescopes[telescope].split('.')[0]
        if (!(site in used_telescopes)){
            used_telescopes[site] = 0;
        }
        used_telescopes[site]++;
        groups.add({id: g,
                    content: site_code_to_name[site] + ' ' + used_telescopes[site],
                    title: sorted_telescopes[telescope],
                    style: 'color: ' + site_to_color[sorted_telescopes[telescope].split(".")[0]] + ';'});
        for(index in data[sorted_telescopes[telescope]]){
            event = data[sorted_telescopes[telescope]][index];
            var reason = '';
            if (event['event_type'] == 'NOT_OK_TO_OPEN' || event['event_type'] == 'ENCLOSURE_INTERLOCK'){
                reason = ': ' + event['event_reason'];
            }
            else if (event['event_type'] == 'SEQUENCER_UNAVAILABLE'){
                reason = ': Telescope initializing';
            }
            items.add({
                group: g,
                title: event_types[event['event_type']] + reason + "<br/>start: " + event['start'].replace('T',' ')
                + "<br/>end: " + event['end'].replace('T',' '),
                className: event['event_type'],
                start: event['start'] + 'Z',
                end: event['end'] + 'Z',
                toggle: 'tooltip',
                html: true,
                type: 'range'
            });
        }
        if(block && block.site == site && block.observatory == sorted_telescopes[telescope].split('.')[1] && block.telescope == sorted_telescopes[telescope].split('.')[2]){
           items.add({
                group: g,
                title: block.type.toLowerCase() + " at " + sorted_telescopes[telescope] + "<br/>" + "start: " + block.start +
                "<br/>end: " + block.end,
                className: block.type,
                start: block.start + 'Z',
                end: block.end + 'Z',
                toggle: 'tooltip',
                html: true,
                type: 'range'
            });
        }
        g++;
    }

    var options = {
        groupOrder: 'id',
        stack: false,
        maxHeight: '450px',
        align: 'left',
        dataAttributes: ['toggle', 'html'],
        selectable: false,
        zoomKey: 'ctrlKey',
        moment: function(date){
            return vis.moment(date).utc();
        }
    };
    var container = document.getElementById(request_number + '-telescope-states-plot');
    var timeline = new vis.Timeline(container);
    timeline.setOptions(options);
    timeline.setGroups(groups);
    timeline.setItems(items);

    $('#' + request_number + '-ts-loading').hide()

    $('#' + request_number + "-telescope-states-plot").find('.vis-label').each(function() {
        $(this).tooltip({'container':'body', 'placement': 'top'});
    });

    //HAX
    $('.vis-group').mouseover(function(){
        $('.vis-item').tooltip({container: 'body'});
    })

    $('#' + request_number + '-telescope-states-zoom-in' + ', #' + request_number + '-telescope-states-zoom-out').click(function(){
        var range = timeline.getWindow();
        var interval = range.end - range.start;
        var percentage = parseFloat($(this).data('percentage'));

        timeline.setWindow({
            start: range.start.valueOf() - interval * percentage,
            end:   range.end.valueOf()   + interval * percentage
        });
    });

    data['plot'] = timeline;
}

