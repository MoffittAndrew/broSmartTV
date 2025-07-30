window.addEventListener("DOMContentLoaded", () => {
  const websocket = new WebSocket("ws://localhost:9559/");
  document.querySelector(".minus").addEventListener("click", () => {
    websocket.send("message!");
  });
});

var screen = new Screen(); // argument is optional

// on getting local or remote streams
screen.onaddstream = function(e) {
    document.body.appendChild(e.video);
};

// check pre-shared screens
// it is useful to auto-view
// or search pre-shared screens
screen.check();

document.getElementById('share-screen').onclick = function() {
    screen.share();
};

screen.openSignalingChannel = function(callback) {
    return io.connect().on('message', callback);
};