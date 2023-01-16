
const COLOURS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"];


$(document).ready(function() {
	var ctx = $("#measurements_plot");
	var config = {
		type: "line",
		data: {
			labels: [],
			datasets: [],
			time_fmt: [],
			xlimits: [],
			xticks: [],
			xticklabels: [],
		},
		options: {
			spanGaps: true,
			tooltips: {
				mode: "index",
				intersect: false,
				bodyFontColor: "#000000",
				bodyFontSize: 14,
				backgroundColor: "rgba(255, 250, 250, 0.7)",
				titleFontColor: "#000000",
				titleFontSize: 14,
				borderColor: "rgba(0, 0, 0, 0.7)",
				borderWidth: 1,
				bodySpacing: 4,
				callbacks: {
					title: function(tooltip_item, data) {
						return data.time_fmt[tooltip_item[0].index];
					},
				},
			},
			hover: {
				mode: "nearest",
				intersect: true,
			},
			scales: {
				xAxes: [{
					type: "linear",
					distribution: "series",
					ticks: {
						callback: function(tick_value, index, ticks) {
							return config.data.xticklabels[index];
						},
					},
					afterBuildTicks: function(axis, ticks) {
						/* Sets axis limits and returns tick locations */
						axis.min = config.data.xlimits[0];
						axis.max = config.data.xlimits[1];
						return config.data.xticks;
					},
				}],
			},
		},
	}

	var plot = new Chart(ctx, config);


	function get_initial_plot_data() {
		var url = $("#get-initial-plot-data-url").val();

		$.ajax({
			type: "GET",
			url: url,
			dataType: "json",

			success: function(data) {
				/* Set plot */
				config.data.labels = data.time;
				config.data.time_fmt = data.time_fmt;
				config.data.xlimits = data.xlimits;
				config.data.xticks = data.xticks;
				config.data.xticklabels = data.xticklabels;

				for (var ds_idx = 0; ds_idx < data.labels.length; ds_idx++) {
					var dataset = {};
					dataset.label = data.labels[ds_idx];

					/* Create data */
					dataset.data = [];
					for (var time_idx = 0; time_idx < data.time.length; time_idx++)
						dataset.data.push({
							x: data.time[time_idx],
							y: data.data[ds_idx][time_idx],
						});

					dataset.borderColor = COLOURS[ds_idx];
					dataset.backgroundColor = COLOURS[ds_idx];
					dataset.fill = false;
					// dataset.lineTension = 0;

					config.data.datasets.push(dataset);
				}

				plot.update();
			},

			error: function(data) {
			},
		});
	}


	get_initial_plot_data();
});

