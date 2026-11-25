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
