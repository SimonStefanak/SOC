# BookLog – project notes

## Before these notes started (2 – 23 Nov 2026)
*Prompt:* A recap of the work done before the notes began.
- Set the project up as a Django site on the local SQLite database, with 10,000 books, genres and series imported from the goodbooks-10k data.
- Built the **book page** from the design: cover, details, genres, catalog rating, shelf dropdown, start/finish dates, your star rating and heart, your review and other readers' reviews. Everything saves to the database; card controls save in the background.
- Built the **homepage**: "Currently reading" card with Mark as finished, "Finished this year" and "Favourite by genre".
- Added **search** (title, author, ISBN), the **To read** and **Finished** shelf pages with filters and sorting, and the **Calendar** page (month / week / day) showing reading spans as bars.
- Renamed the "Read" shelf to "Finished" and "Diary" to "Calendar"; added the site footer, the new logo (#D7DEDF) and a black browser-tab icon; lined the header up with the page content; made the footer black.
- Added a motion layer (`motion.css`, `site.js`): page cross-fades, covers gliding between pages, card lifts, star and heart pops, and a soft glow on gold elements.
- Book page: "More from [series]" carousel above the reviews, using the To read card style.
- Homepage: "Finished this year" became a carousel with dark slate cards; the "Currently reading" card got a review box, rating stars and a pale-blue heart that save in the background.
- Fixed the browser showing old CSS by adding version numbers to stylesheet and script addresses.
- Card titles are shortened: subtitles after ":" or " - " are dropped, and anything over 40 characters ends in "…".
- Fixed `runserver` after the project was moved (rebuilt the virtual environment).
- Noted that book descriptions are empty because the dataset has none; fetching them from Open Library / Google Books was offered but not built yet.

## 23 Nov 2026 · Liked page
*Prompt:* Make a page like "To read" and "Finished" for the books the user liked, called "Liked".
- New **Liked** page at `/liked/` showing every hearted book from any shelf, with the shelf name, the date it was liked and your stars on each card.
- Filters: date liked, genre; sorts: date liked, your rating, title, author.
- Added a `liked_at` date (migration 0005), set when the heart goes on and cleared when it goes off; existing likes got their last-changed date.
- "Liked" link added to the nav and footer.

## 23 Nov 2026 · Project notes PDF
*Prompt:* From now on, write short notes after every prompt and save them into a PDF.
- Created `notes/notes.md` (the notes), `notes/build_pdf.py` (turns them into a PDF) and `notes/BookLog-notes.pdf`.
- Installed `reportlab` (makes the PDF) and `pypdfium2` (previews it) into the project's virtual environment. They are note-taking tools only; the site doesn't use them, so they are not in `requirements.txt`.
- Added this recap of the earlier work, then one entry per prompt from here on.

## 25 Nov 2026 · Settings from environment variables, HTTPS
*Prompt:* Read SECRET_KEY, DEBUG and ALLOWED_HOSTS from environment variables (a local .env file), add STATIC_ROOT and HTTPS settings that switch on only when DEBUG is off.
- `config/settings.py` now reads `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` from the environment, with a small built-in `.env` reader (no new package). Real environment variables win over the file.
- DEBUG is off unless set; a missing secret key stops the site with a clear message instead of running with a weak one.
- New local `.env` (fresh secret key, DEBUG on, localhost) and a commit-safe `.env.example` template. `.env` and `staticfiles/` are git-ignored.
- `STATIC_ROOT = staticfiles/` for `collectstatic` (dry run found 137 files).
- With DEBUG off: http redirects to https, secure login/CSRF cookies, HSTS at 1 hour (adjustable), optional proxy header via `DJANGO_BEHIND_HTTPS_PROXY`.
- `check --deploy` still flags the console email backend (no email is sent by the site yet) and two HSTS options left off on purpose.

## 25 Nov 2026 · Log in and Create account pages
*Prompt:* Update the log in page and create a register page from the new design; "Forgot password?" should not go anywhere yet.
- Log in page rebuilt from the mockup: centred form, serif heading, "Forgot password?" next to the password label (deliberately inactive for now), "No account? Create one" link. A failed log-in keeps the username and shows one friendly error.
- New **Create account** page at `/accounts/register/`: email, username, password, confirm password, with the hints from the design; errors replace the hint under the field they belong to.
- `RegisterForm` (in `forms.py`) requires an email that no other account uses (any capitalisation) and applies Django's password rules (8+ characters, not too common, not all numbers, not like the username).
- After signing up the new account is logged in and taken back to where it came from (`?next=`), or the homepage. Off-site `next` links are ignored.
- Auth styles from the mockup replaced the old login styles in `style.css`; form fields rise in like the rest of the site.

## 25 Nov 2026 · Phone (responsive) design
*Prompt:* Code the smartphone version from the phone mockups and CSS.
- Below 760px the top bar keeps only the logo and avatar, and a fixed **bottom tab bar** takes over: Home, Search, To read, Calendar (instead of the mockup's "Diary"), Finished, with the current page highlighted. It sits above the iPhone home indicator.
- **Book page** reflows into the phone layout: small cover beside the title and genres, full-width shelf, dates and rating rows, heart on the far right, description clamped to one line with **More / Less** (only shown when a book has a description). Hint now reads "Your rating comes from the stars above."
- **Homepage**: compact "Currently reading" card (cover beside text, buttons across the card, review box hidden on phones), **See all** link next to "Finished this year", swipe-only carousels.
- **To read / Finished / Liked**: stacked filters, two cards per row. Search results also two per row.
- **Footer** collapses to three centred lines; calendar and log-in keep their phone rules.
- The old phone rules in `style.css` were replaced by one new phone section; tab bar stays still during page transitions and its icons press in when tapped (`motion.css`).
- Checked with headless Chrome screenshots (logged out and logged in). Open point: the **Liked** page has no tab, so on phones it is only reachable by URL.

## 26 Nov 2026 · Book page: shelf icons instead of the dropdown
*Prompt:* Apply the new book page design: the shelf dropdown becomes three icon buttons.
- The "Add to shelf / To read / Reading / Finished" dropdown is replaced by three icons under the cover: **+** Want to read, **open book** Reading, **tick** Finished. The active one is gold (with the gold glow); hovering shows a small label.
- At most one is on. Clicking the active icon takes the book off your shelf; if the book still has a rating, review, dates or heart, the server keeps it on a shelf (as before) and the matching icon lights up again.
- Saves in the background like the other card controls; a hidden `status` field carries the value, so the server code is unchanged (only the unused `status_choices` was removed from the view).
- The unliked heart outline is now pale blue (#cbf1f5) on the book page too; liked stays gold.
- Phone layout: the icon row takes the dropdown's place, 240px wide. Checked with desktop and phone screenshots.

## 26 Nov 2026 · Shelf icons redesigned
*Prompt:* Make the shelf icons look better, more consistent and easier to understand.
- Replaced the three mismatched icons (solid plus, solid book, thick tick, each nudged into place by hand) with one outline family drawn at the same size and line weight.
- Reused the site's own icons so they mean the same everywhere: **bookmark** = Want to read (as the To read tab), **open book** = Reading, **circle tick** = Finished (as the Finished tab).
- Each icon now has a small visible label underneath instead of a hover-only tooltip (works on phones too).
- Active shelf: gold icon and label on a soft gold pill, matching the phone tab bar's active style; hover shows a faint pill; the gold glow and the pop on click stay.
- On phones the row spans the full width. Checked with desktop and phone screenshots.

## 26 Nov 2026 · Shelf icons: back to bulky, made uniform
*Prompt:* Go back to the bulky first style with no text under the icons, but make all three the same size and thickness.
- Icons are again **plus** (Want to read), **open book** (Reading) and **tick** (Finished), with no labels underneath.
- All three are drawn to one rule: the same 24px box shown at 34px, the same 3px rounded stroke; the book's pages are filled so it stays bulky. No more hand-nudged offsets.
- The name appears in a small label above an icon on hover/keyboard focus; the active one is gold with the glow, the others light grey, white on hover.
- Checked with desktop (zoomed) and phone screenshots.

## 26 Nov 2026 · Calendar page: List view (the "Diary" design)
*Prompt:* Add the Diary design to the Calendar page, but keep the name Calendar.
- The Calendar page now has a header band with the title **Calendar** and a **List | Calendar** switch. "Calendar" is the existing month/week/day grid (still the default); "List" (`/calendar/?view=list`) is the new design.
- List view: **Reading now** first (gold, "Started 12 Nov · day 15"), then finished books grouped by the month they were finished, newest first. Each row: day and weekday, small cover, title and author, dates read with the number of days ("28 Oct – 6 Nov · 10 days", or "No start date"), your stars, a heart if liked, and a review icon that jumps to your review on the book page (new `#reviews` anchor).
- Phone: rows stack (stars, heart and review icon on one line). The mockup hides the List/Calendar switch on phones; it is kept so the month grid stays reachable.
- Fixed during testing: a misplaced `@login_required` that briefly broke the page and unprotected the calendar; the row template now loads its filters.
- Checked with desktop and phone screenshots; logged-out visitors are sent to log in.

## 26 Nov 2026 · Back to the shelf dropdown; "To read" is now "Want"
*Prompt:* Put the original dropdown back for the shelf on the book page, and rename every "to read" to "want".
- Book page: the three shelf icons are replaced by the original dropdown again (Add to shelf / Want / Reading / Finished), gold with the glow when it says Reading, saving on change. The icon styles and script were removed; the dropdown code is restored as it was.
- The shelf "To read" is now called **Want** everywhere: the dropdown, nav, phone tab bar, footer, the shelf page title, its empty message, the homepage button ("Your Want list") and the shelf name on Liked cards. Migration 0006 records the new label; stored data is unchanged.
- The page moved from `/to-be-read/` to `/want/`; the old address redirects there (filters kept), so bookmarks still work.

## 26 Nov 2026 · BookLog wordmark in the navbar
*Prompt:* New navbar CSS; only the logo should change.
- The top bar now shows the logo icon followed by the **BookLog** wordmark (32px, bold, white), as in the new navbar CSS. On phones the wordmark is hidden and only the icon shows, also as in that file.
- Only the logo changed. The other differences in the provided CSS (e.g. moving search into the phone top bar and hiding the avatar there, the old shelf-icon styles) were deliberately not applied.
- The logo link's accessible name is now "BookLog home". Checked with desktop and phone screenshots.

## 26 Nov 2026 · Wordmark with a full stop
*Prompt:* Add "." to the end of the BookLog wordmark.
- The navbar wordmark now reads **BookLog.** The footer's "BookLog" and the copyright line were left as they are.
