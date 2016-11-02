create_telescope_availability_chart = function(data){
    // data is in the format obtained from the /telescope_availability endpoint
    // data = {'telescope1': [[date, value],[date,value],...], ...}

    var min_date = new Date(8640000000000000);
    var max_date = new Date(-8640000000000000);

    var sorted_telescopes = [];

    for(telescope in data){
        if(data[telescope].length > 0){
            var first_date = new Date(data[telescope][0][0]);
            if(first_date < min_date){
                min_date = first_date;
            }
            var last_date = new Date(data[telescope][data[telescope].length-1][0]);
            if(last_date > max_date){
                max_date = last_date;
            }
        }
        sorted_telescopes[sorted_telescopes.length] = telescope;
    }

    sorted_telescopes.sort();

    var telescope_availability_chart = $('#telescope_availability_chart');
    var availability_chart = $('<table></table>').addClass('availability_chart').addClass('table').addClass('table-bordered');
    availability_chart.addClass("table-condensed");
    var thead = $('<thead></thead>').addClass('thead-default');
    var header_item = $('<th></th>').text('Telescope');
    thead.append(header_item);

    var current_date = new Date(min_date);
    while(current_date <= max_date){
        header_item = $('<th></th>').text(current_date.getMonth()+1 + "/" + current_date.getDate());
        thead.append(header_item);
        current_date.setDate(current_date.getDate() + 1);
    }
    availability_chart.append(thead);
    var tbody = $('<tbody></tbody>').addClass('tbody-default');
    for(i in sorted_telescopes){
        var telescope = sorted_telescopes[i];
        var row = $('<tr></tr>');
        row.append($('<td></td>').text(telescope))
        for(var i = 0; i < data[telescope].length; i++){
            var date = new Date(data[telescope][i][0]);
            if(i == 0 && date.toDateString() != min_date.toDateString()){
                row.append($('<td></td>'));
            }
            var col = $('<td></td>').text(Math.round(100.0*data[telescope][i][1]))
            if(data[telescope][i][1] > 0.75){
                col.addClass('success');
            }
            else if(data[telescope][i][1] > 0.25){
                col.addClass('warning');
            }
            else{
                col.addClass('danger');
            }
            row.append(col);
        }
        tbody.append(row);
    }
    availability_chart.append(tbody);
    telescope_availability_chart.append(availability_chart)

}