/* Site-wide polish (every page). Visual only: the site works without it. */
(function () {
  "use strict";

  /* Covers fade in once loaded; a broken cover falls back to the "Cover" placeholder. */
  function reveal(img) { img.classList.add("is-loaded"); }
  function broken(img) {
    var cover = img.closest(".cover");
    img.remove();
    if (cover) cover.textContent = "Cover";
  }
  document.querySelectorAll(".cover img").forEach(function (img) {
    if (img.complete) {
      if (img.naturalWidth) reveal(img); else broken(img);
    } else {
      img.addEventListener("load", function () { reveal(img); }, { once: true });
      img.addEventListener("error", function () { broken(img); }, { once: true });
    }
  });

  /* Stagger entrance animations: each child gets its index as --i (see motion.css). */
  document.querySelectorAll(".book-grid, .carousel__track, .shelf-grid, .review-list, .chips, .genres, .book-info, .current__body")
    .forEach(function (list) {
      Array.prototype.forEach.call(list.children, function (child, i) {
        child.style.setProperty("--i", i);
      });
    });

  /* Shelf filters apply as soon as you pick an option. */
  document.querySelectorAll(".filters .filters__select, .cal__view").forEach(function (select) {
    select.addEventListener("change", function () { select.form.submit(); });
  });

  /* Carousels: arrows page through the row; edges fade where there is more to see. */
  var smooth = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  document.querySelectorAll("[data-carousel]").forEach(function (root) {
    var track = root.querySelector(".carousel__track");
    var prev = root.querySelector("[data-carousel-prev]");
    var next = root.querySelector("[data-carousel-next]");
    function update() {
      var max = track.scrollWidth - track.clientWidth;
      var atStart = track.scrollLeft <= 1;
      var atEnd = track.scrollLeft >= max - 1;
      prev.disabled = atStart;
      next.disabled = atEnd;
      root.classList.toggle("can-left", !atStart);
      root.classList.toggle("can-right", !atEnd);
      root.classList.toggle("is-static", max <= 1);
    }
    function page(dir) {
      track.scrollBy({ left: dir * track.clientWidth * 0.85, behavior: smooth ? "smooth" : "auto" });
    }
    prev.addEventListener("click", function () { page(-1); });
    next.addEventListener("click", function () { page(1); });
    track.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    update();
  });

  /* Nav gets a shadow once the page scrolls under it. */
  var nav = document.querySelector(".nav");
  if (nav) {
    var onScroll = function () { nav.classList.toggle("is-scrolled", window.scrollY > 4); };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  /* Flash messages: click to dismiss; success messages fold away by themselves. */
  function dismiss(li) {
    li.classList.add("is-leaving");
    li.addEventListener("transitionend", function () { li.remove(); }, { once: true });
  }
  document.querySelectorAll(".messages li").forEach(function (li) {
    li.title = "Dismiss";
    li.addEventListener("click", function () { dismiss(li); });
    if (li.classList.contains("success")) setTimeout(function () { dismiss(li); }, 3500);
  });
})();
