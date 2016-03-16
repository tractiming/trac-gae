function UTC2local(JSONString){
	var dateString = JSONString.slice(0,10);
	var timeString = JSONString.slice(11,19);

	dateString = dateString.replace(/-/g, '/');
	dateString += ' ' + timeString + ' UTC';

	var d = new Date(dateString);
	return d.toString();
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

// format time in seconds.milliseconds to hh:mm:ss.mil
function formatTime(time) {
	var hours = Math.floor(time / 3600);
	var mins = Math.floor((time - (hours * 3600)) / 60);
	var secs = (time % 60).toFixed(3);
	secs = Math.floor(secs / 10) == 0 ? '0'+secs : secs;
	if (hours == 0)
	{
		return mins.toString() + ':' + secs.toString();
	}
	else{
		mins = Math.floor(mins / 10) == 0 ? '0'+mins : mins;
		return hours.toString() + ':' + mins.toString() + ':' + secs.toString();
	}
}

// convert time string in mm:ss.mil to seconds and milliseconds
function convertToSeconds(timeStr) {
	var times = timeStr.split(':');
	var mins = Number(times[0]);
	var secs = Number(times[1]);
	return ((mins * 60)+secs);
}