import argparse
import csv
import os

from tqdm import tqdm

csv.field_size_limit(10 * 1024 * 1024)


expected_header = ["repo_url", "license"]


def extract_repo_name(repo_url):
    return repo_url.split("/")[-1]


def _fix_row(row, header):
    fixed_row = []
    for col_name in header:
        if col_name in row:
            fixed_row.append(row[col_name])
        else:
            fixed_row.append("")
    return fixed_row


def fix_csv_file(input_file):
    output_file = os.path.splitext(os.path.basename(input_file))[0]
    output_file = "fixed_" + output_file + ".csv"
    with open(input_file, "r") as input_csv, open(
        output_file, "w", newline=""
    ) as output_csv:
        reader = csv.DictReader(input_csv, delimiter="\t")
        writer = csv.writer(output_csv, delimiter="\t")
        writer.writerow(expected_header)
        for row in reader:
            fixed_row = _fix_row(row, expected_header)
            writer.writerow(fixed_row)
    print(f"Fixed CSV file saved as '{output_file}'")


import io
import sqlite3


def extract_repo_name(repo_url):
    return repo_url.split("/")[-1]


def save_db_to_markdown(db_fname, chunk_size=100, ignored_urls=[]):
    conn = sqlite3.connect(db_fname)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM repo_details")
    mkdwn_fname = "AwesomeList.md"
    with open(mkdwn_fname, "w") as f:
        f.write("# Awesome GitHub Repos\n\n")
        f.write(
            "A curated list of awesome oneAPI GitHub repositories related to various categories.\n\n"
        )
        table_of_contents = "## Table of Contents\n\n"
        topic_dict = {}
        while True:
            rows = cursor.fetchmany(chunk_size)
            if not rows:
                break

            for row in rows:
                (
                    _,
                    repo_url,
                    license_spdx,
                    _,
                    star_count,
                    forks_count,
                    pushed_at,
                    _,
                    _,
                    languages,
                    topics,
                    open_issues,
                    closed_issues,
                    description,
                    fork,
                    size,
                    watchers_count,
                    language,
                    keyword,
                    additional_keywords,
                    is_relevant,
                    brief_desc,
                    class_label,
                    _,
                    _,
                    _,
                ) = row
                if repo_url in ignored_urls:
                    continue
                if is_relevant >= 0.4:
                    print(f"relevant score: {is_relevant}")
                    repo_name = extract_repo_name(repo_url)
                    if class_label not in topic_dict:
                        topic_dict[class_label] = f"### {class_label}\n\n"
                        table_of_contents += f"- [{class_label}](#{class_label.lower().replace(' ', '-')})\n"
                    repo_details = f"""
- **[{repo_name}]({repo_url})** - {brief_desc} ![GitHub stars](https://img.shields.io/badge/stars-{star_count}-blue)
    - OneAPI components: {keyword}, {",".join(additional_keywords.split("|"))}
    - auto_generated = True\n\n"""
                    topic_dict[class_label] += repo_details
        f.write(table_of_contents)
        f.write("\n")
        for topic_content in topic_dict.values():
            f.write(topic_content)
            f.write("\n")
    conn.close()
    return mkdwn_fname


def export():
    ignored_urls = [
        "https://github.com/openvinotoolkit/openvino",
        "https://github.com/openvinotoolkit/model_server",
        "https://github.com/intel-iot-devkit/smart-video-workshop",
        "https://github.com/openvinotoolkit/openvino_tensorflow",
        "https://github.com/OpenVINO-dev-contest/YOLOv7_OpenVINO_cpp-python",
        "https://github.com/openvinotoolkit/docker_ci",
        "https://github.com/openvinotoolkit/openvino_contrib",
        "https://github.com/oneapi-src/oneAPI-spec",
        "https://github.com/Gforcex/OpenGraphic",
        "https://github.com/oneapi-src/oneMKL",
        "https://github.com/openvinotoolkit/open_model_zoo",
        "https://github.com/openvinotoolkit/training_extensions",
        "https://github.com/isl-org/MiDaS",
        "https://github.com/intel/pti-gpu",
        "https://github.com/intel/yask",
        "https://github.com/intel/openvino-rs",
        "https://github.com/intel/clDNN",
        "https://github.com/intel/handwritten-chinese-ocr-samples",
        "https://github.com/intel/ros_openvino_toolkit",
        "https://github.com/intel/intel-extension-for-pytorch",
        "https://github.com/intel/ros2_openvino_toolkit",
        "https://github.com/intel/torch-ccl",
        "https://github.com/intel/intel-extension-for-transformers",
        "https://github.com/intel/intel-extension-for-tensorflow",
        "https://github.com/intel/openvino-ai-plugins-gimp",
        "https://github.com/intel/scikit-learn-intelex",
        "https://github.com/intel/media-delivery",
        "https://github.com/intel/llvm",
        "https://github.com/intel/libxcam",
        "https://github.com/intel/MLSL",
        "https://github.com/intel/robot_devkit",
        "https://github.com/intel/ros_intel_movidius_ncs",
        "https://github.com/intel/intel-device-plugins-for-kubernetes",
        "https://github.com/intel/conversational-ai-chatbot",
        "https://github.com/intel/nn-hal",
        "https://github.com/intel/ros2_grasp_library",
        "https://github.com/intel/ros2_object_analytics",
        "https://github.com/intel/inference-engine-node",
        "https://github.com/intel/gna",
        "https://github.com/intel/neural-compressor",
        "https://github.com/intel/cartwheel-ffmpeg",
        "https://github.com/oneapi-src/SYCLomatic",
        "https://github.com/oneapi-src/oneDPL",
        "https://github.com/oneapi-src/oneCCL",
        "https://github.com/oneapi-src/oneTBB",
        "https://github.com/oneapi-src/oneVPL",
        "https://github.com/oneapi-src/oneDNN",
        "https://github.com/oneapi-src/oneVPL-intel-gpu",
        "https://github.com/intel/llvm",
        "https://github.com/oneapi-src/oneDAL",
        "https://github.com/intel-analytics/BigDL",
        "https://github.com/amd/ZenDNN",
        "https://github.com/pytorch/pytorch",
        "https://github.com/tensorflow/tensorflow",
        "https://github.com/fffaraz/awesome-cpp",
        "https://github.com/dylanhogg/crazy-awesome-python",
        "https://github.com/zishun/awesome-geometry-processing",
        "https://github.com/cgwire/awesome-cg-vfx-pipeline",
        "https://github.com/killop/anything_about_game",
        "https://github.com/jslee02/awesome-graphics-libraries",
        "https://github.com/matiascodesal/awesome-usd",
        "https://github.com/fffaraz/awesome-cpp",
        "https://github.com/josephmisiti/awesome-machine-learning",
        "https://github.com/jgvictores/awesome-deep-reinforcement-learning",
        "https://github.com/taishi-i/awesome-japanese-nlp-resources",
        "https://github.com/sjinzh/awesome-yolo-object-detection",
        "https://github.com/dylanhogg/crazy-awesome-python",
        "https://github.com/EthicalML/awesome-production-machine-learning",
        "https://github.com/krzemienski/awesome-video",
        "https://github.com/sanbuphy/my-awesome-cs",
        "https://github.com/zhengzangw/awesome-huge-models",
        "https://github.com/csarron/awesome-emdl",
        "https://github.com/Kludex/awesome-fastapi-projects",
        "https://github.com/fkromer/awesome-ros2",
        "https://github.com/awesome-stable-diffusion/awesome-stable-diffusion",
        "https://github.com/protontypes/awesome-robotic-tooling",
        "https://github.com/r0f1/datascience",
        "https://github.com/IntelPython/scikit-learn_bench",
    ]
    save_db_to_markdown(db_fname="./db/repos.sqlite", ignored_urls=ignored_urls)


if __name__ == "__main__":
    export()
