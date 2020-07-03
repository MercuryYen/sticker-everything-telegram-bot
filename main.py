#coding = unicode
import hashlib
import configparser
from mag import handle_image
import requests
from PIL import Image
import numpy as np
from numba import jit
import math
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import telegram
from flask import Flask, request
import logging
import random
import threading
import json
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)
config = configparser.ConfigParser()
config.read('config.ini')
app = Flask(__name__)
bot = telegram.Bot(token=(config['TELEGRAM']['ACCESS_TOKEN']))

emojis = "😂😘😍😊😁😔😄😭😒😳😜😉😃😢😝😱😡😏😞😅😚😌😀😋😆😐😕👍👌👿❤🖤💤🎵🔞"


def random_emoji():
	return emojis[random.randint(0, len(emojis) - 1)]


def emojiToInt(string):
	for i in range(len(emojis)):
		if string == emojis[i]:
			return i
	return -1


@app.route('/hook', methods=['POST'])
def webhook_handler():
	if request.method == "POST":
		update = telegram.Update.de_json(request.get_json(force=True), bot)
		dispatcher.process_update(update)
		#bot.sendMessage(chat_id=update.message.chat.id, text=str(update))
	return 'ok'


def getHashFromUpdate(update):
	m = hashlib.md5()
	x = str(update.message.from_user.id)

	m.update(x.encode('utf-8'))

	return m.hexdigest()[:7]


def getPackLenFromHash(bot, userHash):
	count = 0

	end = False
	while not end:
		try:
			bot.getStickerSet(name="user" + str(userHash) + "_" +
			                  str(count + 1) + "_by_sticker_everything_bot")
			count += 1
		except:
			end = True

	return count


def start(bot, update):
	bot.sendMessage(
	    chat_id=update.message.chat.id,
	    text="這個Bot可以將圖片轉換成貼圖\n" +
	    "This bot can transform any image to telegram sticker.\n\n" +
	    "command:\n" + 
	    "/new <貼圖包名稱> - 建立命名的新貼圖包\n" +
	    "/set - 設定預設上傳貼圖包\n" +
	    "/list - 顯示所有已建立的貼圖包\n" + 
	    "/now - 顯示目前預設貼圖包\n"+
	    "/help - 救命！\n" + 
	    "/about - 一些有關bot的資訊，以及為什麼你需要這個bot\n\n" +
	    "command:\n" +
	    "/new <name of sticker pack> - Create a new sticker pack with name.\n" +
	    "/set - Set which pack is the default uploading sticker pack.\n"+ 
	    "/list - Show all packs.\n" + 
	    "/now - Display now default sticker pack\n"+
	    "/help - Help! \n" +
	    "/about - Information about this bot and why you need this bot")
	bot.sendMessage(
	    chat_id=update.message.chat.id,
	    text="可以透過 /help 了解完整流程\n\nSending /help to show how to use.")


def new(bot, update):

	userHash = getHashFromUpdate(update)

	if len(update.message.text.split(" ")) == 1:
		bot.sendMessage(
		    chat_id=update.message.chat.id,
		    text=
		    "貼圖包名稱不得為空\nName of sticker pack shouldn't be empty\n\nexample:\n  /new Helltaker"
		)
		return

	count = getPackLenFromHash(bot, userHash)

	bot.createNewStickerSet(
	    user_id=update.message.chat.id,
	    name="user" + str(userHash) + "_" + str(count + 1) +
	    "_by_sticker_everything_bot",
	    title=update.message.text[len(update.message.text.split(" ")[0]) + 1:]
	    + " @sticker_everything_bot",
	    png_sticker=open("example2.png", "rb"),
	    emojis="💤")

	try:
		storage = bot.getStickerSet(name="user" + str(userHash) +
		                            "_default_sticker_pack" +
		                            "_by_sticker_everything_bot")

		bot.addStickerToSet(user_id=update.message.chat.id,
		                    name=storage.name,
		                    png_sticker=open("example2.png", "rb"),
		                    emojis=emojis[count + 1])

		bot.deleteStickerFromSet(storage.stickers[0].file_id)

	except:
		bot.createNewStickerSet(user_id=update.message.chat.id,
		                        name="user" + str(userHash) +
		                        "_default_sticker_pack" +
		                        "_by_sticker_everything_bot",
		                        title="data storage",
		                        png_sticker=open("example2.png", "rb"),
		                        emojis=emojis[0])

	bot.sendMessage(
	    chat_id=update.message.chat.id,
	    text="貼圖包編號 number of sticker pack：" + str(count + 1) +
	    "\nurl:https://t.me/addstickers/user" + str(userHash) + "_" +
	    str(count + 1) +
	    "_by_sticker_everything_bot\n\n目前該貼圖包為預設上傳貼圖包\nNow this pack is default uploading pack.\n貼圖是暫時的，很快就會被取代掉。\nThe sticker in the pack is temporary. After adding sticker it would be removed."
	)

	return


def add(bot, update):

	userHash = getHashFromUpdate(update)
	inputNum = -1

	try:
		storage = bot.getStickerSet(name="user" + str(userHash) +
		                            "_default_sticker_pack" +
		                            "_by_sticker_everything_bot")

		inputNum = emojiToInt(storage.stickers[0].emoji)

	except:
		bot.sendMessage(
		    chat_id=update.message.chat.id,
		    text="目前還沒有貼圖包\nNo pack to add:\n\nexample:\n  /new Helltaker")
		return



	z = requests.get(bot.getFile(
	    update.message.photo[-1].file_id).file_path).content
	open('temp.png', 'wb').write(z)
	img = Image.open('temp.png').convert('RGBA')
	arr = np.array(img)
	mag = 512 / max(len(arr[0]), len(arr))
	new_arr = handle_image(mag, arr)
	# Image.fromarray(new_arr, 'RGBA').save("output.png")
	Image.fromarray(
	    np.array(
	        img.resize(
	            (math.ceil(len(arr[0]) * mag), math.ceil(len(arr) * mag)),
	            Image.LANCZOS)), 'RGBA').save("output.png")

	sticker = bot.uploadStickerFile(user_id=update.message.chat.id,
	                                png_sticker=open("output.png",
	                                                 'rb')).file_id

	bot.addStickerToSet(user_id=update.message.chat.id,
	                    name="user" + str(userHash) + "_" + str(inputNum) +
	                    "_by_sticker_everything_bot",
	                    png_sticker=sticker,
	                    emojis=random_emoji())

	if bot.getStickerSet(
	    name="user" + str(userHash) + "_" + str(inputNum) +
	    "_by_sticker_everything_bot").stickers[0].emoji == "💤":
		bot.deleteStickerFromSet(
		    bot.getStickerSet(
		        name="user" + str(userHash) + "_" + str(inputNum) +
		        "_by_sticker_everything_bot").stickers[0].file_id)

	bot.sendSticker(
	    chat_id=update.message.chat.id,
	    sticker=bot.getStickerSet(
	        name="user" + str(userHash) + "_" + str(inputNum) +
	        "_by_sticker_everything_bot").stickers[-1].file_id,
	    reply_markup=InlineKeyboardMarkup([[
	        InlineKeyboardButton(
	            text=bot.getStickerSet(name="user" + str(userHash) + "_" +
	                                   str(inputNum) +
	                                   "_by_sticker_everything_bot").title,
	            url="https://t.me/addstickers/user" + str(userHash) + "_" +
	            str(inputNum) + "_by_sticker_everything_bot")
	    ]]))
	return


def add2(bot, update):
	userHash = getHashFromUpdate(update)
	inputNum = -1

	try:
		storage = bot.getStickerSet(name="user" + str(userHash) +
		                            "_default_sticker_pack" +
		                            "_by_sticker_everything_bot")

		inputNum = emojiToInt(storage.stickers[0].emoji)

	except:
		bot.sendMessage(
		    chat_id=update.message.chat.id,
		    text="目前還沒有貼圖包\nNo pack to add:\n\nexample:\n  /new Helltaker")
		return

	z = requests.get(bot.getFile(
	    update.message.document.file_id).file_path).content
	open('temp.png', 'wb').write(z)
	img = Image.open('temp.png').convert('RGBA')
	arr = np.array(img)
	mag = 512 / max(len(arr[0]), len(arr))
	new_arr = handle_image(
	    mag, arr)  # Image.fromarray(new_arr, 'RGBA').save("output.png")
	Image.fromarray(
	    np.array(
	        img.resize(
	            (math.ceil(len(arr[0]) * mag), math.ceil(len(arr) * mag)),
	            Image.LANCZOS)), 'RGBA').save("output.png")

	sticker = bot.uploadStickerFile(user_id=update.message.chat.id,
	                                png_sticker=open("output.png",
	                                                 'rb')).file_id

	bot.addStickerToSet(user_id=update.message.chat.id,
	                    name="user" + str(userHash) + "_" + str(inputNum) +
	                    "_by_sticker_everything_bot",
	                    png_sticker=sticker,
	                    emojis=random_emoji())

	if bot.getStickerSet(
	    name="user" + str(userHash) + "_" + str(inputNum) +
	    "_by_sticker_everything_bot").stickers[0].emoji == "💤":
		bot.deleteStickerFromSet(
		    bot.getStickerSet(
		        name="user" + str(userHash) + "_" + str(inputNum) +
		        "_by_sticker_everything_bot").stickers[0].file_id)

	bot.sendSticker(
	    chat_id=update.message.chat.id,
	    sticker=bot.getStickerSet(
	        name="user" + str(userHash) + "_" + str(inputNum) +
	        "_by_sticker_everything_bot").stickers[-1].file_id,
	    reply_markup=InlineKeyboardMarkup([[
	        InlineKeyboardButton(
	            text=bot.getStickerSet(name="user" + str(userHash) + "_" +
	                                   str(inputNum) +
	                                   "_by_sticker_everything_bot").title,
	            url="https://t.me/addstickers/user" + str(userHash) + "_" +
	            str(inputNum) + "_by_sticker_everything_bot")
	    ]]))
	return


def allPack(bot, update):

	allStickersText = ""

	allStickers = []

	count = 0

	userHash = getHashFromUpdate(update)

	end = False
	while not end:
		try:
			x = bot.getStickerSet(name="user" + str(userHash) + "_" +
			                      str(count + 1) +
			                      "_by_sticker_everything_bot")
			allStickersText += str(count + 1) + ". " + x.title + "\n"
			allStickers += [[
			    InlineKeyboardButton(text=x.title,
			                         url="https://t.me/addstickers/user" +
			                         str(userHash) + "_" + str(count + 1) +
			                         "_by_sticker_everything_bot")
			]]
			count += 1
		except:
			end = True

	bot.sendMessage(chat_id=update.message.chat.id,
	                text="貼圖包們：\nSticker packs:\n\n" + allStickersText,
	                reply_markup=InlineKeyboardMarkup(allStickers))


def help_(bot, update):

	bot.sendMessage(
	    chat_id=update.message.chat.id,
	    text=
	    "流程：建立貼圖包 → (設定預設上傳貼圖包) → 加入貼圖包 → 加入貼圖包......\n\nProcess : create pack → (set default uploading pack) → add image to pack → add image to pack......"
	)
	bot.sendMessage(chat_id=update.message.chat.id,
	                text="建立貼圖包的範例：\nexample of creating pack:")
	bot.sendMessage(chat_id=update.message.chat.id, text="/new Helltaker")

	bot.sendMessage(chat_id=update.message.chat.id,
	                text="new時會自動設定預設上傳貼圖包，如果需要更改預設時：\nexample of setting default uploading pack:")
	bot.sendMessage(chat_id=update.message.chat.id, text="/set")

	bot.sendMessage(chat_id=update.message.chat.id,
	                text="將圖片加入貼圖包只需要傳送圖片或檔案就行了\n圖片與檔案的差別在於解析度和透明保留\n\nThe way to add sticker is sending image or sending image as a file.\nThe differences between sending image and sending image as a file are resolution and whether keeping transparency.")
	bot.sendPhoto(chat_id=update.message.chat.id,
	              photo=open("example.png", "rb"))
	bot.sendDocument(chat_id=update.message.chat.id,
	              	document=open("example.png", "rb"))

	bot.sendMessage(chat_id=update.message.chat.id, text="如果有困惑或是不懂的地方都可以找 @Homura343\n\nWhen in doubt, @Homura343.")

def about(bot, update):
	bot.sendMessage(
	    chat_id=update.message.chat.id,
	    text="Author:@Homura343\nChannel:https://t.me/ArumohChannel")

	bot.sendMessage(
	    chat_id=update.message.chat.id,
	    text="這個bot優點在於創建好貼圖包後，可以不用考慮檔案大小、表情符號選擇，一次把所有圖片檔案全部轉換成貼圖。\n\nAdvantage of using this bot to upload sticker is that you don't need to think about resolution and choosing emojis.")
	
	bot.sendMessage(
	    chat_id=update.message.chat.id,
	    text="範例的貼圖\n\nThe example sticker.")
	bot.sendSticker(
	    chat_id=update.message.chat.id,
	    sticker=bot.getStickerSet(
	        name="user8c9ce55_1_by_sticker_everything_bot").stickers[0].file_id,
	    reply_markup=InlineKeyboardMarkup([[
	        InlineKeyboardButton(
	            text="Helltaker",
	            url="https://t.me/addstickers/user8c9ce55_1_by_sticker_everything_bot")
	    ]]))


def now(bot, update):
	userHash = getHashFromUpdate(update)
	try:
		num = emojiToInt(
		    bot.getStickerSet(name="user" + str(userHash) +
		                      "_default_sticker_pack" +
		                      "_by_sticker_everything_bot").stickers[0].emoji)
	except:
		bot.sendMessage(
		    chat_id=update.message.chat.id,
		    text="目前還沒有貼圖包\nNo pack to add:\n\nexample:\n  /new Helltaker")
		return

	x = bot.getStickerSet(name="user" + str(userHash) + "_" + str(num) +
	                      "_by_sticker_everything_bot")

	bot.sendMessage(
	    chat_id=update.message.chat.id,
	    text="目前預設上傳貼圖包為：\nDefault uploading target sticker pack.\n  " + str(num) + ". " + x.title,
	    reply_markup = InlineKeyboardMarkup([[
			    InlineKeyboardButton(text=x.title,
			                         url="https://t.me/addstickers/user" +
			                         str(userHash) + "_" + str(num) +
			                         "_by_sticker_everything_bot")
			]]))

def setup(bot, update):
	userHash = getHashFromUpdate(update)


	count = 0
	end = False
	allStickers = []
	while not end:
		try:
			x = bot.getStickerSet(name="user" + str(userHash) + "_" +
			                      str(count + 1) +
			                      "_by_sticker_everything_bot")
			allStickers += [[
			    InlineKeyboardButton(text=x.title,
			                         callback_data="S "+str(count+1))
			]]
			count += 1
		except:
			end = True

	bot.sendMessage(chat_id=update.message.chat.id,
	                text="選擇預設貼圖包：\nSelect default uploading pack:",
	                reply_markup=InlineKeyboardMarkup(allStickers))

def process_result(self,update,job_queue):
	query = update.callback_query

	m = hashlib.md5()
	x = str(query.from_user.id)

	m.update(x.encode('utf-8'))

	userHash = m.hexdigest()[:7]

	storage = bot.getStickerSet(name="user" + str(userHash) +
		                      "_default_sticker_pack" +
		                      "_by_sticker_everything_bot")
	bot.addStickerToSet(user_id=query.from_user.id,
		                    name=storage.name,
		                    png_sticker=open("example2.png", "rb"),
		                    emojis=emojis[int(query.data.split(" ")[1])])



	x = bot.getStickerSet(name="user" + str(userHash) + "_" +
			                      query.data.split(" ")[1] +
			                      "_by_sticker_everything_bot")

	bot.deleteStickerFromSet(storage.stickers[0].file_id)
	bot.editMessageText(chat_id = query.message.chat.id,
						message_id = query.message.message_id,
						text = "已設定預設上傳貼圖包為：\nNow default uploading sticker pack is :\n  "+x.title)

dispatcher = Dispatcher(bot, None)

dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('new', new))
dispatcher.add_handler(CommandHandler('set',setup))
dispatcher.add_handler(CommandHandler('list', allPack))
dispatcher.add_handler(CommandHandler('now', now))
dispatcher.add_handler(CommandHandler('help', help_))
dispatcher.add_handler(CommandHandler('about', about))
dispatcher.add_handler(MessageHandler(Filters.photo, add))
dispatcher.add_handler(MessageHandler(Filters.document, add2))
dispatcher.add_handler(CallbackQueryHandler(process_result, pass_job_queue=True))
if __name__ == "__main__":
	app.run(debug=True)
