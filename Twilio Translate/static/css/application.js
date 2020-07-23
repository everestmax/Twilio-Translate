var source = new EventSource("http://bdbba7017120.ngrok.io/twiml");
var words_received = [];

source.addEventListener('greeting',function(event){
    var data = JSON.parse(event.data);
    $('#log').html(data);
}, false);
