import base64
import json
from urllib.parse import parse_qs, urlparse
import telebot

# Yahan apna Telegram Bot ka Token daalo
TOKEN = "BOT_TOKEN"
bot = telebot.TeleBot(TOKEN)


def decode_single_url(text):
  try:
    parsed_url = urlparse(text.strip())
    query_params = parse_qs(parsed_url.query)

    encoded_data = None
    param_type = "json"

    # Check karo ki kaun sa parameter hai ('m', 's', ya 'share')
    if "share" in query_params:
      encoded_data = query_params["share"][0]
    elif "m" in query_params:
      encoded_data = query_params["m"][0]
    elif "s" in query_params:
      encoded_data = query_params["s"][0]
      param_type = "string"

    if encoded_data:
      # URL-safe Base64 ko standard base64 mein convert karo
      encoded_data = encoded_data.replace("-", "+").replace("_", "/")

      padding = len(encoded_data) % 4
      if padding > 0:
        encoded_data += "=" * (4 - padding)

      decoded_bytes = base64.b64decode(encoded_data)
      decoded_str = decoded_bytes.decode("utf-8", errors="ignore")

      # Agar 's' parameter hai ya JSON nahi hai, toh check karo ki ||| se jude hain kya
      if param_type == "string":
        if "|||" in decoded_str:
          split_urls = decoded_str.split("|||")
          return [{"url": u.strip(), "key": "N/A"} for u in split_urls if u.strip()]
        return [{"url": decoded_str, "key": "N/A"}]

      # JSON parse karne ki koshish karo
      try:
        parsed_json = json.loads(decoded_str)
        if isinstance(parsed_json, dict):
          # Check karo agar URL ke andar ||| hai toh unhe alag items bana do
          url_val = parsed_json.get("url", "")
          if "|||" in url_val:
            sub_urls = url_val.split("|||")
            results = []
            for sub_u in sub_urls:
              if sub_u.strip():
                item_copy = parsed_json.copy()
                item_copy["url"] = sub_u.strip()
                results.append(item_copy)
            return results
          return [parsed_json]
        return parsed_json
      except:
        if "|||" in decoded_str:
          split_urls = decoded_str.split("|||")
          return [{"url": u.strip(), "key": "N/A"} for u in split_urls if u.strip()]
        return [{"url": decoded_str, "key": "N/A"}]

  except Exception as e:
    print(f"Error decoding: {e}")
    return None
  return None


@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
  bot.reply_to(
      message,
      "⚡ **Fast Decoder Bot Active!**\n\nLinks bhejo, bina kisi `|||` ke"
      " alag-alag karke mil jayengi.",
  )


@bot.message_handler(func=lambda message: True)
def bulk_decode_handler(message):
  text = message.text.strip()
  lines = text.splitlines()

  total_results = []
  for line in lines:
    if "http" in line:
      decoded_data = decode_single_url(line)
      if decoded_data and isinstance(decoded_data, list):
        total_results.extend(decoded_data)

  if not total_results:
    decoded_data = decode_single_url(text)
    if decoded_data and isinstance(decoded_data, list):
      total_results = decoded_data

  if total_results:
    bot.send_message(
        message.chat.id,
        f"🔥 **Successfully Decoded ({len(total_results)} items found):**",
        parse_mode="Markdown",
    )

    for idx, item in enumerate(total_results, start=1):
      url = item.get("url", "N/A")
      key = item.get("key", "N/A")
      name = item.get("name", "N/A")

      item_text = (
          f"🔹 **Item #{idx}**\n"
          f"🏷 **Name:** `{name}`\n"
          f"🔑 **Key:** `{key}`\n\n"
          f"🔗 **URL:** {url}"
      )
      bot.send_message(message.chat.id, item_text, parse_mode="Markdown")
  else:
    bot.reply_to(
        message,
        "❌ Koi valid encoded link nahi mila. Dobara check karo bhai!",
    )


if __name__ == "__main__":
  print("🚀 Fast Decoder Bot is running...")
  bot.infinity_polling()
