"""
数据库工具模块

提供数据库查询和操作功能，支持SQLite、MySQL、PostgreSQL等数据库
"""

import sqlite3
import json
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
import os


def execute_sql_query(
    db_path: str,
    query: str,
    params: Optional[tuple] = None
) -> Dict[str, Any]:
    """
    执行SQL查询

    Args:
        db_path: 数据库文件路径（SQLite）或连接字符串
        query: SQL查询语句
        params: 查询参数

    Returns:
        查询结果字典
    """
    try:
        # 检查是否是SQLite数据库
        if db_path.endswith('.db') or db_path.endswith('.sqlite') or db_path.endswith('.sqlite3'):
            return _execute_sqlite_query(db_path, query, params)
        else:
            # 这里可以扩展支持其他数据库
            return {
                "success": False,
                "error": f"不支持的数据库类型: {db_path}",
                "suggestion": "目前只支持SQLite数据库（.db, .sqlite, .sqlite3扩展名）"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"执行SQL查询失败: {str(e)}",
            "query": query,
            "params": params
        }


def _execute_sqlite_query(db_path: str, query: str, params: Optional[tuple] = None) -> Dict[str, Any]:
    """执行SQLite查询"""
    try:
        # 检查数据库文件是否存在
        if not os.path.exists(db_path):
            return {
                "success": False,
                "error": f"数据库文件不存在: {db_path}",
                "suggestion": "请检查文件路径是否正确"
            }

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 执行查询
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # 获取结果
        if query.strip().upper().startswith('SELECT'):
            # 查询操作
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            # 转换为字典列表
            result = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    # 处理特殊类型
                    if isinstance(row[i], bytes):
                        row_dict[col] = str(row[i])
                    else:
                        row_dict[col] = row[i]
                result.append(row_dict)
            
            return {
                "success": True,
                "type": "query",
                "row_count": len(result),
                "columns": columns,
                "data": result,
                "query": query
            }
        else:
            # DML操作（INSERT, UPDATE, DELETE等）
            conn.commit()
            affected_rows = cursor.rowcount
            
            return {
                "success": True,
                "type": "dml",
                "affected_rows": affected_rows,
                "query": query
            }
    
    except sqlite3.Error as e:
        return {
            "success": False,
            "error": f"SQLite错误: {str(e)}",
            "query": query
        }
    finally:
        if 'conn' in locals():
            conn.close()


def list_tables(db_path: str) -> Dict[str, Any]:
    """
    列出数据库中的所有表

    Args:
        db_path: 数据库文件路径

    Returns:
        表信息字典
    """
    query = """
    SELECT name, type, sql 
    FROM sqlite_master 
    WHERE type IN ('table', 'view') 
    AND name NOT LIKE 'sqlite_%'
    ORDER BY type, name
    """
    
    result = execute_sql_query(db_path, query)
    
    if result.get("success"):
        tables = []
        for row in result.get("data", []):
            tables.append({
                "name": row["name"],
                "type": row["type"],
                "sql": row["sql"]
            })
        
        return {
            "success": True,
            "database": db_path,
            "table_count": len(tables),
            "tables": tables
        }
    else:
        return result


def describe_table(db_path: str, table_name: str) -> Dict[str, Any]:
    """
    描述表结构

    Args:
        db_path: 数据库文件路径
        table_name: 表名

    Returns:
        表结构信息
    """
    # 获取表信息
    table_info_query = f"PRAGMA table_info({table_name})"
    result = execute_sql_query(db_path, table_info_query)
    
    if not result.get("success"):
        return result
    
    columns = []
    for row in result.get("data", []):
        columns.append({
            "name": row["name"],
            "type": row["type"],
            "notnull": bool(row["notnull"]),
            "default_value": row["dflt_value"],
            "primary_key": bool(row["pk"])
        })
    
    # 获取索引信息
    index_query = f"PRAGMA index_list({table_name})"
    index_result = execute_sql_query(db_path, index_query)
    
    indexes = []
    if index_result.get("success"):
        for idx_row in index_result.get("data", []):
            idx_name = idx_row["name"]
            idx_unique = bool(idx_row["unique"])
            
            # 获取索引列
            idx_cols_query = f"PRAGMA index_info({idx_name})"
            idx_cols_result = execute_sql_query(db_path, idx_cols_query)
            
            idx_columns = []
            if idx_cols_result.get("success"):
                for col_row in idx_cols_result.get("data", []):
                    idx_columns.append(col_row["name"])
            
            indexes.append({
                "name": idx_name,
                "unique": idx_unique,
                "columns": idx_columns
            })
    
    return {
        "success": True,
        "table": table_name,
        "column_count": len(columns),
        "columns": columns,
        "index_count": len(indexes),
        "indexes": indexes
    }


def query_to_dataframe(db_path: str, query: str) -> Dict[str, Any]:
    """
    执行查询并返回Pandas DataFrame

    Args:
        db_path: 数据库文件路径
        query: SQL查询语句

    Returns:
        包含DataFrame信息的结果
    """
    try:
        result = execute_sql_query(db_path, query)
        
        if not result.get("success"):
            return result
        
        if result.get("type") != "query":
            return {
                "success": False,
                "error": "查询必须是SELECT语句",
                "query": query
            }
        
        # 转换为DataFrame
        df = pd.DataFrame(result["data"])
        
        # 生成统计信息
        stats = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "memory_usage": f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB"
        }
        
        # 数值列的统计
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            numeric_stats = df[numeric_cols].describe().to_dict()
            stats["numeric_statistics"] = numeric_stats
        
        return {
            "success": True,
            "dataframe_info": stats,
            "sample_data": df.head(10).to_dict(orient='records'),
            "query": query
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"转换为DataFrame失败: {str(e)}",
            "query": query
        }


def create_sample_database() -> str:
    """
    创建示例数据库（用于测试和演示）

    Returns:
        创建的数据库文件路径
    """
    import tempfile
    
    # 创建临时数据库文件
    temp_dir = tempfile.gettempdir()
    db_path = os.path.join(temp_dir, f"sample_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建示例表
        cursor.execute("""
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            salary REAL,
            hire_date DATE,
            email TEXT UNIQUE
        )
        """)
        
        cursor.execute("""
        CREATE TABLE departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            manager TEXT,
            budget REAL
        )
        """)
        
        cursor.execute("""
        CREATE TABLE projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department_id INTEGER,
            start_date DATE,
            end_date DATE,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (department_id) REFERENCES departments(id)
        )
        """)
        
        # 插入示例数据
        departments = [
            ('技术部', '张三', 1000000),
            ('市场部', '李四', 500000),
            ('财务部', '王五', 300000),
            ('人力资源部', '赵六', 200000)
        ]
        
        cursor.executemany("INSERT INTO departments (name, manager, budget) VALUES (?, ?, ?)", departments)
        
        employees = [
            ('张三', '技术部', 15000, '2020-01-15', 'zhangsan@example.com'),
            ('李四', '市场部', 12000, '2020-03-20', 'lisi@example.com'),
            ('王五', '财务部', 10000, '2020-05-10', 'wangwu@example.com'),
            ('赵六', '人力资源部', 8000, '2020-07-05', 'zhaoliu@example.com'),
            ('钱七', '技术部', 18000, '2021-02-28', 'qianqi@example.com'),
            ('孙八', '市场部', 11000, '2021-04-15', 'sunba@example.com')
        ]
        
        cursor.executemany("""
        INSERT INTO employees (name, department, salary, hire_date, email) 
        VALUES (?, ?, ?, ?, ?)
        """, employees)
        
        projects = [
            ('企业网站重构', 1, '2023-01-01', '2023-06-30', 'active'),
            ('市场推广活动', 2, '2023-02-01', '2023-12-31', 'active'),
            ('财务系统升级', 3, '2023-03-01', '2023-09-30', 'in_progress'),
            ('员工培训计划', 4, '2023-04-01', '2023-08-31', 'completed')
        ]
        
        cursor.executemany("""
        INSERT INTO projects (name, department_id, start_date, end_date, status) 
        VALUES (?, ?, ?, ?, ?)
        """, projects)
        
        # 创建索引
        cursor.execute("CREATE INDEX idx_employees_department ON employees(department)")
        cursor.execute("CREATE INDEX idx_employees_salary ON employees(salary)")
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "database_path": db_path,
            "message": "示例数据库创建成功",
            "tables": ["employees", "departments", "projects"],
            "sample_queries": [
                "SELECT * FROM employees LIMIT 5",
                "SELECT department, AVG(salary) as avg_salary FROM employees GROUP BY department",
                "SELECT d.name as department, COUNT(e.id) as employee_count FROM departments d LEFT JOIN employees e ON d.name = e.department GROUP BY d.name"
            ]
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"创建示例数据库失败: {str(e)}"
        }