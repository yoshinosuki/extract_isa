import sys
import os
import struct
import hashlib
from collections import defaultdict


def extract_wmv_files(input_file_path):
    """
    从二进制文件中提取WMV/ASF视频文件

    WMV/ASF文件特征：
    - ASF头部对象的固定GUID标识：75B22630-668E-11CF-A6D9-00AA0062CE6C
    - 对应的字节序列：b'\x30\x26\xB2\x75\x8E\x66\xCF\x11\xA6\xD9\x00\xAA\x00\x62\xCE\x6C'
    """

    # 创建输出目录
    base_name = os.path.splitext(os.path.basename(input_file_path))[0]
    output_dir = f"{base_name}_wmv"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        # 读取整个文件
        with open(input_file_path, 'rb') as f:
            data = f.read()

        # ASF头部对象GUID
        asf_header_guid = b'\x30\x26\xB2\x75\x8E\x66\xCF\x11\xA6\xD9\x00\xAA\x00\x62\xCE\x6C'

        # ASF文件属性对象GUID（用于获取文件大小）
        file_properties_guid = b'\xA1\xDC\xAB\x8C\xA9\xCF\x11\x8E\xE4\x00\xC0\x0C\x20\x53\x65'

        # 查找所有ASF头部位置
        header_positions = []
        start = 0
        file_size = len(data)
        print(f"分析文件: {os.path.basename(input_file_path)}")
        print(f"文件总长度: {file_size:,} 字节")
        print("开始扫描WMV/ASF文件...")

        while True:
            pos = data.find(asf_header_guid, start)
            if pos == -1:
                break
            header_positions.append(pos)
            start = pos + 1

        if not header_positions:
            print("未找到WMV/ASF文件头部")
            return

        print(f"发现 {len(header_positions)} 个潜在的WMV/ASF文件开头")

        # 提取WMV文件
        extracted_files = []
        for i, header_start in enumerate(header_positions):
            # 检查头部对象大小位置是否有效
            if header_start + 24 > file_size:
                print(f" 位置 {header_start} 超出文件范围，跳过")
                continue

            try:
                # 读取头部对象大小 (8-byte, little-endian, 64-bit)
                header_size = struct.unpack('<Q', data[header_start + 16:header_start + 24])[0]

                # 检查头部大小是否合理
                if header_size < 24 or header_size > file_size - header_start:
                    print(f"  偏移量 {header_start} 头部大小无效: {header_size}，跳过")
                    continue

                # 输出头部基本信息
                print(f"\n潜在WMV文件 #{i + 1} 在偏移量 {header_start}")
                print(f"  头部大小: {header_size:,} 字节")

                # 尝试获取文件大小
                file_size_value = None
                properties_pos = data.find(file_properties_guid, header_start, header_start + header_size)

                if properties_pos != -1:
                    # 文件大小位于属性对象的偏移40字节处
                    if properties_pos + 48 <= file_size:
                        file_size_value = struct.unpack('<Q', data[properties_pos + 40:properties_pos + 48])[0]
                        print(f"  发现文件属性，大小为: {file_size_value:,} 字节")

                # 确定文件结束位置
                if file_size_value:
                    file_end = header_start + file_size_value
                    if file_end > file_size:
                        print(f"  文件大小 {file_size_value:,} 超过文件边界，使用备选结束方案")
                        file_end = None
                else:
                    file_end = None

                # 如果没有有效的文件大小，使用下一个头部作为结束位置
                if file_end is None:
                    next_header_start = file_size  # 默认到文件结束

                    # 查找下一个头部位置
                    for next_hdr in header_positions:
                        if next_hdr > header_start:
                            next_header_start = next_hdr
                            break

                    file_end = next_header_start
                    print(f"  使用备选结束位置: {file_end:,} 字节")

                # 确保结束位置合理
                if file_end <= header_start:
                    print(f"  无效的文件结束位置，跳过")
                    continue

                # 提取文件数据
                wmv_data = data[header_start:file_end]
                data_hash = hashlib.md5(wmv_data).hexdigest()[:8]

                # 创建输出文件名
                output_file = os.path.join(output_dir, f"video_{i + 1}_{data_hash}.wmv")

                # 检查是否是空文件
                if len(wmv_data) == 0:
                    print(f"  警告: 文件 {output_file} 大小为零，跳过")
                    continue

                with open(output_file, 'wb') as out_file:
                    out_file.write(wmv_data)

                file_info = {
                    'path': output_file,
                    'size': len(wmv_data),
                    'start': header_start,
                    'end': file_end
                }
                extracted_files.append(file_info)

                print(f"  提取WMV文件: {len(wmv_data):,} 字节")
                print(f"  保存为: {output_file}")

            except struct.error as e:
                print(f"  解析错误: {e}，跳过此位置")
            except Exception as e:
                print(f"  处理错误: {e}，跳过此位置")

        # 处理重复文件
        file_hashes = defaultdict(list)
        for file_info in extracted_files:
            with open(file_info['path'], 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            file_hashes[file_hash].append(file_info)

        duplicates = []
        for hash_value, files in file_hashes.items():
            if len(files) > 1:
                duplicates.append(files)

        if duplicates:
            print("\n发现重复文件:")
            for i, dup_group in enumerate(duplicates):
                print(f"重复组 #{i + 1} (MD5: {hash_value})")
                for file_info in dup_group:
                    print(f"  {file_info['path']} (大小: {file_info['size']} 字节)")

        print(f"\n扫描完成! 共提取 {len(extracted_files)} 个WMV/ASF文件到目录 '{output_dir}'")

    except Exception as e:
        print(f"处理过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用说明: python extract_wmv.py <二进制文件路径>")
        # print("示例: python extract_wmv.py MOV_03.isv")
    else:
        extract_wmv_files(sys.argv[1])