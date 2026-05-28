
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
		dataset.pointRadius = 0;  /* Don't draw points - major performance improvement */
		dataset.parsing = false;  /* Data is already in {x, y} format - skip parsing */

		datasets.push(dataset);
	}

	/* Chart settings */
	config = {
		type: "line",
		data: {
			labels: data.time,
			datasets: datasets,
			titles: data.titles,
			xlimits: data.xlimits,
			xticks: data.xticks,
			xticklabels: data.xticklabels,
			new_xticks_url: data.new_xticks_url,
			zoom_history: [],
		},
		options: {
			spanGaps: true,
			plugins: {
				// decimation: {
				// 	enabled: true,
				// 	algorithm: 'lttb',  /* Largest Triangle Three Buckets - preserves visual shape */
				// 	samples: 500,  /* Max points to render when zoomed out */
				// },
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
				zoom: {
					zoom: {
						drag: {
							enabled: true,
						},
						mode: 'x',
						onZoomStart: function({chart}) {
							config.data.zoom_history.push({
								xlimits: config.data.xlimits,
								xticks: config.data.xticks,
								xticklabels: config.data.xticklabels,
							});
						},
						onZoomComplete: function({chart}) {
							var new_xlimits = [chart.scales.x.start, chart.scales.x.end];
							fetch_and_apply_xticks(new_xlimits);

							chart.update();
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


	/* Zoom */

	$("body").on("click", "button.btn-zoom-back", function(event) {
		if (config.data.zoom_history.length === 0)
			return;

		var zoom = config.data.zoom_history.pop();

		if (config.data.zoom_history.length === 0) {
			/* Fully zoomed out — recalculate to include any new data */
			recalculate_full_xlimits();
		} else {
			config.data.xlimits = zoom.xlimits;
			config.data.xticks = zoom.xticks;
			config.data.xticklabels = zoom.xticklabels;
		}

		/* Use zoomScale to set X range - this lets Chart.js auto-calculate Y limits */
		plot.zoomScale('x', {min: config.data.xlimits[0], max: config.data.xlimits[1]}, 'default');
	});

	$("body").on("click", "button.btn-zoom-reset", function(event) {
		if (config.data.zoom_history.length === 0)
			return;

		config.data.zoom_history = [];

		recalculate_full_xlimits();

		/* Use zoomScale to set X range - this lets Chart.js auto-calculate Y limits */
		plot.zoomScale('x', {min: config.data.xlimits[0], max: config.data.xlimits[1]}, 'default');
	});

	/* Toggle points visibility */
	$("body").on("click", "button.btn-toggle-points", function(event) {
		var showPoints = plot.data.datasets[0].pointRadius === 0;
		var newRadius = showPoints ? 3 : 0;

		for (var ds of plot.data.datasets) {
			ds.pointRadius = newRadius;
		}

		$(this).text(showPoints ? "Hide Points" : "Show Points");
		plot.update();
	});

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

	/* Update x axis only if not zoomed in */
	if (config.data.zoom_history.length === 0) {
		config.data.xlimits = ctx.xlimits;
		config.data.xticks = ctx.xticks;
		config.data.xticklabels = ctx.xticklabels;
	}

	plot.update();
}


function fetch_and_apply_xticks(new_xlimits) {
	var request_data = {
		xlimits: new_xlimits,
	};

	$.ajax({
		type: "GET",
		url: config.data.new_xticks_url,
		data: request_data,
		contentType: "application/json; charset=utf-8",
		dataType: "json",
		async: false,

		success: function(data) {
			config.data.xlimits = new_xlimits;
			config.data.xticks = data.xticks;
			config.data.xticklabels = data.xticklabels;
		},

		error: function(data) {
			alert("Request failed (error " + data.status + ": " + data.statusText + "); please reload page");
		},
	});
}


function recalculate_full_xlimits() {
	var points = config.data.datasets[0].data;
	fetch_and_apply_xticks([points[0].x, points[points.length - 1].x]);
}
