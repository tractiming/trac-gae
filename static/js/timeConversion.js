function UTC2local(part1, part2){
	var timeString = part1
	timeString = timeString.replace(/-/g, '/');
	timeString = timeString.concat(' ');
	timeString = timeString.concat(part2);
	timeString = timeString.concat(' UTC');
	var time = new Date(timeString);
	time = time.toString();
	return time;
	}

function local2UTC(timeString){
	var utcTime = new Date(timeString);
	utcTime = utcTime.toUTCString();
	var uT = new Date(utcTime);
	uT = uT.toISOString();
	return uT;
}

function localISOString(timeString){
	var utcISO = new Date(timeString)
	var tzo = -utcISO.getTimezoneOffset();
	var dif = tzo >= 0 ? '+' : '-';
	var pad = function(num) {
		var norm = Math.abs(Math.floor(num));
		return (norm < 10 ? '0' : '') + norm;
	};
	return utcISO.getFullYear()
		+ '-' + pad(utcISO.getMonth()+1)
		+ '-' + pad(utcISO.getDate())
		+ 'T' + pad(utcISO.getHours()) 
		+ ':' + pad(utcISO.getMinutes())
		+ ':' + pad(utcISO.getSeconds())
		+ dif + pad(tzo / 60)
		+ ':' + pad(tzo % 60);
}