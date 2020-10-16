
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

