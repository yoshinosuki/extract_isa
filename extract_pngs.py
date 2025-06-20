import sys
import os


def extract_pngs(isa_file_path):
    png_header = bytes.fromhex("89 50 4E 47 0D 0A 1A 0A")
    png_footer = bytes.fromhex("00 00 00 00 49 45 4E 44 AE 42 60 82")

    output_dir = os.path.splitext(os.path.basename(isa_file_path))[0] + "_pngs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        with open(isa_file_path, 'rb') as file:
            data = file.read()

        start_index = 0
        counter = 1

        while start_index < len(data):
            header_pos = data.find(png_header, start_index)
            if header_pos == -1:
                break

            footer_pos = data.find(png_footer, header_pos)
            if footer_pos == -1:
                print(f"警告：在偏移量 {header_pos} 找到PNG头，但未找到尾部标识")
                break

            end_pos = footer_pos + len(png_footer)
            png_data = data[header_pos:end_pos]
            output_path = os.path.join(output_dir, f"image_{counter}.png")

            with open(output_path, 'wb') as png_file:
                png_file.write(png_data)

            print(f"提取: PNG #{counter} [偏移量 {header_pos}-{end_pos}] 保存为 {output_path}")
            counter += 1
            start_index = end_pos

        if counter == 1:
            print("未找到有效的PNG图片")
        else:
            print(f"共提取 {counter - 1} 张PNG图片到目录 '{output_dir}'")

    except Exception as e:
        print(f"处理错误: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python extract_pngs.py <isa文件路径>")
        # python extract_pngs.py system.isa
    else:
        extract_pngs(sys.argv[1])
