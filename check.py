import os
import sys


def get_file_size(size):
    """将文件大小转换为易读格式 (B, KB, MB, GB)"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} GB"


def main():
    # 获取目标文件夹路径
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        folder_path = input("请输入文件夹路径: ")

    # 检查路径有效性
    if not os.path.isdir(folder_path):
        print("错误：提供的路径不是有效的文件夹。")
        return

    # 获取所有ogg文件及其大小
    ogg_files = []
    try:
        for file_name in os.listdir(folder_path):
            if file_name.lower().endswith('.ogg'):
                file_path = os.path.join(folder_path, file_name)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    ogg_files.append((file_name, file_size))
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return

    # 检查是否找到文件
    if not ogg_files:
        print("未找到任何.ogg文件。")
        return

    # 按文件大小降序排序
    ogg_files.sort(key=lambda x: x[1], reverse=True)

    # 计算最大文件名长度用于输出对齐
    max_name_length = max(len(name) for name, _ in ogg_files) + 2

    # 打印排序结果
    print("\nOGG 文件排序结果 (从大到小):")
    print("-" * (max_name_length + 12))
    print(f"{'文件名':<{max_name_length}} {'大小':>10}")
    print("-" * (max_name_length + 12))

    for file_name, file_size in ogg_files:
        size_str = get_file_size(file_size)
        print(f"{file_name:<{max_name_length}} {size_str:>10}")
    print("-" * (max_name_length + 12))


if __name__ == "__main__":
    main()