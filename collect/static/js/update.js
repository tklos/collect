
var last_record_time;


function update_measurements_table(table_html) {
    var div = $(".div-measurements-table");
    var ul = div.find("ul.pagination-top");
    var li = ul.find("li.active").first();

    var selected_page = parseInt(li.text());
    if (selected_page != 1)
        return;

    div.html(table_html);
}


function update_data(settings) {
    var request_data = {
        last_record_time: last_record_time,
    };

    $.ajax({
        type: "GET",
        url: settings.url,
        data: request_data,
        dataType: "json",

        success: function(data) {
            if (!data.any_new) {
                /* Update only plot's x-axis limits */
                if (settings.has_plot)
                    update_plot_xaxis(data.plot_ctx);
                return;
            }

            last_record_time = data.last_record_time;

            /* Update number measurements */
            $(".num-measurements").html(data.num_measurements);

            /* Update measurements table */
            update_measurements_table(data.measurements_table_html);

            /* Update map */
            if (settings.has_map)
                update_map(data.map_ctx.locations_l);

            /* Update plot */
            if (settings.has_plot)
                update_plot(data.plot_ctx);
        },
    });
}


$(document).ready(function() {
    var settings = JSON.parse(document.getElementById("id-get-newest-data").textContent);
    last_record_time = settings.last_record_time;

    if (settings.needs_updating)
        setInterval(update_data, 60000, settings);
});
