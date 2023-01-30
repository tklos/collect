
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

