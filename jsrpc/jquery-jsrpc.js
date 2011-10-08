(function( $ ) {
	var messages = [];
	var force_max = 10;
	var force = 0;
	$.jsrpc_start = function() {
		$.jsrpc_flush();
	};
	$.jsrpc_flush = function() {
		//Encode messages
		len = messages.length;
		encoded = $.toJSON(messages);
		messages = [];
		
		force++;
		if (force > force_max) force = 0;
		if (len > 0 || force == 0) {
			//Send a POST request
			force = 0;
			$.post('ajax.cgi', {'array': encoded}, function(data) {
				data = $.evalJSON(data);
				for (i=0;i<data.length;i++) {
					message = data[i];
					context = window;
					for(j=0;j<message.path.length;j++) {
						context = context[message.path[j]];
					}
					if (message.type == "fn")
						context = context.apply(null, message.args);
					messages.push({type: 'fn', id: message.id, value: context});
				}
			});
		}
		window.setTimeout($.jsrpc_flush, 100);
	};
	$.jsrpc_message = function(message) {
		messages.push({type: 'message', value: message});
	}
})( jQuery );
