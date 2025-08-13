import mysql.connector

def get_db_connection():
    """데이터베이스 연결 함수"""
    return mysql.connector.connect(
        host="52.79.248.3",
        user="jjanghoe",
        password="8689",
        database="zzirit_db",
        charset='utf8mb4',
        port=3306
    )
    
# db_handler.py에 꼭 있어야 할 함수!
def query_db(sql):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

# ✅ 부품 정보 조회
def fetch_product_info(part_number: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM pcb_parts WHERE part_number = %s"
    cursor.execute(query, (part_number,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

# ✅ 주문 필요 부품 리스트
def fetch_needed_parts():
    conn = get_db_connection()  # get_connection() → get_db_connection()으로 변경
    cursor = conn.cursor(dictionary=True)
    query = "SELECT part_number FROM pcb_parts WHERE quantity <= min_stock"
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row["part_number"] for row in result]

# ✅ 흡습이 필요한 자재
def fetch_humidity_required_materials():
    conn = get_db_connection()  # 수정
    cursor = conn.cursor(dictionary=True)
    query = "SELECT part_number FROM pcb_parts WHERE needs_humidity_control = 1"
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row["part_number"] for row in result]

# ✅ 흡습이 필요 없는 자재
def fetch_non_humidity_required_materials():
    conn = get_db_connection()  # 수정
    cursor = conn.cursor(dictionary=True)
    query = "SELECT part_number FROM pcb_parts WHERE needs_humidity_control = 0"
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row["part_number"] for row in result]

# ✅ 흡습 여부 O 자재
def fetch_humidity_sensitive_parts():
    conn = get_db_connection()  # 수정
    cursor = conn.cursor(dictionary=True)
    query = "SELECT part_number FROM pcb_parts WHERE is_humidity_sensitive = 1"
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row["part_number"] for row in result]

# ✅ 전체 자재 중 재고 가장 적은 부품
def fetch_part_with_lowest_stock():
    conn = get_db_connection()  # 수정
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT part_number, quantity
        FROM pcb_parts
        ORDER BY quantity ASC
        LIMIT 1
    """
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

# ✅ 전체 자재 중 재고 가장 많은 부품
def fetch_part_with_highest_stock():
    conn = get_db_connection()  # 수정
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT part_number, quantity
        FROM pcb_parts
        ORDER BY quantity DESC
        LIMIT 1
    """
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

# ✅ 흡습 필요 자재 중 재고 가장 많은 부품
def fetch_most_stock_humidity_part():
    conn = get_db_connection()  # 수정
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT part_number, quantity
        FROM pcb_parts
        WHERE needs_humidity_control = 1
        ORDER BY quantity DESC
        LIMIT 1
    """
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

# ✅ 흡습 불필요 자재 중 재고 가장 적은 부품
def fetch_least_stock_non_humidity_part():
    conn = get_db_connection()  # 수정
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT part_number, quantity
        FROM pcb_parts
        WHERE needs_humidity_control = 0
        ORDER BY quantity ASC
        LIMIT 1
    """
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

if __name__ == "__main__":
    conn = get_db_connection()  # 수정
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES;")
    print("✅ 현재 테이블 목록:")
    for row in cursor.fetchall():
        print(row)
    conn.close()