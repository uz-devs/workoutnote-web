function simpleTimer(elementId, options = {}) {
  var type = options.type || "increase"; // increase, decrease
  var time = type === "increase" ? 0 : 60 * 12;
  var ele = document.getElementById(elementId);

  ele.innerHTML = ` <div>
    <button class="simple-timer_button">
      <span>00 : 00</span>
    </button>
  </div>
  <div>
    <button class="simple-timer_reset-button">Reset</button>
  </div>`;
  console.log(ele)

  var button = ele.getElementsByClassName("simple-timer_button")[0];
  var resetButton = ele.getElementsByClassName("simple-timer_reset-button")[0];
  var timerInnerHtml = button.children[0];
  var isStart = false;
  var isPaused = false;
  var timer;

  button.addEventListener("click", () => {
    if (!isStart) {
      start();
    } else {
      pause();
    }
  });
  resetButton.addEventListener("click", stop);

  function init() {
    time = type === "increase" ? 0 : 60 * 12;
    isPaused = false;
    isStart = false;
    timerInnerHtml.innerHTML = "".padStart(2, 0) + " : " + "".padStart(2, 0);
  }

  function render() {
    if (!isPaused) {
      time = time + (type === "increase" ? 1 : -1);
      var min = Math.floor(time / 60);
      var sec = time % 60;
      timerInnerHtml.innerHTML =
        ("" + min).padStart(2, 0) + " : " + ("" + sec).padStart(2, 0);
    }
  }

  function start() {
    isStart = true;
    timer = setInterval(render, 1000);
  }

  function stop() {
    clearInterval(timer);
    timer = null;
    init();
  }

  function pause() {
    console.log("isPaused", isPaused);
    isPaused = !isPaused;
  }
}
