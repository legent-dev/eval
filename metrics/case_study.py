import os
import sys
import json
from PIL import Image, ImageDraw, ImageFont
import re


def load_json(json_path):
    """加载 JSON 文件."""
    try:
        with open(json_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading JSON file: {e}")
        return None

def draw_checkmark(draw, x, y, size, color="green", width=10):
    """Draws a checkmark on the given ImageDraw object."""
    # 使用贝塞尔曲线绘制平滑的对勾，并加长左边线条
    draw.line(
        [
            (x - 0.1 * size, y + 0.5 * size),  # 将起始点向左偏移
            (x + 0.35 * size, y + 0.8 * size),
            (x + 1.0 * size, y + 0.0 * size),
        ],
        fill=color,
        width=width,
        joint="curve",
    )

def draw_cross(draw, x, y, size, color="red", width=10):
    """Draws a cross on the given ImageDraw object."""
    draw.line([(x, y), (x + size, y + size)], fill=color, width=width)
    draw.line([(x + size, y), (x, y + size)], fill=color, width=width)


def concatenate_images_with_actions(
    image_paths,
    actions,
    border_width=5,
    font_path="Courier_New_Bold.ttf",
    font_size=50,
    text_color=(255, 255, 255),
    background_color=(255, 255, 255),
    row_spacing=20,
    highlight_opacity=128,
    highlight_padding=5,
    highlight_vertical_offset=10,
    highlight_all_actions=False,
    title="My Awesome Plot",
):
    """
    拼接图片列表和对应的动作说明，并添加标题和图片序号。

    Args:
        image_paths (list): 图片路径列表。
        actions (list): 动作说明列表，与 image_paths 一一对应。
        border_width (int): 图片边框宽度。
        font_path (str): 字体文件路径。
        font_size (int): 字体大小。
        text_color (tuple): 文字颜色。
        background_color (tuple): 背景颜色。
        row_spacing (int): 行间距。
        highlight_opacity (int): 高亮透明度 (0-255)。
        highlight_padding (int): 高亮背景的 padding。
        highlight_vertical_offset (int): 高亮背景的垂直偏移量。
        highlight_all_actions (bool): 是否高亮所有动作。
        title (str): 图片的标题。

    Returns:
        PIL.Image: 拼接后的图片对象。
    """
    images = [Image.open(path) for path in image_paths]
    num_images = len(images)

    # 根据图片数量确定排布方式
    if num_images > 10:
        images_per_row = (num_images + 1) // 2  # 每排图片数量，向上取整
        num_rows = 2  # 两排
    else:
        images_per_row = num_images
        num_rows = 1

    max_image_width = max(img.width for img in images)
    max_image_height = max(img.height for img in images)
    font = ImageFont.truetype(font_path, font_size)

    title_font = ImageFont.truetype(font_path, font_size)
    title_lines = _wrap_text(title, title_font, max_image_width * images_per_row)

    title_height = len(title_lines) * (font_size + 10)

    canvas_width = images_per_row * (max_image_width + 2 * border_width)
    canvas_height = (
        num_rows * (max_image_height + 2 * border_width + row_spacing)
        + title_height
        + 20
    )

    canvas = Image.new("RGB", (canvas_width, canvas_height), background_color)
    draw = ImageDraw.Draw(canvas)

    # 绘制标题
    y_offset = 10
    for line in title_lines:
        text_bbox = title_font.getbbox(line)
        title_width = text_bbox[2] - text_bbox[0]
        title_x = 10  # 左边距
        draw.text((title_x, y_offset), line, font=title_font, fill=(0, 0, 0))
        y_offset += font_size + 10

    # 绘制图片和动作说明
    for i in range(num_images):
        row = i // images_per_row
        col = i % images_per_row
        x = col * (max_image_width + 2 * border_width) + border_width
        y = (
            row * (max_image_height + 2 * border_width + row_spacing)
            + border_width
            + title_height
            + 20
        )

        # 粘贴图片和边框
        canvas.paste(images[i], (x, y))
        draw.rectangle(
            [
                x - border_width,
                y - border_width,
                x + max_image_width + border_width,
                y + max_image_height + border_width,
            ],
            outline="black",
            width=border_width,
        )

        # 绘制动作说明
        _draw_text_with_wrapping(
            draw,
            actions[i]["action"],
            font,
            text_color,
            x,
            y + max_image_height - font_size * 2,
            max_image_width,
            highlight_all_actions,
            highlight_opacity,
            highlight_padding,
            highlight_vertical_offset,
        )

        # 绘制图片序号
        circle_x = x + 45  # 调整圆圈的 x 坐标
        circle_y = y + 45  # 调整圆圈的 y 坐标
        text_bbox = font.getbbox(str(i + 1))
        circle_radius = 25 + 10
        if "feedback" in actions[i]:
            circle_color = "green" if actions[i]["feedback"] != "failed" else "red"
        else:
            circle_color = "green"
        draw.ellipse(
            (
                circle_x - circle_radius,
                circle_y - circle_radius,
                circle_x + circle_radius,
                circle_y + circle_radius,
            ),
            fill=circle_color,
            outline="black",
            width=0,
        )
        text_x = circle_x - text_bbox[2] // 2
        text_y = circle_y - text_bbox[3] // 2 - 5
        draw.text(
            (text_x, text_y),
            str(i + 1),
            font=ImageFont.truetype(font_path, 50),
            fill="white",
        )

        # 在最后一张图片的右上角绘制对勾或叉叉
        if i == num_images - 1:
            done_after_action = (actions[i]["done_after_action"] == 1)
            # 定义对勾或叉叉的大小
            symbol_size = max_image_width * 0.2
            # 定义绘制位置，距离图片右上角有一定偏移
            offset = border_width + 10
            symbol_x = x + max_image_width - symbol_size - offset
            symbol_y = y + offset
            if done_after_action:
                draw_checkmark(
                    draw, symbol_x, symbol_y, symbol_size, color="green", width=20
                )
            else:
                draw_cross(
                    draw, symbol_x, symbol_y, symbol_size, color="red", width=20
                )

    return canvas.convert("RGB")


def _wrap_text(text, font, max_width):
    """辅助函数：根据最大宽度将文本自动换行。"""
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        if font.getbbox(current_line + " " + word)[2] > max_width:
            lines.append(current_line)
            current_line = word
        else:
            current_line += " " + word if current_line else word
    lines.append(current_line)
    return lines


def _draw_text_with_wrapping(
    draw,
    text,
    font,
    text_color,
    x,
    y,
    max_width,
    highlight,
    highlight_opacity,
    highlight_padding,
    highlight_vertical_offset,
):
    """辅助函数：绘制换行文本并添加高亮。"""
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        if font.getbbox(current_line + " " + word)[2] > max_width:
            lines.append(current_line)
            current_line = word
        else:
            current_line += " " + word if current_line else word
    lines.append(current_line)

    for j, line in enumerate(lines):
        text_bbox = font.getbbox(line)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = x + (max_width - text_width) // 2

        # 高亮处理
        if highlight:
            highlight_mask = Image.new("RGBA", draw.im.size, (0, 0, 0, 0))
            highlight_draw = ImageDraw.Draw(highlight_mask)
            highlight_bbox = (
                text_x - highlight_padding,
                y + j * font.size + highlight_vertical_offset - highlight_padding,
                text_x + text_width + highlight_padding,
                y + j * font.size + highlight_vertical_offset + font.size + highlight_padding,
            )
            highlight_draw.rectangle(
                highlight_bbox, fill=(255, 255, 255, highlight_opacity)
            )
            draw.im = Image.alpha_composite(draw.im.convert("RGBA"), highlight_mask)

        # 绘制文本
        draw.text((text_x, y + j * font.size), line, font=font, fill=text_color)


def list_all_subsubfolders(folder_path):
    """
    Lists all sub-subfolders (folders two levels deep) within a given folder.

    Args:
        folder_path: The path to the main folder.

    Returns:
        A list of paths to all sub-subfolders.
    """
    subsubfolders = []
    for root, dirs, _ in os.walk(folder_path):
        # Calculate the depth of the current folder relative to the main folder
        depth = root.replace(folder_path, "").count(os.sep)

        # Only append folders at depth 1 (sub-subfolders)
        if depth == 1:
            for d in dirs:
                subsubfolders.append(os.path.join(root, d))
    return subsubfolders


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python concatenate.py <model_name>")
        sys.exit(1)

    model_name = sys.argv[1]
    result_folder = f"/data41/private/legent/eval/EmbodiedEvalData/final_results/{model_name}"
    subsubfolders = list_all_subsubfolders(result_folder)

    # Create the "case_studies" folder if it doesn't exist
    case_studies_big_folder = "/data41/private/legent/eval/EmbodiedEvalData/case_studies"
    import shutil
    # delete the folder if it exists
    shutil.rmtree(case_studies_big_folder, ignore_errors=True)
    os.makedirs(case_studies_big_folder)
    case_studies_folder = f"{case_studies_big_folder}/{model_name}"
    os.makedirs(case_studies_folder, exist_ok=True)

    for folder in subsubfolders:
        try:
            image_paths = sorted(
                os.path.abspath(f.path)
                for f in os.scandir(folder)
                if re.match(r"^\d{4}.*\.png$", f.name) and f.is_file()
            )[:-1]
            traj_json = f"{folder}/traj.json"
            action_texts = load_json(traj_json)
            task_title = load_json(f"{folder}/task.json")["task"]

            if len(image_paths) <= 0:
                raise ValueError(f"No images to concatenate!!! {folder}")

            # 拼接图片和动作说明，并设置标题
            concatenated_image = concatenate_images_with_actions(
                image_paths, action_texts, highlight_all_actions=False, title=task_title
            )

            # Create the subfolder structure within "case_studies"
            relative_path = os.path.relpath(folder, result_folder)
            save_path = f"{case_studies_folder}/{relative_path}.png"
            save_folder = os.path.dirname(save_path)
            os.makedirs(save_folder, exist_ok=True)

            concatenated_image.save(save_path)
            print("Finished: ", folder)
        except (FileNotFoundError, json.JSONDecodeError, IndexError) as e:
            print(f"Error processing folder {folder}: {e}")

    traj_folder = (
        "/data41/private/legent/eval/EmbodiedEvalData/final_results/human/SocialInteraction/"
        "traj0310_task-20240927023237-vr_store-I_m_hungry,_could_you_please_"
        "buy_me_a_loaf_of_bread__The_bread_section_is_right_across_from_the_checkout_counter_"
    )
