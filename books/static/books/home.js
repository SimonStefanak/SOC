/* Homepage "Currently reading" card: review, rating stars and heart.
   Each change is saved in the background to books.views.quick_update,
   which only touches the field that was sent. */
(function () {
  "use strict";

  var box = document.querySelector("[data-quick-url]");
  if (!box) return; // nothing being read, or logged out

  var url = box.dataset.quickUrl;
  var csrf = box.querySelector("[name=csrfmiddlewaretoken]").value;
  var msg = box.querySelector(".shelf__msg");
  var msgTimer;

  function showMessage(text, isError) {
    clearTimeout(msgTimer);
    msg.textContent = text;
    msg.classList.toggle("is-error", !!isError);
    msg.classList.add("is-shown");
    if (!isError) msgTimer = setTimeout(function () { msg.classList.remove("is-shown"); }, 1600);
  }

  function save(fields, keepalive) {
    var data = new FormData();
    data.append("csrfmiddlewaretoken", csrf);
    Object.keys(fields).forEach(function (key) { data.append(key, fields[key]); });
    return fetch(url, {
      method: "POST",
      body: data,
      headers: { "X-Requested-With": "XMLHttpRequest" },
      credentials: "same-origin",
      keepalive: !!keepalive          // lets a last review save finish while the page unloads
    })
      .then(function (res) { return res.json(); })
      .then(function (json) {
        if (json.ok) showMessage("✓ Saved");
        else showMessage(json.errors.join(" "), true);
      })
      .catch(function () { if (!keepalive) showMessage("Couldn't save. Check your connection.", true); });
  }

  // Replay a one-off animation class (motion.css), optionally after a delay
  function pop(el, delay) {
    delay = delay || 0;
    clearTimeout(el._popTimer);
    el.classList.remove("is-pop");
    void el.offsetWidth;
    el.querySelector("svg").style.animationDelay = delay + "ms";
    el.classList.add("is-pop");
    el._popTimer = setTimeout(function () { el.classList.remove("is-pop"); }, delay + 700);
  }

  // the card is a <form> for its markup only: every field saves on its own
  box.addEventListener("submit", function (e) { e.preventDefault(); });

  /* ---------- rating stars ---------- */
  var stars = Array.prototype.slice.call(box.querySelectorAll(".rate__star"));
  var rating = Number(box.dataset.rating) || 0;

  function paintStars(upTo) {
    stars.forEach(function (star) {
      star.classList.toggle("is-on", Number(star.dataset.value) <= upTo);
    });
  }

  stars.forEach(function (star) {
    var value = Number(star.dataset.value);
    star.addEventListener("mouseenter", function () { paintStars(value); });
    star.addEventListener("mouseleave", function () { paintStars(rating); });
    star.addEventListener("click", function () {
      rating = rating === value ? 0 : value;   // click the same star again to clear
      stars.forEach(function (s) { s.setAttribute("aria-pressed", String(Number(s.dataset.value) === rating)); });
      paintStars(rating);
      stars.forEach(function (s, i) { if (i < rating) pop(s, i * 45); });
      save({ rating: rating || "" });
    });
  });

  /* ---------- heart ---------- */
  var like = box.querySelector(".like");
  like.addEventListener("click", function () {
    var on = like.getAttribute("aria-pressed") !== "true";
    like.setAttribute("aria-pressed", String(on));
    pop(like);
    save({ favorite: on ? "true" : "false" });
  });

  /* ---------- review: saves shortly after you stop typing ---------- */
  var review = box.querySelector("textarea");
  var savedText = review.value;
  var typingTimer;

  function saveReview(keepalive) {
    clearTimeout(typingTimer);
    if (review.value === savedText) return;
    savedText = review.value;
    save({ review_text: review.value }, keepalive);
  }

  review.addEventListener("input", function () {
    clearTimeout(typingTimer);
    typingTimer = setTimeout(saveReview, 900);
  });
  review.addEventListener("blur", function () { saveReview(); });
  // leaving the page (e.g. "Mark as finished" or "Book page") with unsaved typing
  window.addEventListener("pagehide", function () { saveReview(true); });
})();
