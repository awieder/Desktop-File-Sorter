from watchdog.observers import Observer #monitors a specefied directory or file for changes, can work continuosly without
                                        #blocking main program execution
from watchdog.events import FileSystemEventHandler #handles file creation, deletion, modification etc
import time
import os #can create directories
import json
import shutil #can move files
import datetime
SOURCE_DIR
TARGET_DIR

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
    observer.schedule(event_handler, DOWNLOAD_DIR, recursive=False)
    observer.start()
    print("Starting watching for downloads")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
