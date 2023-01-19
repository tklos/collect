
var config;
var plot;


const COLOURS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"];


$(document).ready(function() {
	var plot_obj = document.getElementById("id-plot-data");
	if (plot_obj === null)
		return;

	var data = JSON.parse(plot_obj.textContent);

	/* Prepare datasets */
	var datasets = [];
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

		datasets.push(dataset);
	}

	config = {
		type: "line",
		data: {
			labels: data.time,
			datasets: datasets,
			titles: data.titles,
			xlimits: data.xlimits,
			xticks: data.xticks,
			xticklabels: data.xticklabels,
		},
		options: {
			spanGaps: true,
			plugins: {
				tooltip: {
					mode: "index",
					intersect: false,
					bodyColor: "#000000",
					bodyFont: {
						size: 14,
					},
					backgroundColor: "rgba(255, 250, 250, 0.7)",
					titleColor: "#000000",
					titleFont: {
						size: 14,
					},
					borderColor: "rgba(0, 0, 0, 0.7)",
					borderWidth: 1,
					bodySpacing: 4,
					boxPadding: 5,
					callbacks: {
						title: function(context) {
							return config.data.titles[context[0].dataIndex];
						},
					},
				},
			},
			hover: {
				mode: "nearest",
				intersect: true,
			},
			scales: {
				x: {
					type: "linear",
					distribution: "series",
					ticks: {
						callback: function(tick_value, index, ticks) {
							return config.data.xticklabels[index];
						},
					},
					afterBuildTicks: function(axis) {
						/* Sets axis limits and tick locations */
						axis.min = config.data.xlimits[0];
						axis.max = config.data.xlimits[1];

						axis.ticks = config.data.xticks.map(v => ({value: v}));
					},
				},
			},
		},
	}

	var chart_el = $("#measurements_plot");

	plot = new Chart(chart_el, config);
});


function update_plot(ctx) {
	/* Update data */
	for (t of ctx.titles)
			config.data.titles.push(t);

	for (var idx = 0; idx < config.data.datasets.length; idx++) {
			var dataset_data = config.data.datasets[idx].data;
			for (var time_idx = 0; time_idx < ctx.time.length; time_idx++)
					dataset_data.push({x: ctx.time[time_idx], y: ctx.data[idx][time_idx]});
	}

	/* Update x axis */
	config.data.xlimits = ctx.xlimits;
	config.data.xticks = ctx.xticks;
	config.data.xticklabels = ctx.xticklabels;

	plot.update();
}


function update_plot_xaxis(ctx) {
	config.data.xlimits = ctx.xlimits;
	config.data.xticks = ctx.xticks;
	config.data.xticklabels = ctx.xticklabels;

	plot.update();
}

