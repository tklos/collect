
var COLOURS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]


$(document).ready(function() {
	var ctx = $("#measurements_plot");
	var config = {
		type: "line",
		data: {
			labels: [],
			datasets: [],
		},
		options: {
			tooltips: {
				mode: 'index',
				intersect: false,
				bodyFontColor: "#000000",
				bodyFontSize: 14,
				backgroundColor: "rgba(255, 250, 250, 0.7)",
				titleFontColor: "#000000",
				titleFontSize: 14,
				borderColor: "rgba(0, 0, 0, 0.7)",
				borderWidth: 1,
				bodySpacing: 4,
			},
			hover: {
				mode: 'nearest',
				intersect: true,
			},
		},
	}

	var plot = new Chart(ctx, config);


	function get_plot_data() {
		var get_plot_data_url = $("#get-plot-data-url").val();

		$.ajax({
			type: "GET",
			url: get_plot_data_url,
			dataType: "json",

			success: function(data) {
				config.data.labels = data.time;

				for (idx = 0; idx < data.labels.length; idx++) {
					var dataset = {};
					dataset.label = data.labels[idx];
					dataset.data = data.data[idx];

					dataset.borderColor = COLOURS[idx];
					dataset.backgroundColor = COLOURS[idx];
					dataset.fill = false;

					config.data.datasets.push(dataset);
				}

				plot.update();
			},

			error: function(data) {
			}
		});
	}

	get_plot_data();


});

