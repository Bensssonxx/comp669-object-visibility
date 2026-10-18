# Milestone 材料与阅读顺序

先看 `reports/PILOT_REPORT_ZH.md` 的真实结果与解释，再看 PPT。报告和 PPT 都必须等两个模型完成预测、通过审计后才能生成；文件缺失时不能用示意数字替代。

## 汇报要讲清楚的主线

1. 原问题“遮挡更多会不会下降”过于宽泛。现在研究等量可见图像是否包含等量主体，以及主体面积接近时预测是否仍然变化。
2. Oxford-IIIT Pet 提供像素级主体标注，适合先验证测量方法。它是 37 类品种分类 pilot，不能称为 ImageNet-100 结果。
3. 固定模型、同图、同像素遮挡，分类器只在完整训练图上训练。验证集只选择分类器参数，测试集只用于评估。
4. 第一组比较不同位置、模式和可见面积；第二组在同一图片上固定方形遮挡面积、形状，比较主体面积差异大／接近的样本对。
5. 主体像素面积不等于识别所需语义信息。即便面积匹配，眼睛、脸、毛发、背景等仍然不同，不能把剩余差异叫作 prefix attention 的因果效果。
6. 用实际准确率、成对差值和正确性翻转率讲证据。少量案例只是说明，不代表总体发生率。负结果或宽置信区间都应如实报告。

## 三个容易说错的概念

- “图像保留 50%”：全部图片像素中有一半未涂灰。
- “主体保留 50%”：原图中被标注为主体的像素，有一半未涂灰。它的分母不是全图。
- “成对翻转”：同一原图的两个遮挡版本，一个分类正确、一个分类错误。不是二者都错误但预测类别不同；后者另外用 prediction disagreement 记录。

## 文件

- `COMP669_Object_Visibility_Milestone_v1.pptx` 或后续明确标注的修订版本：可编辑的英文汇报，含英文讲稿与来源说明。
- `SPEAKER_NOTES_EN.md`：按页讲稿，便于练习。需要用自己的话解释并核对实际结果。
- `slide_data.json`：PPT 所用真实统计数值。
- `assets/`：根据已审计结果和实际输入生成的图，不是生成式示意图片。
- `../reports/PILOT_REPORT_EN.md`：可交教授审阅的英文实验说明。

## 本地生成

在项目根目录执行：

```bash
source scripts/env.sh
.venv/bin/python scripts/analyze.py --run pilot_v1
.venv/bin/python scripts/audit_run.py --require-predictions
.venv/bin/python scripts/qualitative_cases.py
.venv/bin/python scripts/write_reports.py
.venv/bin/python scripts/prepare_slide_assets.py
```

PPT 使用 Codex 随附的 `@oai/artifact-tool`。将 `scripts/build_milestone.mjs` 复制到 `.build-presentation/`，该目录的 `node_modules` 链接到随附 Node 包后运行；具体主机路径见该脚本。它与科学实验的 Python 环境分开。每次修订用新的 `MILESTONE_VERSION`，保留前一版供核对。

## 提交前

Part 2 的 slides 截止为 2026-10-21 23:59 ET，10-22 汇报，12 分钟加 1–2 分钟问答。slides 需要初步结果、分析、后续实验、仓库链接与 AI 使用说明。

仓库目前私有，需在正式提交前安排教师访问。还需学生本人审阅和理解材料；本流程不自动提交 Canvas，也不自动发送邮件或邀请教师。
