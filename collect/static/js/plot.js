
const COLOURS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"];


$(document).ready(function() {
	var data = JSON.parse(document.getElementById("id-plot-data").textContent);

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

	var ctx = $("#measurements_plot");
	var config = {
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

	var plot = new Chart(ctx, config);
});

