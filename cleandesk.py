from watchdog.observers import (
    Observer,
)  # monitors a specefied directory or file for changes, can work continuosly without

# blocking main program execution
from watchdog.events import (
    FileSystemEventHandler,
)  # handles file creation, deletion, modification etc
import time
import os  # can create directories
import shutil  # can move files
import datetime
import subprocess
import sys

SOURCE_DIR = os.path.expanduser(
    os.getenv("SOURCE_DIR", "~/Downloads")
)  # get the source directory from the environment variable
TARGET_DIR = os.path.expanduser(
    os.getenv("TARGET_DIR", "~/Downloads/Sorted")
)  # get the target directory from the environment variable
os.makedirs(TARGET_DIR, exist_ok=True)


def get_download_month(path: str) -> str:
    # 1) macOS: use Spotlight's kMDItemDownloadedDate if present
    if sys.platform == "darwin":
        try:
            result = subprocess.run(
                ["mdls", "-raw", "-name", "kMDItemDownloadedDate", path],
                capture_output=True,
                text=True,
            )
            raw = result.stdout.strip()
            if result.returncode == 0 and raw and raw != "(null)":
                dt = datetime.datetime.strptime(raw, "%Y-%m-%d %H:%M:%S %z")
                return dt.strftime("%B %Y")
        except Exception:
            pass

    # 2) Fallback: birth/creation time (or ctime)
    try:
        stat = os.stat(path)
        if hasattr(stat, "st_birthtime"):  # macOS provides true birth time
            ts = stat.st_birthtime
        else:
            ts = os.path.getctime(path)
        return datetime.datetime.fromtimestamp(ts).strftime("%B %Y")
    except Exception:
        return ""


def wait_for_download(filepath):
    last_size = -1
    correct_count = 0
    while correct_count < 3:
        try:
            size = os.path.getsize(filepath)
        except FileNotFoundError:
            return False
        if size == last_size:
            correct_count += 1
        else:
            correct_count = 0
        last_size = size
        time.sleep(1)
    return True


def get_Month(filepath):
    if not os.path.exists(filepath):
        print("File not found to get month")
        return ""
    try:
        creation_time = os.path.getctime(filepath)
        creation_datetime_obj = datetime.date.fromtimestamp(creation_time)
        month_string = creation_datetime_obj.strftime("%B %Y")
        return month_string

    except Exception as e:
        print(f"Error when getting creation time: {e}")


class Handler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            filename = os.path.basename(event.src_path)
            if filename.endswith(".crdownload") or filename.endswith(".part"):
                return
            dest = os.path.join(TARGET_DIR, filename)
            if wait_for_download(event.src_path):
                print("Trying to move file")
                try:
                    shutil.move(event.src_path, dest)
                    print("Moved file successfully")
                    month_string = get_Month(dest)
                    folder_path = os.path.join(TARGET_DIR, month_string)
                    if not os.path.isdir(folder_path):
                        os.mkdir(folder_path)
                    shutil.move(dest, folder_path)
                    print("Moved file to correct sorted folder")

                except Exception as e:
                    print(f"Could not move file: {e}")


def main():
    print("Hi")
    event_handler = Handler()
    observer = Observer()
    observer.schedule(event_handler, SOURCE_DIR, recursive=False)
    observer.start()
    print("Starting sorting for old downloads")

    for file in os.listdir(SOURCE_DIR):
        try:
            source_path = os.path.join(SOURCE_DIR, file)
            month_string = (
                get_download_month(source_path) or get_Month(source_path) or "Unknown"
            )
            folder_path = os.path.join(TARGET_DIR, month_string)
            os.makedirs(folder_path, exist_ok=True)
            shutil.move(source_path, folder_path)
            print(f"Moved {file} to {folder_path}")
        except Exception as e:
            print(f"Could not move file: {e}")

    print("Starting watcher for new downloads")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
