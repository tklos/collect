
const COLOURS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"];

const PLOT_UPDATE_INTERVAL = 60000;



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

			date_from_interval: null,
			last_record_time: null,
			update_handle: null,
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
				/* Fill date form */
				var form = $("#form-date");
				form.find("#id_date_from").val(data.date_from_s);
				form.find("#id_date_to").val(data.date_to_s);

				/* Set plot */
				config.data.labels = data.time;
				config.data.time_fmt = data.time_fmt;
				config.data.xlimits = data.xlimits;
				config.data.xticks = data.xticks;
				config.data.xticklabels = data.xticklabels;

				for (var idx = 0; idx < data.labels.length; idx++) {
					var dataset = {};
					dataset.label = data.labels[idx];

					/* Create data */
					dataset.data = [];
					for (var time_idx = 0; time_idx < data.time.length; time_idx++)
						dataset.data.push({x: data.time[time_idx], y: data.data[idx][time_idx]});

					dataset.borderColor = COLOURS[idx];
					dataset.backgroundColor = COLOURS[idx];
					dataset.fill = false;
					// dataset.lineTension = 0;

					config.data.datasets.push(dataset);
				}

				/* Set updating plot every minute */
				config.data.last_record_time = data.last_record_time;
				if (data.is_until_now)
					config.data.update_handle = setInterval(get_newest_plot_data, PLOT_UPDATE_INTERVAL);

				plot.update();
			},

			error: function(data) {
			}
		});
	}

	get_initial_plot_data();


	$("body").on("submit", "#form-date", function(event) {
		event.preventDefault();

		/* Stop updating plot */
		clearInterval(config.data.update_handle);

		var form = $(this);

		$.ajax({
			type: form.attr("method"),
			url: form.attr("action"),
			data: form.serialize(),
			dataType: "json",

			success: function(data) {
				config.data.time_fmt = data.time_fmt;
				config.data.xlimits = data.xlimits;
				config.data.xticks = data.xticks;
				config.data.xticklabels = data.xticklabels;

				for (var idx = 0; idx < config.data.datasets.length; idx++) {
					dataset_data = [];
					for (var time_idx = 0; time_idx < data.time.length; time_idx++)
						dataset_data.push({x: data.time[time_idx], y: data.data[idx][time_idx]});

					config.data.datasets[idx].data = dataset_data;
				}

				/* Set updating plot every minute */
				config.data.date_from_interval = data.date_from_interval;
				config.data.last_record_time = data.last_record_time;
				if (data.is_until_now)
					config.data.update_handle = setInterval(get_newest_plot_data, PLOT_UPDATE_INTERVAL);

				plot.update();
			},

			error: function(data) {
			}
		});
	});


	function get_newest_plot_data() {
		var url = $("#get-newest-plot-data-url").val();
		var request_data = {
			date_from_interval: config.data.date_from_interval,
			xlimits: config.data.xlimits,
			last_record_time: config.data.last_record_time,
		};

		$.ajax({
			type: "POST",
			url: url,
			data: request_data,
			dataType: "json",

			success: function(data) {
				/* Update data */
				if (data.last_record_time !== null) {
					config.data.last_record_time = data.last_record_time;

					for (t of data.time_fmt)
						config.data.time_fmt.push(t);

					for (var idx = 0; idx < config.data.datasets.length; idx++) {
						var dataset_data = config.data.datasets[idx].data;
						for (var time_idx = 0; time_idx < data.time.length; time_idx++)
							dataset_data.push({x: data.time[time_idx], y: data.data[idx][time_idx]});
					}
				}

				/* Update x axis */
				config.data.xlimits = data.xlimits;
				config.data.xticks = data.xticks;
				config.data.xticklabels = data.xticklabels;

				plot.update();
			},

			error: function(data) {
			},
		});
	}


	/* Set/Reset plot ylimits */
	$("body").on("submit", "#form-ylimits", function(event) {
		event.preventDefault();

		var form = $(this);
		var min_val = parseFloat(form.find("#id_ylimits_min").val());
		var max_val = parseFloat(form.find("#id_ylimits_max").val());

		if (!isNaN(min_val))
			config.options.scales.yAxes[0].ticks.min = min_val;
		if (!isNaN(max_val))
			config.options.scales.yAxes[0].ticks.max = max_val;

		plot.update();
	});

	$("body").on("click", "button.btn-ylimits-reset", function(event) {
		var form = $(this).closest("#form-ylimits");
		form.find("#id_ylimits_min").val("");
		form.find("#id_ylimits_max").val("");

		delete config.options.scales.yAxes[0].ticks.min;
		delete config.options.scales.yAxes[0].ticks.max;

		plot.update();
	});


});

