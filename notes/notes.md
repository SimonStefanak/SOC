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
