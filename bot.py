import os
import discord
import cv2
from io import BytesIO
import numpy as np 
import re
import pytesseract
import math
import easyocr  # EasyOCRを使用

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)

reader = easyocr.Reader(['en'], gpu=False)

#########################################
# 前処理：背景色が2色（#8D8DA1, #525271）に対応するOCR用画像生成
#########################################
def preprocess_image_for_ocr(image):
    # HSV色空間に変換
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # 背景色(#8D8DA1)のHSV範囲（例）
    lower_bg1 = np.array([100, 20, 90])
    upper_bg1 = np.array([140, 50, 140])
    # 背景色(#525271)のHSV範囲（例）
    lower_bg2 = np.array([130, 20, 70])
    upper_bg2 = np.array([180, 50, 120])
    # 背景マスク作成
    mask_bg1 = cv2.inRange(hsv_image, lower_bg1, upper_bg1)
    mask_bg2 = cv2.inRange(hsv_image, lower_bg2, upper_bg2)
    combined_mask = cv2.bitwise_or(mask_bg1, mask_bg2)
    # 背景部分を白に変換
    result = cv2.bitwise_and(image, image, mask=cv2.bitwise_not(combined_mask))
    result[combined_mask != 0] = [255, 255, 255]
    # グレースケール化
    gray_result = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    # しきい値処理（背景が白、文字が黒になるように）
    _, thresh = cv2.threshold(gray_result, 180, 255, cv2.THRESH_BINARY_INV)
    # ガウシアンブラーでノイズ除去
    blurred = cv2.GaussianBlur(thresh, (5, 5), 0)
    return blurred

#########################################
# OCRで「PERFECT」「MISS」の位置抽出
#########################################
def extract_perfect_miss_positions(image):
    preprocessed_img = preprocess_image_for_ocr(image)
    details = pytesseract.image_to_data(preprocessed_img, output_type=pytesseract.Output.DICT)
    perfect_positions = []
    miss_positions = []
    for i, word in enumerate(details['text']):
        if 'PERFECT' in word.upper():
            (x, y, w, h) = (details['left'][i], details['top'][i], details['width'][i], details['height'][i])
            perfect_positions.append((x, y, w, h))
        if 'MISS' in word.upper():
            (x, y, w, h) = (details['left'][i], details['top'][i], details['width'][i], details['height'][i])
            miss_positions.append((x, y, w, h))
    return perfect_positions, miss_positions

#########################################
# ラベル描画：縦は1.2倍、横は1.3倍
#########################################
def draw_labels(image, perfect_positions, miss_positions):
    labeled_image = image.copy()
    for perfect_pos, miss_pos in zip(perfect_positions, miss_positions):
        _, y_perfect, _, h_perfect = perfect_pos
        _, y_miss, _, h_miss = miss_pos
        base_length = (y_miss + h_miss) - y_perfect
        square_width = int(base_length * 1.3)
        square_height = int(base_length * 1.2)
        x_perfect, y_perfect, _, _ = perfect_pos
        x_label = max(0, x_perfect - int(base_length * 0.1))
        y_label = max(0, y_perfect - int(base_length * 0.1))
        cv2.rectangle(labeled_image, (x_label, y_label), (x_label + square_width, y_label + square_height), (0, 255, 0), 2)
    return labeled_image

#########################################
# 黒塗り用
#########################################
def blackout_positions(image, positions):
    for (x, y, w, h) in positions:
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 0), -1)
    return image

#########################################
# EasyOCRでスコアを読み取る
#########################################
def extract_score_with_easyocr(image):
    results = reader.readtext(image, detail=0)  # テキストのみ取得
    numbers = [re.sub(r'\D', '', text) for text in results]  # 数字のみ抽出
    numbers = [num for num in numbers if num]  # 空文字削除
    return numbers

#########################################
# Discordイベント
#########################################
@client.event
async def on_message(message):
    if client.user.mentioned_in(message) and message.attachments:
        # debugフラグ判定
        is_debug = "debug" in message.content.lower()
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg"]):
                file_path = f"temp_{attachment.filename}"
                await attachment.save(file_path)
                img = cv2.imread(file_path)
                processed_img = img.copy()

                all_perfect_positions, all_miss_positions = [], []

                # 最大5回繰り返して各ラベル領域を抽出
                for _ in range(5):
                    perfect_positions, miss_positions = extract_perfect_miss_positions(processed_img)
                    if not perfect_positions or not miss_positions:
                        break
                    all_perfect_positions.extend(perfect_positions)
                    all_miss_positions.extend(miss_positions)
                    processed_img = blackout_positions(processed_img, perfect_positions)
                    processed_img = blackout_positions(processed_img, miss_positions)

                # ラベル付き画像の作成
                labeled_image = draw_labels(img, all_perfect_positions, all_miss_positions)
                _, encoded_img = cv2.imencode('.png', labeled_image)
                img_bytes = encoded_img.tobytes()
                image_file = discord.File(BytesIO(img_bytes), filename="labeled_result.png")
                # debug時のみ送信
                if is_debug:
                    await message.channel.send("（デバッグ用）読み取り部分にラベルをつけた画像です:", file=image_file)

                label_regions = []
                for perfect_pos, miss_pos in zip(all_perfect_positions, all_miss_positions):
                    x_perfect, y_perfect, _, _ = perfect_pos
                    _, y_miss, _, h_miss = miss_pos
                    base_length = (y_miss + h_miss) - y_perfect
                    square_width = int(base_length * 1.3)
                    square_height = int(base_length * 1.2)
                    x_label = max(0, x_perfect - int(base_length * 0.1))
                    y_label = max(0, y_perfect - int(base_length * 0.1))
                    label_regions.append((x_label, y_label, square_width, square_height))

                label_regions.sort(key=lambda r: r[0])
                summary_lines = []
                player_number = 1
                all_player_scores = []

                for region in label_regions:
                    x_label, y_label, square_width, square_height = region
                    crop = img[y_label:y_label+square_height, x_label:x_label+square_width]
                    if crop.size == 0:
                        player_number += 1
                        continue

                    # OCR処理
                    half = crop.shape[1] // 2
                    right_half = crop[:, half:crop.shape[1]]
                    preprocessed_right = preprocess_image_for_ocr(right_half)
                    ocr_text_list = extract_score_with_easyocr(preprocessed_right)

                    # 失敗時は左右10pxカットして再試行
                    if len(ocr_text_list) < 5:
                        cut_left = 10
                        cut_right = 10
                        if preprocessed_right.shape[1] > (cut_left + cut_right + 10):
                            cut_img = preprocessed_right[:, cut_left:preprocessed_right.shape[1]-cut_right]
                            ocr_text_list = extract_score_with_easyocr(cut_img)

                    if len(ocr_text_list) < 5:
                        _, enc_img = cv2.imencode('.png', preprocessed_right)
                        right_img_bytes = enc_img.tobytes()
                        file_debug = discord.File(BytesIO(right_img_bytes), filename=f"player{player_number}_preprocessed.png")

                        await message.channel.send(f"Player_{player_number} のスコアラベルが認識できませんでした。", file=file_debug)
                        summary_lines.append(f"Player_{player_number}: 状態=スコア認識に失敗 \n-# 手動で入力してください。")
                        player_number += 1
                        continue

                    try:
                        perfect_val = int(ocr_text_list[0])
                        great_val   = int(ocr_text_list[1])
                        good_val    = int(ocr_text_list[2])
                        bad_val     = int(ocr_text_list[3])
                        miss_val    = int(ocr_text_list[4])
                    except Exception as e:
                        _, enc_img = cv2.imencode('.png', preprocessed_right)
                        right_img_bytes = enc_img.tobytes()
                        file_debug = discord.File(BytesIO(right_img_bytes), filename=f"player{player_number}_preprocessed.png")
                        await message.channel.send(f"Player_{player_number} の数値変換に失敗しました: {e}", file=file_debug)
                        summary_lines.append(f"Player_{player_number}: 状態=数値変換に失敗 \n-# 手動で入力してください。")
                        player_number += 1
                        continue

                    total_notes = perfect_val + great_val + good_val + bad_val + miss_val
                    if total_notes == 0:
                        player_number += 1
                        continue

                    score_raw = (
                        perfect_val * 3 +
                        great_val * 2 +
                        good_val * 1 +
                        bad_val * 0 +
                        miss_val * 0
                    )

                    score = math.floor(score_raw)  # 小数点以下を切り捨て

                    # プレイヤーのスコアを保存
                    all_player_scores.append({
                        "player": player_number,
                        "perfect": perfect_val,
                        "great": great_val,
                        "good": good_val,
                        "bad": bad_val,
                        "miss": miss_val,
                        "score": score
                    })

                    summary_lines.append(f"Player_{player_number}: 状態=正常 \n-# PERFECT={perfect_val}, GREAT={great_val}, GOOD={good_val}, BAD={bad_val}, MISS={miss_val}, スコア={score}")
                    player_number += 1

                # すべてのプレイヤーの結果をDiscordに送信
                if all_player_scores:
                    for player_score in all_player_scores:
                        result_message = (
                            f"### Player_{player_score['player']} 認識結果\n"
                            "```\n"
                            f"PERFECT(3)  : {player_score['perfect']}\n"
                            f"GREAT(2)    : {player_score['great']}\n"
                            f"GOOD(1)     : {player_score['good']}\n"
                            f"BAD(0)      : {player_score['bad']}\n"
                            f"MISS(0)     : {player_score['miss']}\n"
                            "```\n\n"
                            f"## ランクマスコア  {player_score['score']} \n"
                        )
                        await message.channel.send(result_message)

                    # debug時のみサマリー送信
                    if is_debug:
                        summary_text = "\n".join(summary_lines)
                        await message.channel.send(f"{message.author.mention} の認識結果:\n{summary_text}")
                else:
                    await message.channel.send(f"{message.author.mention} 有効なラベルが1件も認識できませんでした。")

                os.remove(file_path)


client.run(TOKEN)
