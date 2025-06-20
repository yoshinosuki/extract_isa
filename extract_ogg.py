import sys
import os
import struct


def extract_ogg_files(isa_file_path):
    """
    从ISA文件中提取OGG音频文件
    """
    # 创建输出目录
    output_dir = os.path.splitext(os.path.basename(isa_file_path))[0] + "_ogg"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        # 读取整个ISA文件
        with open(isa_file_path, 'rb') as f:
            data = f.read()

        current_pos = 0
        ogg_file_counter = 0
        ogg_stream = bytearray()
        in_stream = False

        print(f"分析ISA文件: {os.path.basename(isa_file_path)}")
        print(f"文件总长度: {len(data):,} 字节")
        print("开始扫描OGG文件...")

        while current_pos < len(data) - 27:  # OggS最小头部长度
            # 检查是否找到OGG头部标识 ('OggS')
            if data[current_pos:current_pos + 4] == b'OggS':
                # 确保有足够的字节读取头部
                if current_pos + 27 > len(data):
                    if in_stream:
                        print(f"警告: 在序列号 {serial} 发现不完整OGG流，大小: {len(ogg_stream)} 字节")
                        in_stream = False
                        ogg_stream = bytearray()
                    current_pos += 4
                    continue

                # 解析页面头部
                try:
                    # 头部格式: [B:版本, B:标志, Q:granule, I:序列号, I:页码, i:CRC, B:段数]
                    version, flags, granule, serial, pagenum, crc, segs = struct.unpack('<BBQIIiB', data[
                                                                                                    current_pos + 4:current_pos + 27])

                    # 验证版本号 (应为0)
                    if version != 0:
                        current_pos += 4
                        continue

                    # 确保有足够的数据读取段表和页面内容
                    page_start = current_pos
                    page_end = current_pos + 27 + segs

                    # 计算内容长度
                    if current_pos + 27 + segs > len(data):
                        if in_stream:
                            print(f"警告: 在序列号 {serial} 发现不完整OGG流，大小: {len(ogg_stream)} 字节")
                            in_stream = False
                            ogg_stream = bytearray()
                        current_pos += 4
                        continue

                    # 读取段表
                    segment_table = data[current_pos + 27:current_pos + 27 + segs]
                    content_length = sum(segment_table)

                    # 计算整个页面结束位置
                    page_end = current_pos + 27 + segs + content_length

                    # 验证页面结束位置
                    if page_end > len(data):
                        if in_stream:
                            print(f"警告: 在序列号 {serial} 发现不完整OGG流，大小: {len(ogg_stream)} 字节")
                            in_stream = False
                            ogg_stream = bytearray()
                        current_pos += 4
                        continue

                    # 进入流收集模式
                    if not in_stream:
                        in_stream = True
                        ogg_stream = bytearray()
                        current_serial = serial  # 记录当前流的序列号

                    # 添加到OGG流（仅当序列号匹配时）
                    if serial == current_serial:
                        ogg_stream.extend(data[page_start:page_end])

                        # 检查是否为流的结束页面 (EOS标志)
                        if flags & 0x04:  # End of stream flag
                            if in_stream and len(ogg_stream) > 0:
                                # 保存OGG文件
                                ogg_file_counter += 1
                                filename = os.path.join(output_dir, f"audio_{ogg_file_counter}.ogg")

                                with open(filename, 'wb') as ogg_file:
                                    ogg_file.write(ogg_stream)

                                print(
                                    f"发现OGG流 #{ogg_file_counter} [序列号: {serial}], 页面数: {pagenum + 1}, 大小: {len(ogg_stream):,} 字节")
                                print(f"保存为: {filename}")

                            in_stream = False
                            ogg_stream = bytearray()

                    # 移动到下一页
                    current_pos = page_end
                except struct.error:
                    # 头部不完整，跳过这个位置
                    if in_stream:
                        print(f"警告: 在序列号 {current_serial} 发现不完整OGG流，大小: {len(ogg_stream)} 字节")
                        in_stream = False
                        ogg_stream = bytearray()
                    current_pos += 1
            else:
                # 如果没有在流中，继续寻找'OggS'
                if not in_stream:
                    current_pos += 1
                # 如果在流中但当前不匹配，结束当前流
                else:
                    if len(ogg_stream) > 0:
                        print(f"警告: 在序列号 {current_serial} 发现不完整OGG流，大小: {len(ogg_stream)} 字节")
                    in_stream = False
                    ogg_stream = bytearray()
                    current_pos += 1

        print(f"扫描完成! 共发现 {ogg_file_counter} 个OGG音频文件")

    except Exception as e:
        print(f"处理过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用说明: python extract_ogg.py <isa文件路径>")
        # print("示例: python extract_ogg.py wave_common.isa")
    else:
        extract_ogg_files(sys.argv[1])