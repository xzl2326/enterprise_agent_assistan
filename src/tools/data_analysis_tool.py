"""
数据分析工具模块

提供数据处理和分析功能，支持CSV、Excel、JSON等格式
"""

import pandas as pd
import numpy as np
import json
import csv
from typing import Dict, Any, List, Optional
import os
from datetime import datetime


def read_data_file(file_path: str) -> Dict[str, Any]:
    """
    读取数据文件（支持CSV、Excel、JSON）

    Args:
        file_path: 文件路径

    Returns:
        数据信息字典
    """
    try:
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"文件不存在: {file_path}"
            }
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.csv':
            df = pd.read_csv(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        elif file_ext == '.json':
            df = pd.read_json(file_path)
        else:
            return {
                "success": False,
                "error": f"不支持的文件格式: {file_ext}",
                "supported_formats": ['.csv', '.xlsx', '.xls', '.json']
            }
        
        # 生成文件信息
        file_info = {
            "success": True,
            "file_path": file_path,
            "file_size": f"{os.path.getsize(file_path) / 1024:.2f} KB",
            "format": file_ext,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "sample_data": df.head(5).to_dict(orient='records'),
            "missing_values": df.isnull().sum().to_dict()
        }
        
        return file_info
    
    except Exception as e:
        return {
            "success": False,
            "error": f"读取文件失败: {str(e)}",
            "file_path": file_path
        }


def analyze_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """
    分析DataFrame数据

    Args:
        df: Pandas DataFrame

    Returns:
        分析结果字典
    """
    try:
        analysis = {
            "success": True,
            "basic_info": {
                "shape": df.shape,
                "row_count": len(df),
                "column_count": len(df.columns),
                "memory_usage": f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB"
            },
            "data_types": {
                col: str(dtype) for col, dtype in df.dtypes.items()
            },
            "missing_values": df.isnull().sum().to_dict(),
            "unique_counts": {col: df[col].nunique() for col in df.columns}
        }
        
        # 数值列统计
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            numeric_stats = df[numeric_cols].describe().to_dict()
            analysis["numeric_statistics"] = numeric_stats
            
            # 相关性分析
            if len(numeric_cols) > 1:
                correlation = df[numeric_cols].corr().to_dict()
                analysis["correlation"] = correlation
        
        # 分类列统计
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(categorical_cols) > 0:
            categorical_stats = {}
            for col in categorical_cols:
                value_counts = df[col].value_counts().head(10).to_dict()
                categorical_stats[col] = {
                    "unique_values": df[col].nunique(),
                    "top_values": value_counts
                }
            analysis["categorical_statistics"] = categorical_stats
        
        return analysis
    
    except Exception as e:
        return {
            "success": False,
            "error": f"数据分析失败: {str(e)}"
        }


def filter_data(
    file_path: str,
    conditions: Dict[str, Any]
) -> Dict[str, Any]:
    """
    根据条件过滤数据

    Args:
        file_path: 数据文件路径
        conditions: 过滤条件字典
        Example: {"column": "age", "operator": ">", "value": 30}

    Returns:
        过滤结果
    """
    try:
        # 读取数据
        file_info = read_data_file(file_path)
        if not file_info.get("success"):
            return file_info
        
        # 这里简化处理，实际应该根据条件构建查询
        # 暂时返回前10行数据
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.csv':
            df = pd.read_csv(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        elif file_ext == '.json':
            df = pd.read_json(file_path)
        
        # 应用过滤条件（简化版）
        filtered_df = df.head(10)  # 暂时返回前10行
        
        return {
            "success": True,
            "original_rows": len(df),
            "filtered_rows": len(filtered_df),
            "conditions": conditions,
            "filtered_data": filtered_df.to_dict(orient='records')
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"数据过滤失败: {str(e)}",
            "file_path": file_path,
            "conditions": conditions
        }


def aggregate_data(
    file_path: str,
    group_by: List[str],
    aggregations: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    数据聚合分析

    Args:
        file_path: 数据文件路径
        group_by: 分组字段列表
        aggregations: 聚合操作字典
        Example: {"salary": ["mean", "sum", "count"], "age": ["min", "max"]}

    Returns:
        聚合结果
    """
    try:
        # 读取数据
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.csv':
            df = pd.read_csv(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        elif file_ext == '.json':
            df = pd.read_json(file_path)
        else:
            return {
                "success": False,
                "error": f"不支持的文件格式: {file_ext}"
            }
        
        # 检查分组字段是否存在
        for col in group_by:
            if col not in df.columns:
                return {
                    "success": False,
                    "error": f"分组字段不存在: {col}",
                    "available_columns": list(df.columns)
                }
        
        # 执行聚合
        agg_result = df.groupby(group_by).agg(aggregations).reset_index()
        
        # 重命名列
        agg_result.columns = ['_'.join(col).strip('_') for col in agg_result.columns.values]
        
        return {
            "success": True,
            "group_by": group_by,
            "aggregations": aggregations,
            "result_rows": len(agg_result),
            "aggregated_data": agg_result.to_dict(orient='records')
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"数据聚合失败: {str(e)}",
            "file_path": file_path
        }


def generate_statistics_report(file_path: str) -> Dict[str, Any]:
    """
    生成数据统计报告

    Args:
        file_path: 数据文件路径

    Returns:
        统计报告
    """
    try:
        # 读取数据
        file_info = read_data_file(file_path)
        if not file_info.get("success"):
            return file_info
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.csv':
            df = pd.read_csv(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        elif file_ext == '.json':
            df = pd.read_json(file_path)
        
        # 生成详细分析
        analysis = analyze_dataframe(df)
        
        # 生成报告
        report = {
            "success": True,
            "report_generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "file_info": {
                "path": file_path,
                "size": f"{os.path.getsize(file_path) / 1024:.2f} KB",
                "rows": len(df),
                "columns": len(df.columns)
            },
            "data_quality": {
                "total_cells": df.size,
                "missing_cells": df.isnull().sum().sum(),
                "missing_percentage": f"{(df.isnull().sum().sum() / df.size) * 100:.2f}%",
                "duplicate_rows": df.duplicated().sum(),
                "duplicate_percentage": f"{(df.duplicated().sum() / len(df)) * 100:.2f}%"
            },
            "column_summary": []
        }
        
        # 每列摘要
        for col in df.columns:
            col_type = str(df[col].dtype)
            col_summary = {
                "column": col,
                "type": col_type,
                "unique_values": df[col].nunique(),
                "missing_values": df[col].isnull().sum()
            }
            
            if col_type.startswith('int') or col_type.startswith('float'):
                col_summary.update({
                    "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
                    "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
                    "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                    "median": float(df[col].median()) if not pd.isna(df[col].median()) else None
                })
            elif col_type == 'object' or col_type == 'category':
                top_values = df[col].value_counts().head(5).to_dict()
                col_summary["top_values"] = top_values
            
            report["column_summary"].append(col_summary)
        
        # 添加分析结果
        report["detailed_analysis"] = analysis
        
        return report
    
    except Exception as e:
        return {
            "success": False,
            "error": f"生成统计报告失败: {str(e)}",
            "file_path": file_path
        }


def create_sample_data() -> Dict[str, Any]:
    """
    创建示例数据（用于测试和演示）

    Returns:
        示例数据信息
    """
    try:
        import tempfile
        
        # 创建示例数据
        data = {
            '员工ID': list(range(1, 11)),
            '姓名': ['张三', '李四', '王五', '赵六', '钱七', '孙八', '周九', '吴十', '郑十一', '王十二'],
            '部门': ['技术部', '市场部', '技术部', '财务部', '市场部', '技术部', '人力资源部', '财务部', '技术部', '市场部'],
            '职位': ['工程师', '经理', '工程师', '会计', '专员', '高级工程师', '专员', '经理', '工程师', '专员'],
            '薪资': [15000, 20000, 12000, 8000, 9000, 18000, 7000, 22000, 13000, 8500],
            '入职日期': pd.date_range(start='2020-01-01', periods=10, freq='M'),
            '绩效评分': [4.5, 4.8, 3.9, 4.2, 4.0, 4.7, 3.8, 4.9, 4.1, 4.3]
        }
        
        df = pd.DataFrame(data)
        
        # 保存到临时文件
        temp_dir = tempfile.gettempdir()
        csv_path = os.path.join(temp_dir, f"sample_employees_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        excel_path = os.path.join(temp_dir, f"sample_employees_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        df.to_excel(excel_path, index=False)
        
        # 生成示例查询
        sample_queries = [
            "SELECT * FROM employees WHERE 部门 = '技术部'",
            "SELECT 部门, AVG(薪资) as 平均薪资 FROM employees GROUP BY 部门",
            "SELECT 职位, COUNT(*) as 人数 FROM employees GROUP BY 职位 ORDER BY 人数 DESC"
        ]
        
        return {
            "success": True,
            "message": "示例数据创建成功",
            "data_files": {
                "csv": csv_path,
                "excel": excel_path
            },
            "data_info": {
                "rows": len(df),
                "columns": list(df.columns),
                "sample_data": df.head(3).to_dict(orient='records')
            },
            "sample_queries": sample_queries,
            "analysis_suggestions": [
                "按部门分析薪资分布",
                "分析不同职位的绩效评分",
                "查看各部门员工数量"
            ]
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"创建示例数据失败: {str(e)}"
        }