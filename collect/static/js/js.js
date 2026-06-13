
$(document).ready(function() {

	$('[data-toggle="tooltip"]').tooltip();


	/* Show/Hide panels */
	$("body").on("click", "button.btn-show-hide-panel", function(event) {
		var target = $(event.target);
		var link = target.closest(".div-show-hide-panel-link");
		var display_div = link.next();

		var msg_show = target.data("show-msg");
		var msg_hide = target.data("hide-msg");

		if (display_div.hasClass("display-none")) {
			target.html(msg_hide);
			display_div.removeClass("display-none");
		} else {
			target.html(msg_show);
			display_div.addClass("display-none");
		}
	});


	/* Show panel if there were any errors in the form included in the given panel */
	$(".form-panel-errors").each(function(idx, el) {
		var display_div = $(el).closest(".div-show-hide-panel");
		var link = display_div.prev();
		var button = link.find(".btn-show-hide-panel");

		button.click();
	});


	/* Bulk delete: select-all checkbox */
	$("body").on("change", ".measurement-select-all", function () {
		var checked = $(this).prop("checked");
		$(this).closest("table").find(".measurement-select-checkbox").prop("checked", checked);
		updateBulkDeleteButton($(this).closest(".div-ajax, .div-measurements-top-controls").closest("div, body"));
	});

	/* Bulk delete: individual checkbox with shift-click range selection */
	var lastCheckedMeasurement = null;
	$("body").on("click", ".measurement-select-checkbox", function (event) {
		var checkboxes = $(this).closest("table").find(".measurement-select-checkbox");
		if (event.shiftKey && lastCheckedMeasurement && lastCheckedMeasurement.closest("table")[0] === $(this).closest("table")[0]) {
			var all = checkboxes.toArray();
			var start = all.indexOf(lastCheckedMeasurement[0]);
			var end = all.indexOf(this);
			if (start > end) { var tmp = start; start = end; end = tmp; }
			var targetState = $(this).prop("checked");
			for (var i = start; i <= end; i++) {
				$(all[i]).prop("checked", targetState);
			}
		}
		lastCheckedMeasurement = $(this);
		var table = $(this).closest("table");
		var all = table.find(".measurement-select-checkbox");
		var allChecked = all.length === all.filter(":checked").length;
		table.find(".measurement-select-all").prop("checked", allChecked);
		updateBulkDeleteButton($(this).closest(".div-ajax, body"));
	});

	function updateBulkDeleteButton(scope) {
		var anyChecked = $(".measurement-select-checkbox:checked").length > 0;
		$(".btn-bulk-delete-measurements").prop("disabled", !anyChecked);
	}

	/* Bulk delete: delete button */
	$("body").on("click", ".btn-bulk-delete-measurements", function (event) {
		var checked = $(".measurement-select-checkbox:checked");
		if (checked.length === 0) return;

		var btn = $(this);
		btn.prop("disabled", true).text("Deleting...");

		var promises = checked.toArray().map(function (cb) {
			var $cb = $(cb);
			var tr = $cb.closest("tr");
			return $.ajax({
				type: "POST",
				url: $cb.data("url"),
				headers: {
					"X-CSRFToken": $cb.data("csrftoken"),
				},
				contentType: "application/json; charset=utf-8",
				dataType: "json",
			}).done(function () {
				tr.addClass("strikeout");
				$cb.prop("checked", false);
			}).fail(function (data) {
				alert("Request failed (error " + data.status + ": " + data.statusText + "); please reload page");
			});
		});

		$.when.apply($, promises).always(function () {
			btn.text("Delete selected");
			updateBulkDeleteButton();
		});
	});


	/* Data panel */
	$("body").on("click", ".measurement-delete-link", function (event) {
		event.preventDefault();

		var obj = $(this);
		var tr = obj.closest("tr");

		$.ajax({
			type: "POST",
			url: obj.data("url"),
			headers: {
				"X-CSRFToken": obj.data("csrftoken"),
			},
			contentType: "application/json; charset=utf-8",
			dataType: "json",

			success: function(data) {
				tr.addClass("strikeout");
			},

			error: function(data) {
				alert("Request failed (error " + data.status + ": " + data.statusText + "); please reload page");
			},
		});
	});


	/* Pagination */
	$("body").on("click", "a.a-paginator", function(event) {
		event.preventDefault();

		var obj = $(this);
		var div = obj.closest(".div-ajax");
		var table = div.find("table.table-ajax");

		$.ajax({
			type: "GET",
			url: obj.data("url"),
			contentType: "application/json; charset=utf-8",
			dataType: "json",

			beforeSend: function() {
				table.addClass("table-inactive");
			},

			success: function(data) {
				div.html(data.html);
			},

			error: function(data) {
				alert("Request failed (error " + data.status + ": " + data.statusText + "); please reload page");
			},
		});
	});


});

