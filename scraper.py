import logging
import typing
from pathlib import Path

from requests_html import HTMLSession, HTML

from exceptions import FetchingError, ContinueException

SAMPLE_FILE_URL = "https://searchcode.com/codesearch/view/28766922/"


class Scraper:
    def __init__(self):
        self.ses = HTMLSession()
        self.lib_name = "Algobox"
        self.domain_url = "https://searchcode.com"
        self.file_tree_url = "https://searchcode.com/api/directory_tree/131038/"
        self.raw_link_xpath = "/html/body/div/div[2]/table/tbody/tr[4]/td[3]/a"
        self.success_counter = 0
        self.total_files_count = None

    def get_file_urls(self) -> typing.List:
        r_list = self.ses.get(self.file_tree_url)

        if not r_list.ok:
            raise FetchingError(
                f"Failed to fetch the file list! Response status: {r_list.status_code}."
            )

        file_urls = [self.domain_url + url.strip('\\"') for url in r_list.html.links]

        return file_urls

    def set_total_files_count(self, count: int) -> None:
        self.total_files_count = count
        logging.info(f"Number of files to download: {count}.")

    def fetch_file_page(self, file_url: str) -> HTML:
        resp = self.ses.get(file_url)
        if not resp.ok:
            raise ContinueException(
                f"Failed to fetch the page for the file {file_url}.", resp.status_code
            )
        else:
            logging.info(f"{file_url} fetched...")

        return resp.html

    def find_raw_file_link(self, file_page: HTML):
        raw_link_element = file_page.xpath(self.raw_link_xpath, first=True)
        raw_url = raw_link_element.attrs.get("href")

        if raw_url is None:
            raise ContinueException(
                f"Failed to find the raw file link in the attrs: "
                f"{raw_link_element.attrs}."
            )

        full_raw_url = self.domain_url + raw_url

        return full_raw_url

    def get_raw_code(self, full_raw_url: str):
        code_page = self.ses.get(full_raw_url)

        if not code_page.ok:
            raise ContinueException(
                f"Failed to fetch the file at {full_raw_url}.", code_page.status_code
            )

        # This is the only way that works to get the entire text:
        code = code_page.html.html
        # newline chars are \r\n; just in case it was important

        return code

    @staticmethod
    def save_file(file_path: Path, code: str) -> None:
        dir_path = file_path.parent
        dir_path.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            f.write(code)

    def fetch_source_code(self):
        file_urls = self.get_file_urls()
        self.set_total_files_count(len(file_urls))

        for file_url in file_urls:
            try:
                file_page = self.fetch_file_page(file_url)
                full_raw_url = self.find_raw_file_link(file_page)
                code = self.get_raw_code(full_raw_url)
            except ContinueException as e:
                logging.warning(e)
                continue

            file_path = Path(self.lib_name + file_url[36:])
            self.save_file(file_path, code)
            self.success_counter += 1

        logging.info(
            f"Successfully fetched and saved {self.success_counter} "
            f"out of {self.total_files_count} files."
        )


if __name__ == "__main__":
    logging.basicConfig(
        # filename="scraplog.log",
        # filemode="w",
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
    )
    scraper = Scraper()
    try:
        scraper.fetch_source_code()
    except FetchingError as e:
        logging.error(e)
        logging.info("No files were downloaded.")
    except Exception as e:
        logging.error("Unexpected exception! Execution stopped.")
        logging.error(e)
