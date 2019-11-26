from pathlib import Path

from requests_html import HTMLSession

FILE_TREE_URL = "https://searchcode.com/api/directory_tree/131038/"
SAMPLE_FILE_URL = "https://searchcode.com/codesearch/view/28766922/"
DOMAIN_URL = "https://searchcode.com"

RAW_LINK_XPATH = "/html/body/div/div[2]/table/tbody/tr[4]/td[3]/a"

ses = HTMLSession()

# r = ses.get(SAMPLE_FILE_URL)
r_list = ses.get(FILE_TREE_URL)
print(f"r_list status code: {r_list.status_code}")

if r_list.ok:
    print(f"Fetched the file list! Response code: {r_list.status_code}.\n")

file_urls = [DOMAIN_URL + url.strip('\\"') for url in r_list.html.links]
# file_paths = [url[16:] for url in r_list.html.links]

for file_url in file_urls:
    r = ses.get(file_url)
    if not r.ok:
        print(
            f"Failed to fetch the page for the file {file_url}. "
            f"Response status code: {r.status_code}."
        )
        continue
    else:
        print(f"{file_url} fetched...")

    raw_link_element = r.html.xpath(RAW_LINK_XPATH, first=True)
    print(f"Raw link element: {raw_link_element}")
    raw_url = raw_link_element.attrs.get("href")

    if raw_url is None:
        print(f"dupa zbita, nie znalazło linka w attrs: {raw_link_element.attrs}")
        continue

    if raw_url is not None:
        full_raw_url = DOMAIN_URL + raw_url
        code_page = ses.get(full_raw_url)

        if not code_page.ok:
            print(
                f"Failed to fetch the file at {full_raw_url}. "
                f"Response code: {r.status_code}"
            )

        if code_page.ok:
            code = code_page.html.html
            # TODO: take care of the endline chars? \r\n everywhere...

            file_path = Path(file_url[37:])
            dir_path = file_path.parent

            dir_path.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w") as f:
                f.write(code)
