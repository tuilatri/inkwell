import typer
from typing_extensions import Annotated
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import sys

try:
    from .comix_scraper import (
        chapter_display, download_chapter, get_manga_info, group_options,
        search_manga,
    )
except ImportError:
    from comix_scraper import (
        chapter_display, download_chapter, get_manga_info, group_options,
        search_manga,
    )

if sys.platform.startswith('win'):
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        elif hasattr(sys.stdout, 'encoding') and sys.stdout.encoding.lower() != 'utf-8':
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

app = typer.Typer(help="comix.to Manga Scraper CLI. Download manga chapters from comix.to with full pagination support.")
console = Console()

# Measured on one comix series: a chapter is ~130 images at ~120 KB each, so
# about 14 MB. Extrapolated to a 286-chapter series that is roughly 4 GB, which
# is worth saying before anything is written rather than after. It is an
# average, not a promise - a series with fewer, larger pages will differ. The
# exact figure is accumulated from the files during the run.
_ESTIMATED_MB_PER_CHAPTER = 14.0


def _human_bytes(n):
    """Format a byte count the way a disk tool would."""
    n = float(n)
    sign = "-" if n < 0 else ""
    n = abs(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024.0:
            return f"{sign}{n:.1f} {unit}"
        n /= 1024.0
    return f"{sign}{n:.1f} PB"


@app.command(name="info", help="Get information about a manga series.")
def get_info(
    series_url: Annotated[str, typer.Argument(help="The comix.to series URL (e.g., https://comix.to/title/y5nn-smoking-behind-the-supermarket-with-you).")],
    group: Annotated[Optional[str], typer.Option("--group", "-g", help="Only this scanlation group, as its /groups/NNNN href. Omit to include every group.")] = None,
):
    """Fetches and displays information about a manga series from comix.to."""
    rprint(Panel(Text("--- comix.to Manga Scraper CLI ---", justify="center", style="bold green"), style="green"))
    rprint(f"\n[bold blue]Fetching manga info from:[/bold blue] [link={series_url}]{series_url}[/link]")

    with console.status("[bold yellow]Fetching manga information...[/bold yellow]", spinner="dots"):
        try:
            manga_title, chapters = get_manga_info(series_url, group_id=group)
        except Exception as e:
            rprint(f"[bold red]Error fetching manga info:[/bold red] {e}")
            rprint("[bold red]Please ensure the URL is correct and you have an internet connection.[/bold red]")
            raise typer.Exit(code=1)

    if not manga_title:
        rprint("[bold red]Could not retrieve the manga title. Check the URL and your connection.[/bold red]")
        raise typer.Exit(code=1)
    if not chapters:
        # get_manga_info returns the title even when the chapter walk came
        # back empty (L528), so this is a distinct state from the one above.
        # One message blaming both sent people to check a URL that was fine.
        rprint(f"[bold red]Read the title '{manga_title}' but found no chapters.[/bold red]")
        rprint("[bold red]The chapter list may have failed to load, or this series has none yet.[/bold red]")
        raise typer.Exit(code=1)

    rprint(Panel(f"[bold cyan]Manga Title:[/bold cyan] [bold white]{manga_title}[/bold white]", style="cyan"))
    rprint(f"[bold magenta]Found {len(chapters)} chapters.[/bold magenta]")

    if Prompt.ask(Text("Do you want to list all chapters?", style="bold yellow"), choices=["yes", "no"], default="no") == "yes":
        list_chapters_func(chapters)


@app.command(name="search", help="[UNDER DEVELOPMENT] Search for manga series by title.")
def search(
    query: Annotated[str, typer.Argument(help="The manga title to search for.")]
):
    """Searches for manga series on comix.to and displays the results."""
    rprint(Panel(Text("--- comix.to Manga Scraper CLI ---", justify="center", style="bold green"), style="green"))
    rprint("\n[bold yellow]⚠ SEARCH FEATURE UNDER DEVELOPMENT[/bold yellow]")
    rprint("[yellow]The search feature is currently being developed and may not work reliably.[/yellow]")
    rprint("\n[bold cyan]Please use direct manga URLs instead:[/bold cyan]")
    rprint("[cyan]Example: https://comix.to/title/y5nn-smoking-behind-the-supermarket-with-you[/cyan]")
    rprint("\n[bold blue]Use the 'info' or 'download' commands with a direct URL.[/bold blue]")
    return


@app.command(name="list", help="List all chapters for a given manga series URL.")
def list_chapters(
    series_url: Annotated[str, typer.Argument(help="The comix.to series URL.")],
    group: Annotated[Optional[str], typer.Option("--group", "-g", help="Only this scanlation group, as its /groups/NNNN href. Omit to include every group.")] = None,
):
    """Lists all chapters for a given manga series URL."""
    rprint(Panel(Text("--- comix.to Manga Scraper CLI ---", justify="center", style="bold green"), style="green"))
    rprint(f"\n[bold blue]Fetching manga info from:[/bold blue] [link={series_url}]{series_url}[/link]")

    with console.status("[bold yellow]Fetching manga information...[/bold yellow]", spinner="dots"):
        try:
            manga_title, chapters = get_manga_info(series_url, group_id=group)
        except Exception as e:
            rprint(f"[bold red]Error fetching manga info:[/bold red] {e}")
            rprint("[bold red]Please ensure the URL is correct and you have an internet connection.[/bold red]")
            raise typer.Exit(code=1)

    if not chapters:
        # The title was being discarded into `_` right above, so the one
        # clue that the URL was fine could not be reported. Split the two
        # failures the same way `info` does.
        if manga_title:
            rprint(f"[bold red]Read the title '{manga_title}' but found no chapters.[/bold red]")
        else:
            rprint("[bold red]Could not retrieve the manga title. Check the URL and your connection.[/bold red]")
        raise typer.Exit(code=1)

    list_chapters_func(chapters)


def list_chapters_func(chapters):
    rprint(Panel(Text("--- Chapters ---", justify="center", style="bold blue"), style="blue"))
    for i, chapter in enumerate(chapters):
        rprint(f"[bold white]{i+1}.[/bold white] [green]{chapter_display(chapter)}[/green] ([link={chapter['url']}]{chapter['url']}[/link])")


@app.command(name="download", help="Download chapters from a manga series.")
def download(
    series_url: Annotated[str, typer.Argument(help="The comix.to series URL.")],
    all_chapters: Annotated[bool, typer.Option("--all", "-a", help="Download all chapters.")] = False,
    chapter_range: Annotated[Optional[str], typer.Option("--range", "-r", help="Download a specific range of chapters (e.g., '1-10').")] = None,
    output_dir: Annotated[str, typer.Option("--output", "-o", help="Directory to save downloaded chapters.")] = ".",
    max_workers: Annotated[int, typer.Option("--max-workers", "-w", help="Maximum number of concurrent chapter downloads.")] = 3,
    image_workers: Annotated[int, typer.Option("--image-workers", "-iw", help="Maximum number of concurrent image downloads per chapter.")] = 15,
    convert_to_pdf: Annotated[bool, typer.Option("--pdf", help="Convert downloaded chapters to PDF.")] = False,
    convert_to_cbz: Annotated[bool, typer.Option("--cbz", help="Convert downloaded chapters to CBZ (comic book archive).")] = False,
    keep_images: Annotated[bool, typer.Option("--keep-images", help="Keep original image files after conversion. Only applicable with --pdf or --cbz.")] = False,
    group: Annotated[Optional[str], typer.Option("--group", "-g", help="Only this scanlation group, as its /groups/NNNN href. Omit to include every group.")] = None,
    output_format: Annotated[str, typer.Option("--format", help="Image format: original keeps the bytes the server sent, png and jpeg re-encode. Original is what comix actually serves - WebP.")] = "original",
    jpeg_quality: Annotated[int, typer.Option("--quality", help="JPEG quality, 50-100. Only used with --format jpeg.")] = 92,
    resume: Annotated[bool, typer.Option("--resume", help="Skip chapters whose pages are already fully on disk. Checks for gaps and compares against the reader's page count, so a half-finished chapter is still fetched.")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose output.")] = False
):
    """Downloads chapters from a manga series."""
    # Validate before any fetching or writing, so a typo costs nothing.
    _formats = ("original", "png", "jpeg")
    if output_format.lower() not in _formats:
        rprint(f"[bold red]Unknown --format '{output_format}'. "
               f"Choose one of: {', '.join(_formats)}.[/bold red]")
        raise typer.Exit(code=2)
    if not 50 <= jpeg_quality <= 100:
        rprint("[bold red]--quality must be between 50 and 100.[/bold red]")
        raise typer.Exit(code=2)

    rprint(Panel(Text("--- comix.to Manga Scraper CLI ---", justify="center", style="bold green"), style="green"))
    rprint(f"\n[bold blue]Fetching manga info from:[/bold blue] [link={series_url}]{series_url}[/link]")

    with console.status("[bold yellow]Fetching manga information...[/bold yellow]", spinner="dots"):
        try:
            manga_title, chapters = get_manga_info(series_url, group_id=group)
        except Exception as e:
            rprint(f"[bold red]Error fetching manga info:[/bold red] {e}")
            rprint("[bold red]Please ensure the URL is correct and you have an internet connection.[/bold red]")
            raise typer.Exit(code=1)

    if not manga_title:
        rprint("[bold red]Could not retrieve the manga title. Check the URL and your connection.[/bold red]")
        raise typer.Exit(code=1)
    if not chapters:
        # get_manga_info returns the title even when the chapter walk came
        # back empty (L528), so this is a distinct state from the one above.
        # One message blaming both sent people to check a URL that was fine.
        rprint(f"[bold red]Read the title '{manga_title}' but found no chapters.[/bold red]")
        rprint("[bold red]The chapter list may have failed to load, or this series has none yet.[/bold red]")
        raise typer.Exit(code=1)

    rprint(Panel(f"[bold cyan]Manga Title:[/bold cyan] [bold white]{manga_title}[/bold white]", style="cyan"))
    rprint(f"[bold magenta]Found {len(chapters)} chapters.[/bold magenta]")

    groups_present = group_options(chapters)
    if len(groups_present) > 1:
        rprint("[bold yellow]This series has chapters from several scanlation "
               "groups:[/bold yellow]")
        for label, gid in groups_present:
            rprint(f"  {label}  [dim]{gid}[/dim]")
        rprint("[dim]Use --group to pick one. Chapters sharing a number are "
               "saved under their own group folder.[/dim]")

    chapters_to_download = []

    if all_chapters:
        chapters_to_download = chapters
        rprint("\n[bold blue]--- Downloading all chapters ---[/bold blue]")
    elif chapter_range:
        try:
            start_chap_str, end_chap_str = chapter_range.split('-')
            start_chap = int(start_chap_str)
            end_chap = int(end_chap_str)

            if not (1 <= start_chap <= len(chapters) and 1 <= end_chap <= len(chapters) and start_chap <= end_chap):
                rprint("[bold red]Invalid chapter range. Please enter valid numbers within the available range.[/bold red]")
                raise typer.Exit(code=1)

            chapters_to_download = chapters[start_chap - 1:end_chap]
            rprint(f"\n[bold blue]--- Downloading chapters {start_chap} to {end_chap} ---[/bold blue]")
        except ValueError:
            rprint("[bold red]Invalid range format. Use 'start-end' (e.g., '1-10').[/bold red]")
            raise typer.Exit(code=1)
    else:
        rprint("[bold yellow]No download option selected. Use --all or --range.[/bold yellow]")
        raise typer.Exit(code=0)

    if not chapters_to_download:
        rprint("[bold yellow]No chapters selected for download.[/bold yellow]")
        return

    # Advisory only. The reader's page count is what makes an exact figure
    # possible, and getting it for 300 chapters costs 300 browser passes - the
    # very thing this is meant to avoid. So: extrapolate up front, report the
    # measured total at the end.
    estimated = _ESTIMATED_MB_PER_CHAPTER * 1024 * 1024 * len(chapters_to_download)
    rprint(f"[bold cyan]Estimate:[/bold cyan] ~{_human_bytes(estimated)}  "
           f"[dim](~{_ESTIMATED_MB_PER_CHAPTER:.0f} MB/chapter × "
           f"{len(chapters_to_download)} chapters)[/dim]")
    rprint("[dim]An average measured on one series, not on this one.[/dim]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console
    ) as progress:
        task = progress.add_task("[bold green]Downloading chapters...", total=len(chapters_to_download))
        
        print_lock = threading.Lock()
        stop_event = threading.Event()
        bytes_written = 0
        # A run that loses chapters used to print "All selected chapters
        # downloaded (or attempted)" and exit 0, even with two of three coming
        # back empty. Observed live 2026-10-13. These three counters are what
        # the summary and the exit code are built from.
        ok_count = 0
        failed_count = 0
        skipped_count = 0

        def download_single_chapter_cli(chapter, index, stop_event):
            nonlocal bytes_written, ok_count, failed_count, skipped_count
            if stop_event.is_set():
                if verbose:
                    with print_lock:
                        rprint(f"[bold yellow]Skipping {chapter_display(chapter)} (download stopped).[/bold yellow]")
                return

            if verbose:
                with print_lock:
                    progress.update(task, description=f"[bold green]Downloading {chapter_display(chapter)}...[/bold green] ([{index+1}/{len(chapters_to_download)}])")
            try:
                result = download_chapter(chapter['url'], manga_title, chapter['title'], output_dir, stop_event, convert_to_pdf, convert_to_cbz, keep_images, image_workers, group=chapter.get('group'), output_format=output_format, jpeg_quality=jpeg_quality, resume=resume)
                got = result.get('downloaded', 0) if isinstance(result, dict) else '?'
                want = result.get('total_images', '?') if isinstance(result, dict) else '?'
                with print_lock:
                    if isinstance(result, dict) and result.get('bytes'):
                        bytes_written += result['bytes']
                    if isinstance(result, dict) and result.get('stopped'):
                        # download_chapter says so itself. It used to be
                        # inferred from stop_event here, which was wrong twice:
                        # it ignored stops entirely, and then it swallowed real
                        # failures that happened before a stop landed - the
                        # flag travels with the result instead of being raced.
                        pass
                    elif isinstance(result, dict) and result.get('skipped'):
                        # A resume skip is the feature working, not a failure.
                        skipped_count += 1
                    elif isinstance(result, dict) and result.get('success'):
                        ok_count += 1
                    else:
                        failed_count += 1
                        rprint(f"[bold red]Incomplete:[/bold red] "
                               f"{chapter_display(chapter)} - {got}/{want} images")
                if not stop_event.is_set() and verbose:
                    with print_lock:
                        progress.advance(task)
            except Exception as e:
                if not stop_event.is_set():
                    with print_lock:
                        failed_count += 1
                        rprint(f"[bold red]Error downloading {chapter_display(chapter)}:[/bold red] {e}")

        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for i, chapter in enumerate(chapters_to_download):
                    if stop_event.is_set():
                        rprint("[bold yellow]Download stopped by user.[/bold yellow]")
                        break
                    futures.append(executor.submit(download_single_chapter_cli, chapter, i, stop_event))
                
                for future in futures:
                    try:
                        future.result()
                    except Exception:
                        pass
                    if stop_event.is_set():
                        for f in futures:
                            f.cancel()
                        break
        except KeyboardInterrupt:
                rprint("\n[bold yellow]KeyboardInterrupt detected. Stopping downloads...[/bold yellow]")
                stop_event.set()
                progress.stop()
                time.sleep(1)
        finally:
                # Measured, not estimated: the sum of what the files actually
                # came to. Zero is still worth printing - it means the run wrote
                # nothing, e.g. every chapter was skipped by --resume.
                rprint(f"\n[bold cyan]Downloaded:[/bold cyan] {_human_bytes(bytes_written)}")
                if stop_event.is_set():
                    rprint("\n[bold yellow]Downloads stopped by user.[/bold yellow]")
                elif failed_count:
                    rprint(f"\n[bold red]{failed_count} of "
                           f"{ok_count + failed_count + skipped_count} chapters "
                           f"failed.[/bold red] "
                           f"[dim]Done: {ok_count}, skipped: {skipped_count}.[/dim]")
                elif skipped_count and not ok_count:
                    # Every chapter was skipped. With ok_count > 0 this branch
                    # must not fire - a run that downloaded one chapter and
                    # skipped another is an ordinary success.
                    rprint(f"\n[bold cyan]Nothing to do - all "
                           f"{skipped_count} chapters were already on disk.[/bold cyan]")
                else:
                    rprint("\n[bold green]All selected chapters downloaded.[/bold green]")

    # Outside the finally on purpose: raising inside one would replace whatever
    # exception was in flight. Ctrl-C is handled above, so by here a non-zero
    # exit can only mean chapters were lost.
    if failed_count:
        raise typer.Exit(code=1)


@app.command(name="gui", help="Launch the GUI application.")
def launch_gui():
    """Launches the GUI application."""
    rprint(Panel(Text("--- comix.to Manga Scraper GUI ---", justify="center", style="bold purple"), style="purple"))
    rprint("[bold yellow]Launching GUI...[/bold yellow]")
    try:
        try:
            from .gui import main_gui
        except ImportError:
            from gui import main_gui
        main_gui()
    except ImportError:
        rprint("[bold red]GUI module not found. Please ensure 'gui.py' exists.[/bold red]")
        raise typer.Exit(code=1)
    except Exception as e:
        rprint(f"[bold red]Error launching GUI:[/bold red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
