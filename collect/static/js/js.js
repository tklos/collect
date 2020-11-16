
$(document).ready(function() {

	$('[data-toggle="tooltip"]').tooltip();


	/* Download device data */
	$("body").on("submit", "#form-download", function(event) {
		event.preventDefault();

		var form = $(this);

		$.ajax({
			type: form.attr("method"),
			url: form.attr("action"),
			data: form.serialize(),
			// responseType: "blob",
			// dataType: "json",

			beforeSend: function() {
				/* Clear previous errors */
				$("#form-download-errors").remove();
			},

			success: function(data, status, response) {
				var filename = response.getResponseHeader("Content-Disposition").match(/filename="(.+)"/)[1];
				var content_type = response.getResponseHeader("Content-Type");
				var blob = new Blob([data], {type: content_type});

				var link = document.createElement("a");
				link.href = window.URL.createObjectURL(blob);
				link.download = filename;

				document.body.appendChild(link);

				link.click();

				window.URL.revokeObjectURL(link.href);
				document.body.removeChild(link);
			},

			error: function(data) {
				$("#div-download").html(data.responseJSON.html);
			},
		});
	});


	/* Delete device data */
	$("body").on("click", "button.btn-show-hide-data-delete-panel", function(event) {
		var target = $(event.target);
		var div = $("body").find(".div-delete");

		if (div.hasClass("display-none")) {
			target.html("Hide delete panel");
			div.removeClass("display-none");
		} else {
			target.html("Show delete panel");
			div.addClass("display-none");
		}
	});

	// $("#delete-data-modal").on("shown.bs.modal", function (e) {
	$("body").on("click", ".btn-delete-data", function (event) {
		var from_s = $("#id_delete_date_from").val();
		var to_s = $("#id_delete_date_to").val();

		if (from_s === "")
			from_s = "(none)";
		if (to_s === "")
			to_s = "(none)";

		$(".delete-confirm-from").html(from_s);
		$(".delete-confirm-to").html(to_s);
	});

	if ($("#form-delete-errors").length) {
		$("button.btn-show-hide-data-delete-panel").html("Hide delete panel");
		$(".div-delete").removeClass("display-none");
	}


	/* Data panel */
	$("body").on("click", "button.btn-show-hide-data-panel", function(event) {
		var target = $(event.target);
		var div = $("body").find(".div-data");

		if (div.hasClass("display-none")) {
			target.html("Hide data panel");
			div.removeClass("display-none");
		} else {
			target.html("Show data panel");
			div.addClass("display-none");
		}
	});

	$("body").on("click", ".measurement-delete-link", function (event) {
		event.preventDefault();

		var obj = $(this);
		var tr = obj.closest("tr");

		$.ajax({
			type: "GET",
			url: obj.data("url"),
			contentType: "application/json; charset=utf-8",
			dataType: "json",

			success: function(data) {
				tr.addClass("strikeout");
			},

			error: function(data) {
				alert("Request failed (error " + data.status + ": " + data.statusText + "); please reload page");
			}
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
			}
		});
	});


});

