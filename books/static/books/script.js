/* Book page: shelf status, dates, rating stars and heart.
   Every change on the book card is saved in the background (POST with
   X-Requested-With, answered with JSON by books.views.book).
   The review text is only saved by the "Save review" button. */
(function () {
  "use strict";

  var form = document.getElementById("book-form");
  if (!form) return; // logged out: nothing to save

  var statusSelect = document.getElementById("status");
  var ratingInput = document.getElementById("rating-input");
  var favoriteInput = document.getElementById("favorite-input");
  var likeBtn = document.getElementById("like-btn");
  var stars = Array.prototype.slice.call(document.querySelectorAll(".rate__star"));
  var dates = document.getElementById("dates");
  var datesLabel = document.getElementById("dates-label");
  var started = document.getElementById("started");
  var finished = document.getElementById("finished");
  var msg = document.getElementById("shelf-msg");
  var msgTimer;

  /* ---------- saving ---------- */

  function showMessage(text, isError) {
    clearTimeout(msgTimer);
    msg.textContent = text;
    msg.classList.toggle("is-error", !!isError);
    msg.classList.add("is-shown");    // fades in (motion.css)
    if (!isError) msgTimer = setTimeout(function () { msg.classList.remove("is-shown"); }, 1600);
  }

  // Replay a one-off animation class (motion.css), optionally after a delay
  function pop(el, delay) {
    delay = delay || 0;
    clearTimeout(el._popTimer);
    el.classList.remove("is-pop");
    void el.offsetWidth;              // restart the animation if it's already running
    el.querySelector("svg").style.animationDelay = delay + "ms";
    el.classList.add("is-pop");
    el._popTimer = setTimeout(function () { el.classList.remove("is-pop"); }, delay + 700);
  }

  function setStatus(value) {
    statusSelect.value = value;
    statusSelect.dataset.status = value;
  }

  function save() {
    var data = new FormData(form);   // includes the card controls via form="book-form"
    data.delete("review_text");       // the review is saved with its own button
    fetch(form.action, {
      method: "POST",
      body: data,
      headers: { "X-Requested-With": "XMLHttpRequest" },
      credentials: "same-origin"
    })
      .then(function (res) { return res.json(); })
      .then(function (json) {
        if (json.ok) {
          setStatus(json.status);   // the server may pick a shelf for you
          showMessage("✓ Saved");
        } else {
          showMessage(json.errors.join(" "), true);
        }
      })
      .catch(function () { showMessage("Couldn't save. Check your connection.", true); });
  }

  /* ---------- shelf status ---------- */

  statusSelect.addEventListener("change", function () {
    statusSelect.dataset.status = statusSelect.value;
    save();
  });

  /* ---------- dates: Started -> Finished -> "Started – Finished" ---------- */

  function formatDate(value) {
    if (!value) return "dd/mm/yyyy";
    var p = value.split("-");          // yyyy-mm-dd
    return p[2] + "/" + p[1] + "/" + p[0];
  }

  function renderDates() {
    [started, finished].forEach(function (input) {
      var text = input.parentNode.querySelector(".dates__text");
      text.textContent = formatDate(input.value);
      text.classList.toggle("is-empty", !input.value);
    });
    var step = finished.value ? "done" : started.value ? "finish" : "start";
    dates.dataset.step = step;
    datesLabel.textContent = step === "done" ? "Started – Finished" : step === "finish" ? "Finished" : "Started";
  }

  [started, finished].forEach(function (input) {
    // open the calendar when the field is clicked (the input itself is invisible)
    input.addEventListener("click", function () {
      if (input.showPicker) { try { input.showPicker(); } catch (e) { /* not allowed: browser default */ } }
    });
    input.addEventListener("change", function () {
      renderDates();
      save();
    });
  });

  /* ---------- rating stars ---------- */

  function paintStars(upTo) {
    stars.forEach(function (star) {
      star.classList.toggle("is-on", Number(star.dataset.value) <= upTo);
    });
  }

  function currentRating() { return Number(ratingInput.value) || 0; }

  stars.forEach(function (star) {
    var value = Number(star.dataset.value);
    star.addEventListener("mouseenter", function () { paintStars(value); });
    star.addEventListener("mouseleave", function () { paintStars(currentRating()); });
    star.addEventListener("click", function () {
      var next = currentRating() === value ? 0 : value;  // click the same star again to clear
      ratingInput.value = next || "";
      stars.forEach(function (s) { s.setAttribute("aria-pressed", String(Number(s.dataset.value) === next)); });
      paintStars(next);
      // a little wave across the stars you just lit
      stars.forEach(function (s, i) { if (i < next) pop(s, i * 45); });
      save();
    });
  });

  /* ---------- heart ---------- */

  likeBtn.addEventListener("click", function () {
    var on = likeBtn.getAttribute("aria-pressed") !== "true";
    likeBtn.setAttribute("aria-pressed", String(on));
    favoriteInput.value = on ? "true" : "false";
    pop(likeBtn);
    save();
  });
})();
