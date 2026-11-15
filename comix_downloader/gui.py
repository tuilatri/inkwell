import customtkinter as ctk
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from tkinter import messagebox, filedialog
import os

try:
    from .comix_scraper import (
        PIL_AVAILABLE, chapter_display, download_chapter, filter_by_group,
        get_manga_info, group_options, search_manga,
    )
except ImportError:
    from comix_scraper import (
        PIL_AVAILABLE, chapter_display, download_chapter, filter_by_group,
        get_manga_info, group_options, search_manga,
    )

ALL_GROUPS = "All groups"


class ComixScraperGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("comix.to Manga Scraper")
        self.geometry("800x700")
        self.resizable(True, True)
        # Below this the three-column action frame clips "Stop All Downloads".
        # Grid does not reflow, so the window degrades to "cannot go smaller"
        # rather than "text disappears".
        self.minsize(760, 560)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        # The log is the one widget that should absorb leftover height. This used
        # to be row 1 (action_frame), which lays its content out from the top and
        # so left ~200px of dead space underneath at every window size.
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1)

        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.input_frame.grid_columnconfigure(0, weight=1)
        self.input_frame.grid_columnconfigure(1, weight=3)
        self.input_frame.grid_columnconfigure(2, weight=1)

        self.url_label = ctk.CTkLabel(self.input_frame, text="Series URL:")
        self.url_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.url_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Enter comix.to series URL")
        self.url_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.info_button = ctk.CTkButton(self.input_frame, text="Get Info", command=self.get_info_thread)
        self.info_button.grid(row=0, column=2, padx=10, pady=5, sticky="e")

        # comix has no working search - the CLI command is a stub too. The row
        # was built disabled and hidden rather than removed, so search can come
        # back without rewriting the layout; it occupied a full prominent row
        # for a control nobody can use.
        self.search_label = ctk.CTkLabel(self.input_frame, text="Search Query:")
        self.search_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.search_entry = ctk.CTkEntry(self.input_frame, placeholder_text="[UNDER DEVELOPMENT] Search not available", state="disabled")
        self.search_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.search_button = ctk.CTkButton(self.input_frame, text="Search (Dev)", command=self.search_manga_thread, state="disabled")
        self.search_button.grid(row=1, column=2, padx=10, pady=5, sticky="e")
        self.search_label.grid_remove()
        self.search_entry.grid_remove()
        self.search_button.grid_remove()

        # comix hosts several scanlation groups publishing the same series, and
        # two groups routinely publish the same chapter number. The list is
        # fetched unfiltered and narrowed in memory - refetching per group would
        # cost a full pager walk each time.
        self.group_label = ctk.CTkLabel(self.input_frame, text="Group:")
        self.group_menu = ctk.CTkOptionMenu(
            self.input_frame, values=[ALL_GROUPS], command=self._on_group_changed)
        self.all_chapters = []
        self.group_menu.set(ALL_GROUPS)

        self.action_frame = ctk.CTkFrame(self)
        self.action_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        # Three columns, not five. At five, every column shrinks as the window
        # narrows while the buttons keep their text width, so "Stop All
        # Downloads" was clipped to "op All Downloa". Grid does not reflow, so
        # the structure has to be chosen rather than adapted - three is the most
        # that fits the widest label at the narrowest supported width.
        self.action_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.list_chapters_button = ctk.CTkButton(self.action_frame, text="List Chapters", command=self.list_chapters_thread)
        self.list_chapters_button.grid(row=0, column=0, padx=10, pady=8, sticky="ew")

        self.download_all_button = ctk.CTkButton(self.action_frame, text="Download All", command=self.download_all_thread)
        self.download_all_button.grid(row=0, column=1, padx=10, pady=8, sticky="ew")

        self.download_range_button = ctk.CTkButton(self.action_frame, text="Download Range", command=self.download_range_thread)
        self.download_range_button.grid(row=0, column=2, padx=10, pady=8, sticky="ew")

        self.output_dir_button = ctk.CTkButton(self.action_frame, text="Select Output Dir", command=self.select_output_directory)
        self.output_dir_button.grid(row=1, column=0, padx=10, pady=8, sticky="ew")

        self.stop_downloads_button = ctk.CTkButton(self.action_frame, text="Stop All Downloads", command=self.stop_all_downloads, fg_color="red")
        self.stop_downloads_button.grid(row=1, column=1, padx=10, pady=8, sticky="ew")

        self.settings_button = ctk.CTkButton(self.action_frame, text="Settings", command=self.open_settings)
        self.settings_button.grid(row=1, column=2, padx=10, pady=8, sticky="ew")

        self.convert_pdf_checkbox = ctk.CTkCheckBox(self.action_frame, text="Convert to PDF")
        self.convert_pdf_checkbox.grid(row=2, column=0, padx=10, pady=8, sticky="w")
        self.convert_pdf_checkbox.bind("<Button-1>", self.toggle_keep_images_checkbox)

        self.convert_cbz_checkbox = ctk.CTkCheckBox(self.action_frame, text="Convert to CBZ")
        self.convert_cbz_checkbox.grid(row=2, column=1, padx=10, pady=8, sticky="w")
        self.convert_cbz_checkbox.bind("<Button-1>", self.toggle_keep_images_checkbox)

        # This label was clipped to "Keep Images (with PDF/C" even at the
        # default width. Its own column is now a third of the frame instead of a
        # fifth, which is most of the fix; wraplength covers anything longer.
        self.keep_images_checkbox = ctk.CTkCheckBox(
            self.action_frame, text="Keep Images (PDF/CBZ)")
        self.keep_images_checkbox.grid(row=2, column=2, padx=10, pady=8, sticky="w")
        self.keep_images_checkbox.configure(state="disabled")

        self.auto_delete_session_checkbox = ctk.CTkCheckBox(self.action_frame, text="Auto-delete Chrome session")
        self.auto_delete_session_checkbox.grid(row=3, column=0, columnspan=3, padx=10, pady=8, sticky="w")

        # Its own colspan-3 row, for the same reason the two rows above are:
        # CTkCheckBox does not pass wraplength through, and a fourth column in
        # row 2 would undo the widening that stopped the buttons clipping.
        # Enabled by default, unlike Keep Images - resume means something with
        # no converter alongside it.
        self.resume_checkbox = ctk.CTkCheckBox(self.action_frame, text="Resume (skip downloaded)")
        self.resume_checkbox.grid(row=4, column=0, columnspan=3, padx=10, pady=8, sticky="w")

        self.output_dir_label = ctk.CTkLabel(self.action_frame, text=f"Output: {os.getcwd()}", wraplength=520)
        self.output_dir_label.grid(row=5, column=0, columnspan=3, padx=10, pady=(0, 8), sticky="w")
        self.output_directory = os.getcwd()

        # Was a ~3px hairline that read as a smudge rather than a progress bar.
        self.progress_bar = ctk.CTkProgressBar(self, orientation="horizontal", height=12)
        self.progress_bar.grid(row=2, column=0, padx=20, pady=(6, 10), sticky="ew")
        self.progress_bar.set(0)

        self.output_text = ctk.CTkTextbox(self, wrap="word")
        self.output_text.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="nsew")
        self.output_text.insert("end", "Welcome to comix.to Manga Scraper GUI!\n\n")
        self.output_text.insert("end", "HOW TO USE:\n")
        self.output_text.insert("end", "1. Paste manga URL in 'Series URL' field\n")
        self.output_text.insert("end", "   Example: https://comix.to/title/y5nn-smoking-behind-the-supermarket-with-you\n")
        self.output_text.insert("end", "2. Click 'Get Info' to load manga details\n")
        self.output_text.insert("end", "3. Use 'Download All' or 'Download Range' to download chapters\n\n")
        self.output_text.insert("end", "NOTE: Search feature is under development. Please use direct URLs.\n")
        self.output_text.configure(state="disabled")

        self.selection_frame = ctk.CTkFrame(self)
        self.selection_frame.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.selection_frame.grid_columnconfigure(1, weight=1)
        self.selection_frame.grid_remove()

        self.selection_label = ctk.CTkLabel(self.selection_frame, text="Enter selection number:")
        self.selection_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.selection_entry = ctk.CTkEntry(self.selection_frame, placeholder_text="Enter number or 0 to cancel")
        self.selection_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.selection_button = ctk.CTkButton(self.selection_frame, text="Select", command=self.process_selection)
        self.selection_button.grid(row=0, column=2, padx=10, pady=10, sticky="e")

        self.manga_title = None
        self.chapters = []
        self.download_executor = None
        self.stop_downloads_flag = threading.Event()
        self.max_image_workers = 15
        self.max_concurrent_downloads = 3
        self.image_format = "original"
        self.jpeg_quality = 92
        self.search_results = None

        # Worker threads must not touch widgets, and Tkinter's own after() is
        # not a safe way out either: it calls tk.createcommand(), which is
        # itself a Tk call, and raises when invoked off the main thread. That
        # was measured - it left the chapter list empty and the group menu
        # unpopulated while still reporting success.
        #
        # So workers push callables onto a plain queue and the main thread
        # drains it. `after` is scheduled once, from __init__, where the
        # calling thread is the main thread.
        self._ui_queue = queue.Queue()
        self.after(50, self._drain_ui_queue)

    def _post_ui(self, func, *args):
        """Hand a UI update to the main thread. Safe to call from a worker."""
        self._ui_queue.put((func, args))

    def _read_checkbox(self, box):
        """A checkbox value, read safely from a worker thread.

        Reading a CustomTkinter widget reaches into Tk, so this hops through the
        queue and waits. It must not use after(): after() registers a Tk command
        and therefore fails on a worker with "main thread is not in main loop".
        """
        if threading.current_thread() is threading.main_thread():
            return box.get() == 1

        result = {}
        done = threading.Event()

        def read():
            try:
                result['value'] = box.get() == 1
            finally:
                done.set()

        self._post_ui(read)
        done.wait(5)
        return result.get('value', False)

    def _drain_ui_queue(self):
        while True:
            try:
                func, args = self._ui_queue.get_nowait()
            except queue.Empty:
                break
            try:
                func(*args)
            except Exception as exc:
                self.output_text.configure(state="normal")
                self.output_text.insert("end", f"UI update failed: {exc}\n")
                self.output_text.configure(state="disabled")
        self.after(50, self._drain_ui_queue)

    def toggle_keep_images_checkbox(self, event):
        if self.convert_pdf_checkbox.get() == 1 or self.convert_cbz_checkbox.get() == 1:
            self.keep_images_checkbox.configure(state="normal")
        else:
            self.keep_images_checkbox.configure(state="disabled")
            self.keep_images_checkbox.deselect()

    def log_message(self, message):
        # Tkinter is not thread-safe. Every worker in this file calls this, and
        # without the queue they all touched the widget directly, which raises
        # "main thread is not in main loop" on a worker. Bounce the call back
        # through the queue rather than rewriting every call site.
        if threading.current_thread() is not threading.main_thread():
            self._post_ui(self.log_message, message)
            return
        self.output_text.configure(state="normal")
        self.output_text.insert("end", message + "\n")
        self.output_text.see("end")
        self.output_text.configure(state="disabled")

    def select_output_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_directory = directory
            self.output_dir_label.configure(text=f"Output: {self.output_directory}")
            self.log_message(f"Output directory set to: {self.output_directory}")

    def get_info_thread(self):
        series_url = self.url_entry.get().strip()
        if not series_url:
            messagebox.showerror("Input Error", "Please enter a series URL.")
            return
        self.log_message(f"Fetching info for: {series_url}")
        self.progress_bar.set(0)
        threading.Thread(target=self._get_info, args=(series_url,)).start()

    def _get_info(self, series_url):
        try:
            self.manga_title, self.all_chapters = get_manga_info(series_url)
            if self.manga_title and self.all_chapters:
                self.log_message(f"Manga Title: {self.manga_title}")
                self.log_message(f"Found {len(self.all_chapters)} chapters.")
                self._populate_group_menu()
            else:
                # Same split as cli.py: the title can come back while the
                # chapter list does not, and that is not a URL problem.
                if not self.manga_title:
                    self.log_message("Could not retrieve the manga title. "
                                     "Check the URL and your connection.")
                else:
                    self.log_message(f"Read the title '{self.manga_title}' "
                                     "but found no chapters.")
        except Exception as e:
            self.log_message(f"Error fetching info: {e}")
        finally:
            # this worker cannot touch the widget; hand it to the main thread
            self._post_ui(self.progress_bar.set, 1)

    def _populate_group_menu(self):
        """Show the group filter, but only when the series has more than one.

        Runs on the worker thread, so the widget work is handed to the main
        thread through the queue rather than done here.
        """
        self._post_ui(self._apply_group_menu, group_options(self.all_chapters))

    def _apply_group_menu(self, options):
        if len(options) < 2:
            # Single-group series: a filter with one option is just noise.
            self.group_label.grid_remove()
            self.group_menu.grid_remove()
            self.group_menu.set(ALL_GROUPS)
            self.chapters = list(self.all_chapters)
            return

        values = [ALL_GROUPS] + [label for label, _ in options]
        self.group_menu.configure(values=values)
        self.group_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.group_menu.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.group_menu.set(ALL_GROUPS)
        self.chapters = list(self.all_chapters)
        self.log_message(
            "This series has chapters from several scanlation groups. "
            "Chapters sharing a number are listed separately and saved under "
            "their own group folder.")

    def _on_group_changed(self, label):
        if label == ALL_GROUPS:
            self.chapters = list(self.all_chapters)
        else:
            gid = dict(group_options(self.all_chapters)).get(label)
            self.chapters = filter_by_group(self.all_chapters, gid)
        total = len(self.all_chapters)
        if self.group_menu.winfo_ismapped():
            self.log_message(
                f"Group filter: {label} — {len(self.chapters)} of {total} chapters")

    def list_chapters_thread(self):
        if not self.chapters:
            messagebox.showinfo("Info", "Please get manga info first using 'Get Info' or 'Search' and selecting a series.")
            return
        self.log_message("\n--- Chapters ---")
        for i, chapter in enumerate(self.chapters):
            # No URL. It is not actionable in a GUI and it was longer than the
            # chapter name it trailed, pushing each line to the edge of the box.
            self.log_message(f"{i+1}. {chapter_display(chapter)}")

    def search_manga_thread(self):
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showerror("Input Error", "Please enter a search query.")
            return
        self.log_message(f"Searching for: {query}")
        self.progress_bar.set(0)
        threading.Thread(target=self._search_manga, args=(query,)).start()

    def _search_manga(self, query):
        try:
            results = search_manga(query)
            if results:
                self.log_message(f"\n--- Search Results for '{query}' ---\n")
                for i, manga in enumerate(results):
                    self.log_message(f"[{i+1}] {manga['title']}")
                    self.log_message(f"    URL: {manga['url']}\n")

                self.search_results = results
                self.log_message("Enter the number of the series you want to select, or 0 to cancel:")
                self.selection_frame.grid()
                self.selection_entry.delete(0, ctk.END)
                self.selection_entry.focus_set()
            else:
                self.log_message(f"No results found for '{query}'.")
        except Exception as e:
            self.log_message(f"Error during search: {e}")
        finally:
            # same rule as _get_info: this worker cannot touch the widget
            self._post_ui(self.progress_bar.set, 1)

    def process_selection(self):
        if not self.search_results:
            return

        try:
            selection_text = self.selection_entry.get().strip()
            selection = int(selection_text)

            if 1 <= selection <= len(self.search_results):
                selected_manga = self.search_results[selection - 1]
                self.url_entry.delete(0, ctk.END)
                self.url_entry.insert(0, selected_manga['url'])
                self.log_message(f"Selected: {selected_manga['title']}. URL set in Series URL field.")
                self.log_message("Fetching info for selected manga...")
                self.selection_frame.grid_remove()
                self.search_results = None
                self.get_info_thread()
            elif selection == 0:
                self.log_message("Search selection cancelled.")
                self.selection_frame.grid_remove()
                self.search_results = None
            else:
                self.log_message("Invalid selection. Please enter a valid number.")
        except ValueError:
            self.log_message("Invalid input. Please enter a number.")

    def download_all_thread(self):
        if not self.chapters:
            messagebox.showinfo("Info", "Please get manga info first using 'Get Info' or 'Search' and selecting a series.")
            return
        self.log_message("\n--- Downloading all chapters ---")
        self.progress_bar.set(0)
        threading.Thread(target=self._download_chapters, args=(self.chapters,)).start()

    def download_range_thread(self):
        if not self.chapters:
            messagebox.showinfo("Info", "Please get manga info first using 'Get Info' or 'Search' and selecting a series.")
            return
        
        range_input = ctk.CTkInputDialog(text="Enter chapter range (e.g., 1-10):", title="Download Range")
        chapter_range_str = range_input.get_input()

        if not chapter_range_str:
            self.log_message("Download range cancelled.")
            return

        try:
            start_chap_str, end_chap_str = chapter_range_str.split('-')
            start_chap = int(start_chap_str)
            end_chap = int(end_chap_str)

            if not (1 <= start_chap <= len(self.chapters) and 1 <= end_chap <= len(self.chapters) and start_chap <= end_chap):
                messagebox.showerror("Input Error", "Invalid chapter range. Please enter valid numbers within the available range.")
                return

            chapters_to_download = self.chapters[start_chap - 1:end_chap]
            self.log_message(f"\n--- Downloading chapters {start_chap} to {end_chap} ---")
            self.progress_bar.set(0)
            threading.Thread(target=self._download_chapters, args=(chapters_to_download,)).start()
        except ValueError:
            messagebox.showerror("Input Error", "Invalid range format. Use 'start-end' (e.g., '1-10').")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def _download_chapters(self, chapters_to_download):
        from comix_downloader.comix_scraper import cleanup_chrome_profile
        
        total_chapters = len(chapters_to_download)
        gui_update_lock = threading.Lock()
        
        # Track overall download statistics
        total_success = 0
        total_failed = 0
        total_images_downloaded = 0
        total_images_expected = 0
        total_skipped = 0
        total_skipped_pages = 0

        def download_single_chapter(chapter, index):
            nonlocal total_success, total_failed, total_images_downloaded, total_images_expected, total_skipped, total_skipped_pages

            # Two groups publish the same chapter number, so the bare title
            # gives two identical log lines and no way to tell them apart.
            label = chapter_display(chapter)

            if self.stop_downloads_flag.is_set():
                with gui_update_lock:
                    self.log_message(f"Skipping {label} (download stopped).")
                return

            with gui_update_lock:
                self.log_message(f"Downloading {label}...")
            try:
                # read off the widgets from the main thread; this runs in a
                # pool and Tk is not reachable from here
                convert_to_pdf = self._read_checkbox(self.convert_pdf_checkbox)
                convert_to_cbz = self._read_checkbox(self.convert_cbz_checkbox)
                keep_images = self._read_checkbox(self.keep_images_checkbox)
                resume = self._read_checkbox(self.resume_checkbox)

                result = download_chapter(
                    chapter['url'], self.manga_title, chapter['title'],
                    self.output_directory, self.stop_downloads_flag,
                    convert_to_pdf, convert_to_cbz, keep_images,
                    self.max_image_workers, self.image_format, self.jpeg_quality,
                    group=chapter.get('group'), resume=resume
                )

                # Update statistics
                if result:
                    if result.get('stopped'):
                        # Stop All was pressed. download_chapter says so on the
                        # result, and the caller must not second-guess it from
                        # the flag: reading the flag here made a deliberate stop
                        # print "0/0 images (INCOMPLETE)".
                        #
                        # No counter. This branch can only run when the flag is
                        # set, which means the summary block below - where a
                        # count would be printed - is skipped entirely, so the
                        # per-chapter line is the whole of what the user sees.
                        with gui_update_lock:
                            self.log_message(f"⏹ {label}: stopped before it finished")
                    elif result.get('skipped'):
                        # --resume doing its job: the chapter ends the run in the
                        # state it was asked for, so it counts as success. Its
                        # pages deliberately stay out of the expected/downloaded
                        # fraction - nothing was fetched, and "0/172 downloaded"
                        # would read as a broken download rather than a clean one.
                        total_skipped += 1
                        total_skipped_pages += result['total_images']
                        # Counted successful as well as skipped: the chapter
                        # ends the run in the state that was asked for. Leaving
                        # it out made a clean resume run print "0 successful".
                        total_success += 1
                        with gui_update_lock:
                            self.log_message(f"⏭ {label}: already on disk ({result['total_images']} pages)")
                    else:
                        total_images_expected += result['total_images']
                        total_images_downloaded += result['downloaded']

                        if result['success']:
                            total_success += 1
                            with gui_update_lock:
                                self.log_message(f"✓ {label}: {result['downloaded']}/{result['total_images']} images")
                        else:
                            total_failed += 1
                            with gui_update_lock:
                                self.log_message(f"⚠ {label}: {result['downloaded']}/{result['total_images']} images (INCOMPLETE)")
                
                if not self.stop_downloads_flag.is_set():
                    with gui_update_lock:
                        self.update_progress(index + 1, total_chapters)
            except Exception as e:
                total_failed += 1
                if not self.stop_downloads_flag.is_set():
                    with gui_update_lock:
                        self.log_message(f"✗ Error downloading {label}: {e}")

        if self.download_executor:
            self.download_executor.shutdown(wait=False, cancel_futures=True)
        self.download_executor = ThreadPoolExecutor(max_workers=self.max_concurrent_downloads)
        self.stop_downloads_flag.clear()

        futures = []
        for i, chapter in enumerate(chapters_to_download):
            if self.stop_downloads_flag.is_set():
                self.log_message("Download stopped by user before starting all chapters.")
                break
            futures.append(self.download_executor.submit(download_single_chapter, chapter, i))
        
        for future in futures:
            try:
                future.result()
            except Exception:
                pass
            if self.stop_downloads_flag.is_set():
                for f in futures:
                    f.cancel()
                break

        self.download_executor.shutdown(wait=True)
        
        # Display download summary
        if not self.stop_downloads_flag.is_set():
            self.log_message("\n=== Download Summary ===")
            skipped_note = f" (including {total_skipped} already on disk)" if total_skipped else ""
            self.log_message(f"Chapters: {total_success} successful{skipped_note}, "
                             f"{total_failed} failed/incomplete (out of {total_chapters})")
            if total_images_expected > 0:
                self.log_message(f"Images: {total_images_downloaded}/{total_images_expected} downloaded")
            if total_skipped_pages:
                self.log_message(f"Pages already on disk, not fetched: {total_skipped_pages}")
            # Not unconditional. It used to print this whatever happened, which
            # is the same lie batch 1 removed from the CLI: a run that lost
            # two of three chapters still ended with this line.
            if total_failed:
                self.log_message(f"⚠ {total_failed} chapter(s) did not complete - re-run, or use Resume to skip what is already there.")
            elif total_skipped == total_chapters and total_skipped:
                self.log_message("Nothing to download - every chapter was already on disk.")
            else:
                self.log_message("All selected chapters downloaded.")
            self._post_ui(self.progress_bar.set, 1)
            
            # Auto-delete Chrome session if checkbox is enabled
            if self._read_checkbox(self.auto_delete_session_checkbox):
                self.log_message("\nCleaning up Chrome session...")
                if cleanup_chrome_profile():
                    self.log_message("✓ Chrome session cleaned up successfully")
                else:
                    self.log_message("⚠ Failed to clean up Chrome session")
        else:
            self.log_message("\nDownloads stopped by user.")
            self._post_ui(self.progress_bar.set, 0)

    def update_progress(self, current, total):
        # same reason as log_message: called from the download thread pool
        if threading.current_thread() is not threading.main_thread():
            self._post_ui(self.update_progress, current, total)
            return
        progress_value = (current / total) if total else 0
        self.progress_bar.set(progress_value)
        self.update_idletasks()

    def stop_all_downloads(self):
        if self.download_executor:
            self.stop_downloads_flag.set()
            self.log_message("Stopping all active downloads...")
        else:
            self.log_message("No active downloads to stop.")

    def open_settings(self):
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Settings")
        settings_window.geometry("500x480")
        settings_window.transient(self)
        settings_window.grab_set()

        ctk.CTkLabel(settings_window, text="Max Concurrent Chapter Downloads:").pack(pady=10)
        self.max_downloads_slider = ctk.CTkSlider(settings_window, from_=1, to=10, number_of_steps=9)
        self.max_downloads_slider.set(self.max_concurrent_downloads)
        self.max_downloads_slider.pack(pady=5)
        self.max_downloads_label = ctk.CTkLabel(settings_window, text=f"Value: {int(self.max_downloads_slider.get())}")
        self.max_downloads_label.pack(pady=5)
        self.max_downloads_slider.bind("<B1-Motion>", self._update_max_downloads_label)
        self.max_downloads_slider.bind("<ButtonRelease-1>", self._update_max_downloads_setting)

        ctk.CTkLabel(settings_window, text="Max Concurrent Image Downloads:").pack(pady=10)
        self.max_image_downloads_slider = ctk.CTkSlider(settings_window, from_=5, to=30, number_of_steps=25)
        self.max_image_downloads_slider.set(self.max_image_workers)
        self.max_image_downloads_slider.pack(pady=5)
        self.max_image_downloads_label = ctk.CTkLabel(settings_window, text=f"Value: {int(self.max_image_downloads_slider.get())}")
        self.max_image_downloads_label.pack(pady=5)
        self.max_image_downloads_slider.bind("<B1-Motion>", self._update_max_image_downloads_label)
        self.max_image_downloads_slider.bind("<ButtonRelease-1>", self._update_max_image_downloads_setting)

        ctk.CTkLabel(settings_window, text="Image Format:").pack(pady=(15, 5))
        format_options = ["original", "png", "jpeg"]
        self.format_menu = ctk.CTkOptionMenu(
            settings_window, 
            values=format_options,
            command=self._set_image_format
        )
        self.format_menu.set(self.image_format)
        self.format_menu.pack(pady=5)
        
        ctk.CTkLabel(settings_window, text="JPEG Quality (50-100):").pack(pady=(10, 5))
        self.jpeg_quality_slider = ctk.CTkSlider(settings_window, from_=50, to=100, number_of_steps=50)
        self.jpeg_quality_slider.set(self.jpeg_quality)
        self.jpeg_quality_slider.pack(pady=5)
        self.jpeg_quality_label = ctk.CTkLabel(settings_window, text=f"Quality: {int(self.jpeg_quality_slider.get())}%")
        self.jpeg_quality_label.pack(pady=5)
        self.jpeg_quality_slider.bind("<B1-Motion>", self._update_jpeg_quality_label)
        self.jpeg_quality_slider.bind("<ButtonRelease-1>", self._update_jpeg_quality_setting)

        ctk.CTkButton(settings_window, text="Close", command=settings_window.destroy).pack(pady=20)
    
    def _set_image_format(self, value):
        self.image_format = value
        self.log_message(f"Image format set to: {value.upper()}")
        # download_chapter prints a warning when a requested format cannot
        # be applied, but the GUI never sees scraper stdout, so repeat it
        # here - at the point of the choice, before anything is downloaded.
        if str(value).lower() in ('png', 'jpeg', 'jpg') \
                and not PIL_AVAILABLE:
            self.log_message(
                f"Pillow is not installed, so {value.upper()} cannot be "
                f"applied. Files will be saved in the original format. "
                f"Install it with: pip install Pillow")
    
    def _update_jpeg_quality_label(self, event):
        self.jpeg_quality_label.configure(text=f"Quality: {int(self.jpeg_quality_slider.get())}%")
    
    def _update_jpeg_quality_setting(self, event):
        self.jpeg_quality = int(self.jpeg_quality_slider.get())
        self.log_message(f"JPEG quality set to: {self.jpeg_quality}%")

    def _update_max_downloads_label(self, event):
        self.max_downloads_label.configure(text=f"Value: {int(self.max_downloads_slider.get())}")

    def _update_max_downloads_setting(self, event):
        new_value = int(self.max_downloads_slider.get())
        if new_value != self.max_concurrent_downloads:
            self.max_concurrent_downloads = new_value
            self.log_message(f"Max concurrent downloads set to: {self.max_concurrent_downloads}")

    def _update_max_image_downloads_label(self, event):
        self.max_image_downloads_label.configure(text=f"Value: {int(self.max_image_downloads_slider.get())}")

    def _update_max_image_downloads_setting(self, event):
        new_value = int(self.max_image_downloads_slider.get())
        if new_value != self.max_image_workers:
            self.max_image_workers = new_value
            self.log_message(f"Max concurrent image downloads set to: {self.max_image_workers}")


def main_gui():
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = ComixScraperGUI()
    app.mainloop()


if __name__ == "__main__":
    main_gui()
