import os
import zipfile

def zip_folder(folder_path, output_path):
    # 创建一个压缩文件对象
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 遍历文件夹下的所有文件和子文件夹
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                # 将文件写入压缩文件，保持文件夹结构
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, folder_path))

# 定义文件夹路径和压缩输出文件路径
folder_to_zip = '/data41/private/legent/eval/EmbodiedEvalData/case_studies'
output_zip_file = 'total_cases.zip'

# 调用函数进行压缩
zip_folder(folder_to_zip, output_zip_file)

print(f'文件夹已成功压缩为 {output_zip_file}')
